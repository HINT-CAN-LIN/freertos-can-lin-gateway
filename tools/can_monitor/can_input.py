"""PC 0x200 -> VCU 0x201 handshake, serviced by the CAN bus owner thread."""
import time
from vcu_input import VcuInput, SAFE
from bench_vcu_motor import crc8


def encode(sequence, request):
    d=bytes([1,sequence&255,sequence>>8,*request])
    return d+bytes([crc8(d)])


class CanInput(VcuInput):
    def __init__(self, receiver):
        super().__init__('CAN')
        self.thread=receiver.thread
        self.sequence=0
        self.pending=None
        self.sent=0.0
        self.next_send=0.0
        self.tx_count=0
        self.ack_count=0
        self.on_tx=None

    def send(self, bus, request, now):
        import can
        self.sequence=(self.sequence+1)&65535
        data=encode(self.sequence,request)
        bus.send(can.Message(arbitration_id=0x200,data=data,is_extended_id=False),timeout=.05)
        self.pending=data
        self.sent=now
        self.next_send=now+.05
        self.tx_count+=1
        if self.on_tx: self.on_tx(data,now)

    def service(self, bus, now):
        if self.pending is not None and now-self.sent>=.20:
            self.ready=False
            self.safe()
            self.pending=None
            self.events.put('VCU CAN ACK 시간 초과 → 정지 요청 / 0x201 확인 필요')
        if self.pending is None and now>=self.next_send:
            self.send(bus,SAFE if self.quit.is_set() else self.current(now),now)

    def receive(self, message):
        d=bytes(message.data)
        p=self.pending
        if (message.arbitration_id!=0x201 or message.is_extended_id or message.is_remote_frame
                or message.is_error_frame or message.is_fd or len(d)!=8 or p is None): return
        if d[:3]!=p[:3] or crc8(d[:7])!=d[7]: return
        self.pending=None
        if d[3]!=0 or d[4:7]!=bytes([p[3],p[4],p[6]]):
            self.ready=False
            self.safe()
            self.events.put('VCU CAN 입력 거부 → 정지')
            return
        self.ack_count+=1
        if not self.ready:
            self.ready=True
            self.events.put('VCU CAN ACK 정상 · 0x200 입력 / 0x201 응답')

    def shutdown(self, bus):
        self.ready=False
        self.safe()
        for _ in range(3):
            self.send(bus,SAFE,time.monotonic())
            time.sleep(.01)
        self.events.put('CAN 정지 프레임 송신 완료 · 종료 ACK는 미확인')
