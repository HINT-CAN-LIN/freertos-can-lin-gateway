"""Load in CANgaroo Script View. USB input to real VCU; CAN RX only."""
import sys
import os
from pathlib import Path
import threading
import time

# CANgaroo executes editor text and does not guarantee __file__.
PROJECT = Path(os.environ.get('VCU_PROJECT_ROOT', Path.cwd()))
if not (PROJECT / 'tools/can_monitor').is_dir():
    raise RuntimeError('Launch with Start_CANgaroo.cmd, or set VCU_PROJECT_ROOT to the repository root.')
MODULES = PROJECT / 'tools/can_monitor'
# CANgaroo bundles Python but omits libffi required by ctypes/pyserial.
# Use the matching installed MSYS runtime without altering application files.
_runtime = Path(os.environ.get('CANGAROO_RUNTIME_DIR', 'C:/msys64/ucrt64/bin'))
_dll_directory = os.add_dll_directory(str(_runtime)) if os.name=='nt' and _runtime.is_dir() else None
for folder in (MODULES, MODULES/'.venv/lib/python3.14/site-packages',
               MODULES/'.venv/Lib/site-packages'):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
from protocol import Monitor
from vcu_input import VcuInput

VCU_PORT = 'COM6'


def parse(text):
    parts=text.lower().split()
    if parts in (['s'], ['stop'], ['b'], ['brake'], ['p']): return ('stop',)
    if parts in (['status'], ['help'], ['quit']): return (parts[0],)
    if len(parts) in (2,3) and parts[0] in ('d','r'):
        pedal=int(parts[1]); seconds=float(parts[2]) if len(parts)==3 else 2.0
        if not 0 <= pedal <= 20 or not 1 <= seconds <= 10:
            raise ValueError('Percent 0..20; duration 1..10 seconds')
        return ('drive',parts[0].upper(),pedal,seconds)
    raise ValueError('Use d 10 2 / r 10 2 / s / status / quit')


def main():
    import cangaroo
    if not cangaroo.measurement_running():
        raise RuntimeError('Start Measurement first (CANable COM4, 500 kbit/s).')
    interfaces=[x for x in cangaroo.interfaces() if x.get('bus_type')=='CAN' and 'COM4' in x.get('name','')]
    if len(interfaces)!=1:
        raise RuntimeError('Configure exactly one CAN interface for this workspace.')
    interface_id=interfaces[0]['id']
    monitor=Monitor()
    lock=threading.Lock()
    done=threading.Event()
    driver=VcuInput(VCU_PORT)

    def receive():
        try:
            while not done.is_set():
                if not cangaroo.measurement_running():
                    raise RuntimeError('Measurement stopped')
                messages=cangaroo.receive(timeout=.03)
                now=time.monotonic()
                with lock:
                    for msg in messages:
                        if msg.is_rx and msg.interface_id==interface_id:
                            monitor.accept(msg.id,bytes(msg.get_data()),now,
                                           extended=msg.extended,remote=msg.rtr,fd=msg.fd)
                    vcu=monitor.fresh(0x100,now)
                    motor=monitor.fresh(0x110,now)
                    healthy=bool(vcu and motor and motor['state'] in ('READY','RUN') and
                                 vcu['torque'] is not None and motor['torque'] is not None and motor['rpm'] is not None)
                driver.feedback(healthy)
                while not driver.events.empty(): print(driver.events.get_nowait())
        except BaseException as exc:
            print('RX stopped:',str(exc) or type(exc).__name__)
            driver.stop()
            done.set()

    def status():
        now=time.monotonic()
        with lock:
            for identifier in (0x100,0x110):
                sample=monitor.sample(identifier)
                if sample:
                    print(f'0x{identifier:X}: {sample.values} age={(now-sample.timestamp)*1000:.0f}ms RX={sample.count}')
                else: print(f'0x{identifier:X}: waiting for CAN RX')
        print('VCU USB ACK:', 'OK' if driver.ready else 'NOT READY')

    worker=threading.Thread(target=receive,daemon=True)
    print('REAL VCU -> CAN -> MOTOR. This script does NOT transmit CAN frames.')
    print('USB VCU port:',VCU_PORT,'; CAN interface:',interfaces[0]['name'])
    print('d 10 2 = forward 10% for 2s | r 10 2 = reverse | s = stop/brake')
    print('status = received signals | quit = stop and exit. Max 20%, max 10s.')
    driver.thread.start(); worker.start()
    try:
        while not done.is_set():
            try:
                action=parse(input('VCU> '))
                if action[0]=='quit': break
                if action[0]=='stop':
                    driver.safe(); print('P / zero / brake requested')
                elif action[0]=='drive':
                    driver.apply(*action[1:]); print('RUN requested:',action[1:])
                elif action[0]=='status': status()
                else: print('d 10 2 | r 10 2 | s | status | quit')
            except ValueError as exc:
                driver.safe(); print('Stopped:',exc)
    except (KeyboardInterrupt,EOFError):
        print('Stopping input')
    finally:
        done.set(); driver.stop()
        worker.join(.5); driver.thread.join(1.5)
        print('Stop requested. If USB is lost, VCU UART input expires after 500ms.')


if __name__ in ('__main__','builtins'):
    main()
