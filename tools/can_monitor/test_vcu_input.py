import time
import unittest
from unittest.mock import patch
from vcu_input import VcuInput, SAFE


class InputTests(unittest.TestCase):
    def ready(self):
        driver=VcuInput('TEST')
        driver.ready=True
        driver.feedback(True)
        return driver

    def test_needs_ack_and_feedback(self):
        driver=VcuInput('TEST')
        with self.assertRaises(ValueError): driver.apply('D',10,2)
        driver.ready=True
        with self.assertRaises(ValueError): driver.apply('D',10,2)

    def test_limit_expiration_and_no_resume(self):
        driver=self.ready()
        driver.apply('D',10,2)
        self.assertEqual(driver.current(time.monotonic()),(2,10,0,2))
        driver.feedback(False)
        self.assertEqual(driver.current(time.monotonic()),SAFE)
        driver.feedback(True)
        self.assertEqual(driver.current(time.monotonic()),SAFE)
        driver.apply('R',10,1)
        self.assertEqual(driver.current(time.monotonic()+2),SAFE)
        for pedal,duration in ((21,2),(10,11),(10,float('nan'))):
            with self.assertRaises(ValueError): driver.apply('D',pedal,duration)

    def test_ui_freeze_and_manual_stop(self):
        driver=self.ready(); driver.apply('D',10,2)
        self.assertEqual(driver.current(time.monotonic()+.31),SAFE)
        driver.feedback(True); driver.apply('D',10,2); driver.safe()
        self.assertEqual(driver.current(time.monotonic()),SAFE)

    def test_shutdown_sends_safe(self):
        sent=[]
        driver=VcuInput('TEST')
        def capture(port,seq,*values):
            sent.append(values)
            driver.quit.set()
        with patch('vcu_input.serial.Serial'), patch('vcu_input.command',side_effect=capture):
            driver.run()
        self.assertEqual(sent,[SAFE]*4)
        self.assertFalse(driver.ready)

    def test_ack_failure_stops_worker(self):
        driver=VcuInput('TEST')
        with patch('vcu_input.serial.Serial'), patch('vcu_input.command',side_effect=RuntimeError('bad ACK')) as tx:
            driver.run()
        self.assertEqual(tx.call_count,4)
        self.assertFalse(driver.ready)


if __name__=='__main__': unittest.main()
