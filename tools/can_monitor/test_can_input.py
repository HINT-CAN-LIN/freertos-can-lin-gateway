import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
import can
from can_input import CanInput, encode, crc8, SAFE


class CanInputTests(unittest.TestCase):
    def setUp(self):
        self.ctrl=CanInput(SimpleNamespace(thread=Mock()))
        self.bus=Mock()

    def ack(self, seq=None, status=0):
        p=self.ctrl.pending
        d=bytes([1,p[1] if seq is None else seq,p[2],status,p[3],p[4],p[6]])
        return can.Message(arbitration_id=0x201,is_extended_id=False,data=d+bytes([crc8(d)]))

    def test_matching_ack_required(self):
        self.ctrl.service(self.bus,time.monotonic())
        self.assertEqual(bytes(self.bus.send.call_args.args[0].data),encode(1,SAFE))
        self.ctrl.receive(self.ack(seq=9))
        self.assertFalse(self.ctrl.ready)
        bad=self.ack(); bad.data[7]^=1
        self.ctrl.receive(bad)
        self.assertFalse(self.ctrl.ready)
        self.ctrl.receive(self.ack())
        self.assertTrue(self.ctrl.ready)
        self.ctrl.feedback(True)
        self.ctrl.apply('D',10,2)

    def test_ack_loss_cancels_motion_no_resume(self):
        now=time.monotonic()
        self.ctrl.service(self.bus,now)
        self.ctrl.receive(self.ack())
        self.ctrl.feedback(True)
        self.ctrl.apply('D',10,2)
        self.ctrl.service(self.bus,now+.06)
        self.assertEqual(self.ctrl.pending[4],10)
        self.ctrl.service(self.bus,now+.27)
        self.assertFalse(self.ctrl.ready)
        self.assertEqual(self.ctrl.pending[3:7],bytes(SAFE))
        self.ctrl.receive(self.ack())
        self.assertEqual(self.ctrl.current(now+.28),SAFE)

    def test_virtual_can_roundtrip_and_shutdown(self):
        with can.Bus(interface='virtual',channel='pc-input-test') as pc, can.Bus(interface='virtual',channel='pc-input-test') as ecu:
            self.ctrl.service(pc,time.monotonic())
            msg=ecu.recv(.1)
            self.assertEqual(msg.arbitration_id,0x200)
            ecu.send(self.ack())
            self.ctrl.receive(pc.recv(.1))
            self.assertTrue(self.ctrl.ready)
            self.ctrl.shutdown(pc)
            for _ in range(3): self.assertEqual(bytes(ecu.recv(.1).data)[3:7],bytes(SAFE))
            self.assertFalse(self.ctrl.ready)

    def test_rejection_cancels(self):
        self.ctrl.service(self.bus,time.monotonic())
        self.ctrl.receive(self.ack(status=2))
        self.assertFalse(self.ctrl.ready)
        self.assertEqual(self.ctrl.request,SAFE)

if __name__=='__main__': unittest.main()
