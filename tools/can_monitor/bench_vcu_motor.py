"""Explicit, bounded VCU UART -> real CAN -> Motor bench check. No CAN TX."""
import argparse
import json
from pathlib import Path
import queue
import time
import serial
from protocol import Monitor
from transport import Receiver


def crc8(data):
    crc=0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc=((crc<<1)^7)&255 if crc&128 else (crc<<1)&255
    return crc


def command(port, sequence, ignition=0, pedal=0, brake=1, gear=0):
    frame=bytearray([0xA5,0x5A,2,1,sequence&255,sequence>>8,15,
                     ignition,pedal,brake,gear,0,0,0])
    frame.append(crc8(frame[2:]))
    port.write(frame)
    ack=port.read(8)
    if len(ack)!=8 or ack[:6]!=bytes([0xA5,0x5A,2,0x81,sequence&255,sequence>>8]) or ack[6]!=0 or crc8(ack[2:7])!=ack[7]:
        raise RuntimeError('VCU ACK invalid: '+ack.hex(' '))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--can-port',required=True)
    parser.add_argument('--vcu-port',required=True)
    parser.add_argument('--run-motion-test',action='store_true',required=True,
                        help='Requires physically secured, unloaded motor bench')
    args=parser.parse_args()
    folder=Path(__file__).resolve().parents[2]/'output/can-integration/hardware-captures'
    receiver=Receiver('slcan',args.can_port,folder)
    monitor=Monitor()
    results=[]
    sequence=0

    def collect():
        while not receiver.frames.empty():
            identifier,data,stamp,flags=receiver.frames.get_nowait()
            monitor.accept(identifier,data,stamp,**flags)
        while not receiver.events.empty():
            event,message=receiver.events.get_nowait()
            print(event,message,flush=True)
            if event=='error': raise RuntimeError(message)

    receiver.start()
    try:
        with serial.Serial(args.vcu_port,115200,timeout=.15,write_timeout=.2) as port:
            port.reset_input_buffer()
            try:
                phases=[('safe_ready',1.5,(0,0,1,0)),
                        ('forward_10_percent',2.0,(2,10,0,2)),
                        ('brake',1.5,(2,10,1,2)),
                        ('park_off',1.5,(0,0,1,0))]
                # Wait for CANable startup before any motion.
                deadline=time.monotonic()+4
                while time.monotonic()<deadline:
                    collect()
                    if monitor.fresh(0x100,time.monotonic()) and monitor.fresh(0x110,time.monotonic()): break
                    time.sleep(.02)
                else: raise RuntimeError('Both CAN messages required before test')
                for name,duration,values in phases:
                    print('PHASE',name,flush=True)
                    end=time.monotonic()+duration
                    observed=[]
                    while time.monotonic()<end:
                        sequence+=1
                        command(port,sequence,*values)
                        time.sleep(.04)
                        collect()
                        now=time.monotonic()
                        vcu=monitor.fresh(0x100,now)
                        motor=monitor.fresh(0x110,now)
                        if not vcu or not motor: raise RuntimeError('CAN feedback missing; stopping')
                        observed.append((vcu,motor))
                    tail=observed[-5:]
                    if name=='forward_10_percent':
                        passed=all(v['gear']=='D' and v['torque']==400 and m['torque']==400 and m['state']=='RUN' and m['rpm']>0 for v,m in tail)
                    elif name=='brake':
                        passed=all(v['brake'] and v['torque']==0 and m['torque']==0 for v,m in tail)
                    else:
                        passed=all(v['gear']=='P' and v['torque']==0 and m['torque']==0 for v,m in tail)
                    result=dict(phase=name,passed=passed,vcu=tail[-1][0],motor=tail[-1][1],samples=len(observed))
                    results.append(result)
                    print(json.dumps(result),flush=True)
                    if not passed: raise RuntimeError('CAN response mismatch')
            finally:
                for _ in range(3):
                    sequence+=1
                    try: command(port,sequence)
                    except Exception as exc: print('STOP ACK:',exc,flush=True)
                    time.sleep(.05)
    finally:
        receiver.stop()
        receiver.thread.join(3)
        folder.mkdir(parents=True,exist_ok=True)
        report=folder/(time.strftime('%Y%m%d-%H%M%S')+'-bench-result.json')
        report.write_text(json.dumps(dict(phases=results,ui_drops=receiver.drops),indent=2),encoding='utf-8')
        print('REPORT',report,flush=True)
    return 0


if __name__=='__main__': raise SystemExit(main())
