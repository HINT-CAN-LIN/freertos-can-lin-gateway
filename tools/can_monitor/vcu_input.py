"""VCU UART control with bounded motion and a GUI/feedback lease."""
import queue
import threading
import time
import serial
from bench_vcu_motor import command

SAFE = (0, 0, 1, 0)  # ignition OFF, accelerator 0, brake, P


class VcuInput:
    def __init__(self, port):
        self.port = port
        self.events = queue.SimpleQueue()
        self.lock = threading.Lock()
        self.quit = threading.Event()
        self.wake = threading.Event()
        self.ready = False
        self.request = SAFE
        self.deadline = 0.0
        self.lease = 0.0
        self.thread = threading.Thread(target=self.run, daemon=True)

    def feedback(self, healthy):
        with self.lock:
            self.lease = time.monotonic()+0.30 if healthy else 0

    def apply(self, gear, pedal, duration):
        if gear not in ('P','N','D','R') or not 0 <= pedal <= 20 or not 1 <= duration <= 10:
            raise ValueError('Gear P/N/D/R, pedal 0–20%, duration 1–10 s required')
        with self.lock:
            if not self.ready or time.monotonic() >= self.lease:
                raise ValueError('VCU ACK와 신선한 실제 CAN 수신이 필요합니다.')
            self.request = (2, int(pedal) if gear in ('D','R') else 0, 0, ('P','N','D','R').index(gear))
            self.deadline = time.monotonic()+duration
        self.wake.set()

    def safe(self):
        with self.lock:
            self.request = SAFE
            self.deadline = 0
        self.wake.set()

    def stop(self):
        self.safe()
        self.quit.set()
        self.wake.set()

    def current(self, now):
        with self.lock:
            if self.request != SAFE and (now >= self.deadline or now >= self.lease):
                reason = '시간 종료 → P/브레이크' if now >= self.deadline else 'CAN/화면 갱신 끊김 → P/브레이크'
                self.request = SAFE
                self.events.put(reason)
            return self.request

    def run(self):
        sequence = 0
        try:
            with serial.Serial(self.port,115200,timeout=.15,write_timeout=.15) as port:
                port.reset_input_buffer()
                try:
                    while not self.quit.is_set():
                        sequence = (sequence+1)&65535
                        command(port, sequence, *self.current(time.monotonic()))
                        if not self.ready:
                            self.ready = True
                            self.events.put('VCU ACK 정상 · P/브레이크 대기')
                        self.wake.wait(.05)
                        self.wake.clear()
                finally:
                    self.ready = False
                    # Best effort stop. Firmware also expires UART input at 500 ms.
                    for _ in range(3):
                        sequence = (sequence+1)&65535
                        try:
                            command(port, sequence, *SAFE)
                        except Exception as exc:
                            self.events.put('정지 ACK 미확인: '+str(exc))
        except Exception as exc:
            self.events.put('입력 연결 오류: '+str(exc))
        finally:
            self.ready = False


def create_panel(app):
    import tkinter as tk
    from tkinter import ttk

    window = tk.Toplevel(app)
    window.title('VCU 입력 → CAN → Motor')
    window.geometry('690x370')
    window.resizable(False, False)
    window.configure(bg='#151f30')
    port = tk.StringVar(value='COM6')
    gear = tk.StringVar(value='D')
    pedal = tk.IntVar(value=10)
    duration = tk.StringVar(value='2')
    status = tk.StringVar(value='VCU 연결은 P/브레이크로 시작합니다. 실행 버튼을 눌러야 움직입니다.')
    def label(text):
        tk.Label(window,text=text,bg='#151f30',fg='#edf3fb',font=('Malgun Gothic',11)).pack(anchor='w',padx=20,pady=(12,3))
    label('VCU USB 입력  /  CANable 수신은 메인 화면에서 연결')
    row=ttk.Frame(window); row.pack(fill='x',padx=20,pady=8)
    ttk.Entry(row,textvariable=port,width=12).pack(side='left',padx=6)
    def connect():
        if app.driver and app.driver.thread.is_alive():
            status.set('이미 연결되어 있습니다. 분리 후 포트를 변경하세요.'); return
        app.driver = VcuInput(port.get().strip())
        app.driver.thread.start()
        status.set('VCU 연결 중…')
    ttk.Button(row,text='VCU 연결',command=connect).pack(side='left',padx=6)
    ttk.Button(row,text='분리',command=lambda: app.driver.stop() if app.driver else None).pack(side='left',padx=6)
    row=ttk.Frame(window); row.pack(fill='x',padx=20,pady=8)
    ttk.Label(row,text='기어').pack(side='left',padx=6)
    ttk.Combobox(row,textvariable=gear,values=('P','N','D','R'),state='readonly',width=5).pack(side='left')
    ttk.Label(row,text='가속 % (최대 20)').pack(side='left',padx=10)
    ttk.Spinbox(row,from_=0,to=20,textvariable=pedal,width=5).pack(side='left')
    ttk.Label(row,text='유지 시간(초)').pack(side='left',padx=10)
    ttk.Spinbox(row,from_=1,to=10,textvariable=duration,width=5).pack(side='left')
    def apply():
        try:
            if not app.driver: raise ValueError('먼저 VCU 연결을 누르세요.')
            app.driver.apply(gear.get(),pedal.get(),float(duration.get()))
            status.set(f'실행 요청: {gear.get()} / {pedal.get()}% / {duration.get()}초 · 종료 후 정지')
        except (ValueError, tk.TclError) as exc: status.set(str(exc))
    row=ttk.Frame(window); row.pack(fill='x',padx=20,pady=12)
    ttk.Button(row,text='RUN · 입력 적용',command=apply).pack(side='left',padx=6)
    def brake():
        if app.driver: app.driver.safe()
        status.set('P / 토크 0 / 브레이크 요청')
    tk.Button(row,text='■ 정지 / 브레이크',command=brake,bg='#b52c3d',fg='white',font=('Malgun Gothic',13,'bold'),padx=20,pady=8).pack(side='right',padx=6)
    tk.Label(window,textvariable=status,bg='#151f30',fg='#43dfbd',wraplength=640,justify='left',font=('Malgun Gothic',10)).pack(fill='x',padx=20,pady=10)
    label('PC → USB(COM6) → VCU → CAN → Motor\n데모에서는 구동 불가 · 입력창 닫기/수신 중지 시 정지 요청')
    def close_panel():
        if app.driver: app.driver.stop()
        window.destroy()
        app.input_window = None
    window.protocol('WM_DELETE_WINDOW',close_panel)
    app.driver_status = status
    return window
