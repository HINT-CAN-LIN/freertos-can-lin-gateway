import csv
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import can
from protocol import Monitor, decode, demo_frames
from transport import Receiver


class ProtocolTests(unittest.TestCase):
    def test_vcu_known_vector(self):
        value=decode(0x100,bytes.fromhex('D2 04 FA 00 00 00 00 00'))
        self.assertEqual(value,dict(torque=123.4,gear='D',brake=True,alive=15))

    def test_motor_known_vector(self):
        value=decode(0x110,bytes.fromhex('B8 0B D2 04 3E 00 00 00'))
        self.assertEqual(value,dict(rpm=3000,torque=123.4,state='RUN',alive=15))

    def test_invalid_and_non_data(self):
        self.assertIsNone(decode(0x100,bytes(7)))
        for flag in ('extended','remote','error','fd'):
            self.assertIsNone(decode(0x100,bytes(8),**{flag:True}))
        self.assertIsNone(decode(0x110,bytes.fromhex('FF FF FF FF 00 00 00 00'))['rpm'])
        self.assertEqual(decode(0x100,bytes.fromhex('00 00 07 00 00 00 00 00'))['gear'],'INVALID')

    def test_alive_wrap_gap_expiry(self):
        m=Monitor()
        for i,alive in enumerate((15,0,0)):
            m.accept(0x100,bytes([0,0,alive<<4,0,0,0,0,0]),i*0.01)
        self.assertEqual(m.sample(0x100).alive_gaps,1)
        self.assertEqual(m.sample(0x100).period_ms,10)
        self.assertIsNone(m.fresh(0x100,1))
        # Remote and extended frames cannot overwrite the standard data sample.
        m.accept(0x100,bytes(8),2,extended=True)
        self.assertEqual(m.sample(0x100).timestamp,0.02)

    def test_cache_bound(self):
        m=Monitor()
        for i in range(1000): m.accept(i,bytes(8),i,extended=True)
        self.assertEqual(len(m.samples),512)

    def test_demo_layout(self):
        for i in range(32):
            for identifier,data in demo_frames(i):
                self.assertEqual(decode(identifier,data)['alive'],i%16)


class TransportTests(unittest.TestCase):
    def test_virtual_can_receive_and_csv(self):
        with tempfile.TemporaryDirectory() as folder:
            rx=can.Bus(interface='virtual',channel='three-ecu-test',ignore_config=True)
            tx=can.Bus(interface='virtual',channel='three-ecu-test',ignore_config=True)
            try:
                with patch('transport.open_bus',return_value=rx):
                    receiver=Receiver('slcan','TEST',folder)
                    receiver.start()
                    tx.send(can.Message(arbitration_id=0x100,data=bytes.fromhex('D2 04 FA 00 00 00 00 00'),is_extended_id=False))
                    identifier,data,stamp,flags=receiver.frames.get(timeout=2)
                    self.assertEqual(decode(identifier,data,**flags)['torque'],123.4)
                    receiver.stop()
                    receiver.thread.join(2)
                    self.assertFalse(receiver.thread.is_alive())
                with next(Path(folder).glob('*.csv')).open(encoding='utf-8') as stream:
                    rows=list(csv.DictReader(stream))
                self.assertEqual(rows[0]['id_hex'],'100')
                self.assertEqual(rows[0]['data_hex'],'D2 04 FA 00 00 00 00 00')
            finally: tx.shutdown()

    def test_connection_failure_no_demo_fallback(self):
        with patch('transport.open_bus',side_effect=RuntimeError('no device')):
            receiver=Receiver('gs_usb','0','unused')
            receiver.start()
            receiver.thread.join(2)
        self.assertEqual(receiver.events.get_nowait()[0],'error')
        self.assertTrue(receiver.frames.empty())

    def test_demo_stop(self):
        receiver=Receiver('demo','','unused')
        receiver.start()
        receiver.frames.get(timeout=2)
        receiver.stop()
        receiver.thread.join(2)
        self.assertFalse(receiver.thread.is_alive())


class GuiTests(unittest.TestCase):
    def test_dashboard_updates_and_expires(self):
        from can_monitor import Dashboard
        app=Dashboard()
        app.withdraw()
        try:
            now=time.monotonic()
            app.monitor.accept(0x100,bytes.fromhex('D2 04 FA 00 00 00 00 00'),now)
            app.monitor.accept(0x110,bytes.fromhex('B8 0B D2 04 3E 00 00 00'),now)
            app.refresh()
            self.assertEqual(app.cards['rpm'].cget('text'),'3000')
            self.assertEqual(app.cards['gear'].cget('text'),'D / BRAKE')
            self.assertEqual(len(app.tree.get_children()),2)
            app.monitor.sample(0x110).timestamp-=1
            app.refresh()
            self.assertEqual(app.cards['rpm'].cget('text'),'--')
        finally: app.destroy()


if __name__=='__main__': unittest.main()
