"""Native Windows dashboard for the VCU / Motor / Cluster CAN bench."""
import argparse
from collections import deque
from pathlib import Path
import queue
import time
import tkinter as tk
from tkinter import ttk
from protocol import Monitor, NAMES
from transport import Receiver

ROOT = Path(__file__).resolve().parent
BG, PANEL, TEXT, MUTED, ACCENT = '#0c1220', '#151f30', '#edf3fb', '#91a2b9', '#43dfbd'


class Dashboard(tk.Tk):
    def __init__(self, demo=False):
        super().__init__()
        self.title('VCU · Motor PC Tool')
        self.geometry('1180x810')
        self.minsize(1020, 740)
        self.configure(bg=BG)
        self.monitor = Monitor()
        self.receiver = None
        self.driver = None
        self.input_window = None
        self.driver_status = None
        self.vcu_port = tk.StringVar(value='COM6')
        self.drive_gear = tk.StringVar(value='D')
        self.drive_pedal = tk.StringVar(value='10')
        self.drive_duration = tk.StringVar(value='2')
        self.drive_ready = tk.StringVar(value='전체 연결을 누르면 VCU와 CAN 수신을 함께 연결합니다.')
        self.driver_status = tk.StringVar(value='입력 대기 · 실행 버튼을 눌러야 움직입니다.')
        self.closing = False
        self.history = deque(maxlen=240)
        self.cards = {}
        self.source = tk.StringVar(value='DISCONNECTED — CANable 연결 후 전체 연결')
        self.details = tk.StringVar(value='CANable → 500 kbps · Standard 11-bit · DLC 8 · PC TX 0x200 / VCU ACK 0x201')
        self.backend = tk.StringVar(value='slcan')
        self.channel = tk.StringVar(value='COM4')
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TFrame', background=BG)
        style.configure('TButton', font=('Malgun Gothic', 10), padding=(14, 8), background='#25354c', foreground=TEXT)
        style.map('TButton', background=[('active', '#34506b')])
        style.configure('Treeview', background=PANEL, fieldbackground=PANEL, foreground=TEXT,
                        rowheight=31, borderwidth=0, font=('Consolas', 10))
        style.configure('Treeview.Heading', background='#213148', foreground=MUTED, font=('Segoe UI', 10))
        style.map('Treeview', background=[('selected', '#244b59')])
        self.build()
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.after(100, self.refresh)
        if demo:
            self.after(250, lambda: self.connect('demo'))

    def label(self, parent, text, size=10, color=TEXT, bg=BG, **kwargs):
        return tk.Label(parent, text=text, bg=bg, fg=color, font=('Malgun Gothic', size), **kwargs)

    def build(self):
        header = tk.Frame(self, bg=BG)
        header.pack(fill='x', padx=26, pady=(12, 6))
        self.label(header, 'VCU / MOTOR', 23, ACCENT).pack(side='left')
        self.label(header, 'PC → CANable → CAN → VCU → MOTOR', 11, MUTED).pack(side='right')
        tk.Label(self, textvariable=self.source, bg=BG, fg=ACCENT, font=('Malgun Gothic', 12), anchor='w').pack(fill='x', padx=28)
        controls = tk.Frame(self, bg=BG)
        controls.pack(fill='x', padx=26, pady=8)
        self.label(controls, 'CANable firmware').pack(side='left', padx=(0, 8))
        self.backend_box = ttk.Combobox(controls, textvariable=self.backend, values=('gs_usb', 'slcan'), state='readonly', width=10)
        self.backend_box.pack(side='left')
        self.backend_box.bind('<<ComboboxSelected>>', lambda _: self.channel.set('0' if self.backend.get()=='gs_usb' else ''))
        self.label(controls, '장치 index / COM').pack(side='left', padx=10)
        self.channel_box = ttk.Combobox(controls, textvariable=self.channel, width=12)
        self.channel_box.pack(side='left')
        self.scan_button = ttk.Button(controls, text='COM 검색', command=self.scan)
        self.scan_button.pack(side='left', padx=6)
        self.live_button = ttk.Button(controls, text='전체 연결', command=self.connect_all)
        self.live_button.pack(side='left', padx=4)
        self.demo_button = ttk.Button(controls, text='데모 시작', command=lambda: self.connect('demo'))
        self.demo_button.pack(side='left', padx=4)
        self.stop_button = ttk.Button(controls, text='연결 해제', command=self.stop, state='disabled')
        self.stop_button.pack(side='left', padx=4)
        self.build_drive_controls()
        cards = tk.Frame(self, bg=BG)
        cards.pack(fill='x', padx=26)
        for index, (key, title, unit) in enumerate((('rpm', 'MOTOR RPM', '0x110 · 가상 모터 모델'),
                    ('torque', 'TORQUE REQUEST', '0x100 · Nm'), ('gear', 'GEAR / BRAKE', '0x100 · VCU'),
                    ('state', 'MOTOR STATE', '0x110 · Motor'))):
            cards.columnconfigure(index, weight=1, uniform='cards')
            card=tk.Frame(cards, bg=PANEL)
            card.grid(row=0, column=index, sticky='ew', padx=(0, 10 if index<3 else 0))
            self.label(card, title, 10, MUTED, PANEL).pack(anchor='w', padx=16, pady=(12, 0))
            value=self.label(card, '--', 27, TEXT, PANEL)
            value.pack(anchor='w', padx=16, pady=2)
            self.cards[key]=value
            self.label(card, unit, 9, MUTED, PANEL).pack(anchor='w', padx=16, pady=(0, 12))
        self.health = tk.StringVar(value='VCU —  |  MOTOR —')
        tk.Label(self, textvariable=self.health, bg=BG, fg=MUTED, font=('Malgun Gothic', 10), anchor='w').pack(fill='x', padx=28, pady=6)
        self.chart=tk.Canvas(self, bg=PANEL, height=75, highlightthickness=0)
        self.chart.pack(fill='x', padx=26)
        self.label(self, 'RPM HISTORY  ·  24 s  /  0–12,000 rpm     |     끊긴 데이터는 그래프에 연결하지 않습니다', 9, MUTED).pack(anchor='w', padx=28, pady=(5, 12))
        self.label(self, 'RAW CAN  /  최신 프레임', 11).pack(anchor='w', padx=28, pady=(0, 6))
        table=tk.Frame(self, bg=BG)
        table.pack(fill='both', expand=True, padx=26)
        columns=('id','message','count','period','age','alive','data')
        self.tree=ttk.Treeview(table, columns=columns, show='headings', height=2)
        for key, title, width in zip(columns, ('ID / TYPE','MESSAGE','COUNT','Δ ms','AGE ms','ALIVE GAP','DATA'), (110,170,85,75,85,90,285)):
            self.tree.heading(key,text=title)
            self.tree.column(key,width=width,stretch=key in ('message','data'))
        self.tree.pack(side='left',fill='both',expand=True)
        scroll=ttk.Scrollbar(table,orient='vertical',command=self.tree.yview)
        scroll.pack(side='right',fill='y')
        self.tree.configure(yscrollcommand=scroll.set)
        self.summary=tk.StringVar()
        tk.Label(self,textvariable=self.summary,bg=BG,fg=ACCENT,font=('Consolas',10),anchor='w').pack(fill='x',padx=28,pady=(10,4))
        tk.Label(self,textvariable=self.details,bg=BG,fg=MUTED,font=('Malgun Gothic',9),anchor='w',wraplength=1100,justify='left').pack(fill='x',padx=28,pady=(0,16))

    def build_drive_controls(self):
        panel=tk.Frame(self,bg=PANEL)
        panel.pack(fill='x',padx=26,pady=(0,10))
        row=tk.Frame(panel,bg=PANEL); row.pack(fill='x',padx=12,pady=8)
        for text,var,values,width in (
            ('기어',self.drive_gear,('P','N','D','R'),5),
            ('가속 %',self.drive_pedal,tuple(str(x) for x in range(21)),5),
            ('실행 초',self.drive_duration,tuple(str(x) for x in range(1,11)),5)):
            self.label(row,text,10,MUTED,PANEL).pack(side='left',padx=(0,6))
            field=ttk.Combobox(row,textvariable=var,values=values or (),width=width,
                               state='readonly' if values else 'normal')
            field.pack(side='left',padx=(0,14))
            if var is self.vcu_port: self.vcu_port_box=field
        self.run_button=ttk.Button(row,text='▶ 실행',command=self.apply_drive,state='disabled')
        self.run_button.pack(side='left',padx=6)
        tk.Button(row,text='■ 정지 / 브레이크',command=self.brake,bg='#b52c3d',fg='white',
                  font=('Malgun Gothic',12,'bold'),padx=12,pady=5).pack(side='right')
        for var,color in ((self.drive_ready,ACCENT),(self.driver_status,MUTED)):
            tk.Label(panel,textvariable=var,bg=PANEL,fg=color,font=('Malgun Gothic',10),anchor='w').pack(fill='x',padx=14,pady=(0,5))

    def connect_all(self):
        if self.receiver and self.receiver.thread.is_alive(): return
        self.connect(self.backend.get(), control=True)
        self.driver_status.set('CAN 입력 연결 중 · P/브레이크로 시작')

    def apply_drive(self):
        try:
            if not self.driver: raise ValueError('먼저 전체 연결을 누르세요.')
            self.driver.apply(self.drive_gear.get(),int(self.drive_pedal.get()),float(self.drive_duration.get()))
            self.driver_status.set(f'요청: {self.drive_gear.get()} / {self.drive_pedal.get()}% / {self.drive_duration.get()}초 → 시간 종료 후 정지')
        except (ValueError,tk.TclError) as exc:
            if self.driver: self.driver.safe()
            self.driver_status.set(str(exc))

    def brake(self):
        if self.driver:
            self.driver.safe()
            self.driver_status.set('정지 요청: OFF / P / 토크 0 / 브레이크 · 아래 CAN 응답으로 확인')
        else: self.driver_status.set('VCU 미연결 — 정지 명령을 보낼 연결이 없습니다.')

    def scan(self):
        try:
            from serial.tools import list_ports
            ports=list(list_ports.comports())
            self.channel_box['values']=[p.device for p in ports]
            self.details.set(' / '.join(f'{p.device}: {p.description}' for p in ports) or 'COM 장치 없음. candleLight(gs_usb)는 COM으로 표시되지 않습니다.')
            if self.backend.get()=='slcan' and len(ports)==1:
                self.channel.set(ports[0].device)
        except Exception as exc:
            self.details.set(str(exc))

    def set_running(self, running):
        for widget in (self.live_button,self.demo_button,self.scan_button,self.channel_box):
            widget.configure(state='disabled' if running else 'normal')
        self.backend_box.configure(state='disabled' if running else 'readonly')
        self.stop_button.configure(state='normal' if running else 'disabled')

    def connect(self, backend, control=False):
        if self.receiver and self.receiver.thread.is_alive():
            return
        channel=self.channel.get().strip()
        if backend=='gs_usb' and (not channel.isdecimal()):
            self.details.set('gs_usb 장치 index는 0 이상의 정수입니다. CANable 1개는 0.')
            return
        if backend=='slcan' and not channel:
            self.details.set('COM 검색 후 실제 CANable 포트를 선택하세요.')
            return
        self.monitor=Monitor()
        self.history.clear()
        self.tree.delete(*self.tree.get_children())
        self.receiver=Receiver(backend,channel,ROOT/'captures')
        self.driver=None
        if control and backend!='demo':
            from can_input import CanInput
            self.driver=CanInput(self.receiver)
            self.receiver.control=self.driver
        self.source.set('CONNECTING…' if backend!='demo' else 'DEMO STARTING…')
        self.details.set('CAN 입력 TX 0x200 / VCU ACK RX 0x201 · LIVE 수신 CSV 기록')
        self.set_running(True)
        self.receiver.start()

    def stop(self):
        if self.driver: self.driver.stop()
        if self.receiver:
            self.receiver.stop()
            self.source.set('STOPPING…')
            self.stop_button.configure(state='disabled')

    def close(self):
        self.closing=True
        self.stop()
        self.wait_close()

    def wait_close(self):
        if (self.receiver and self.receiver.thread.is_alive()) or (self.driver and self.driver.thread.is_alive()):
            self.after(100,self.wait_close)
        else:
            self.destroy()

    def refresh(self):
        now=time.monotonic()
        if self.receiver:
            for _ in range(1200):
                try:
                    identifier,data,stamp,flags=self.receiver.frames.get_nowait()
                except queue.Empty:
                    break
                self.monitor.accept(identifier,data,stamp,**flags)
            while True:
                try:
                    event,value=self.receiver.events.get_nowait()
                except queue.Empty:
                    break
                if event=='connected': self.source.set(value)
                elif event=='error':
                    if self.driver: self.driver.stop()
                    self.source.set('CONNECTION ERROR')
                    self.details.set(value+' | 장치·펌웨어·드라이버를 확인하세요. 데모로 자동 전환하지 않습니다.')
                elif event=='log': self.details.set('CSV recording: '+value)
                elif event=='stopped':
                    if self.driver: self.driver.stop()
                    if self.source.get()!='CONNECTION ERROR': self.source.set('STOPPED — 수신 종료')
                    self.set_running(False)
        vcu=self.monitor.fresh(0x100,now)
        motor=self.monitor.fresh(0x110,now)
        healthy=False
        if self.driver:
            live = bool(self.receiver and self.receiver.backend != 'demo' and
                        self.receiver.thread.is_alive() and not self.receiver.stop_event.is_set())
            healthy = bool(live and vcu and motor and motor['state'] in ('READY','RUN') and
                           motor['rpm'] is not None and motor['torque'] is not None and
                           vcu['torque'] is not None)
            self.driver.feedback(healthy)
            while not self.driver.events.empty():
                message = self.driver.events.get_nowait()
                if self.driver_status is not None: self.driver_status.set(message)
        ready=bool(healthy and self.driver and self.driver.ready and not self.driver.quit.is_set())
        self.run_button.configure(state='normal' if ready else 'disabled')
        if ready:
            applied='--' if motor['torque'] is None else f"{motor['torque']:.1f} Nm"
            self.drive_ready.set(f'연결 정상  |  CAN ACK 0x201 OK → VCU 0x100 수신 → Motor 0x110 적용 토크 {applied}')
        elif self.receiver and self.receiver.backend=='demo':
            self.drive_ready.set('데모 화면입니다. 실제 구동은 연결 해제 후 전체 연결을 누르세요.')
        elif not self.driver or not self.driver.ready:
            self.drive_ready.set('VCU CAN ACK 대기 — CAN 입력용 펌웨어 / 0x201 응답을 확인하세요.')
        elif not vcu or not motor:
            self.drive_ready.set('CAN 수신 대기 — COM4, CAN_H/CAN_L, 500 kbps 및 두 보드 전원을 확인하세요.')
        else:
            self.drive_ready.set('실행 대기 — Motor 상태가 READY/RUN이고 연결이 정상이어야 합니다.')
        self.cards['rpm'].configure(text=str(motor['rpm']) if motor and motor['rpm'] is not None else '--')
        self.cards['torque'].configure(text=f"{vcu['torque']:.1f}" if vcu and vcu['torque'] is not None else '--')
        self.cards['gear'].configure(text=(vcu['gear']+(' / BRAKE' if vcu['brake'] else '')) if vcu else '--')
        self.cards['state'].configure(text=motor['state'] if motor else '--',fg='#ff8e87' if motor and motor['state']=='FAIL_SAFE' else TEXT)
        def status(identifier):
            s=self.monitor.sample(identifier)
            if not s: return 'WAITING'
            age=(now-s.timestamp)*1000
            return f'{age:.0f} ms'+(' · LATE >30 ms' if age>30 else ' · RX')
        self.health.set(f'VCU 0x100: {status(0x100)}   |   MOTOR 0x110: {status(0x110)}   |   명령·응답은 실제 CAN 수신값')
        alive_keys=set()
        for key,s in self.monitor.samples.items():
            identifier,extended,remote,error,fd=key
            row=str(key)
            alive_keys.add(row)
            kind='ERR' if error else 'FD' if fd else 'RTR' if remote else 'EXT' if extended else 'STD'
            values=(f'{identifier:03X} {kind}',NAMES.get(identifier,'Unknown') if kind=='STD' else kind,s.count,
                    f'{s.period_ms:.1f}' if s.period_ms is not None else '--',f'{(now-s.timestamp)*1000:.0f}',
                    s.alive_gaps if s.values and 'alive' in s.values else '--',s.data.hex(' ').upper())
            if self.tree.exists(row): self.tree.item(row,values=values)
            else: self.tree.insert('', 'end',iid=row,values=values)
        for row in self.tree.get_children():
            if row not in alive_keys: self.tree.delete(row)
        drops=self.receiver.drops if self.receiver else 0
        vehicle=self.monitor.fresh(0x120,now)
        speed=f"{vehicle['speed']:.1f} km/h" if vehicle and vehicle['speed'] is not None else '-- (no fresh Gateway speed)'
        tx=getattr(self.driver,'tx_count',0)
        ack=getattr(self.driver,'ack_count',0)
        self.summary.set(f'PC TX 0x200: {tx:,}   |   VCU ACK 0x201: {ack:,}   |   UI DROPS {drops:,}   |   UNDECODABLE {self.monitor.rejected:,}')
        self.history.append(motor['rpm'] if motor else None)
        self.draw_chart()
        if not self.closing: self.after(100,self.refresh)

    def draw_chart(self):
        c=self.chart
        c.delete('all')
        width,height=c.winfo_width(),c.winfo_height()
        for value in (0,6000,12000):
            y=height-20-value/12000*(height-40)
            c.create_line(55,y,width-15,y,fill='#25344b')
            c.create_text(45,y,text=f'{value:,}',fill=MUTED,anchor='e',font=('Consolas',9))
        segment=[]
        for index,value in enumerate(self.history):
            if value is None:
                if len(segment)>=4: c.create_line(*segment,fill=ACCENT,width=2)
                segment=[]
            else:
                segment.extend((55+index/239*max(1,width-75),height-20-value/12000*(height-40)))
        if len(segment)>=4: c.create_line(*segment,fill=ACCENT,width=2)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--demo',action='store_true',help='Start synthetic demo; no CAN access')
    args=parser.parse_args()
    Dashboard(demo=args.demo).mainloop()
