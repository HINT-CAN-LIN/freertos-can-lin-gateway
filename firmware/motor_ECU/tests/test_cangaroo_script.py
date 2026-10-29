"""No hardware I/O: exercise the generated CANgaroo script against a mock API."""
import importlib.util
from pathlib import Path
import sys
import re
import time
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "cangaroo" / "motor_control.py"
spec = importlib.util.spec_from_file_location("motor_script_under_test", SCRIPT)
motor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(motor)


class Message:
    id = 0

    def set_data(self, data):
        self.data = bytes(data)


class MockAPI:
    Message = Message

    def __init__(self):
        self.sent = []

    def measurement_running(self):
        return True

    def send(self, msg, interface_id=0):
        self.sent.append((interface_id, msg.id, msg.data))

    def receive(self, timeout=1):
        time.sleep(min(timeout, 0.005))
        return []

    def interfaces(self):
        return [{"id": 256, "name": "MOCK - NO HARDWARE", "bus_type": "CAN", "state": "open"}]


class ScriptTests(unittest.TestCase):
    def auto_controller(self):
        c = motor.Controller(MockAPI(), 256)
        c.status = {"state": 1, "alive": 0}
        c.status_at = 10
        c.set_command(motor.parse_command("auto"), now=10)
        return c

    def test_auto_full_cycle_and_wrap(self):
        c = self.auto_controller()
        now = 10
        self.assertEqual(sum(step[0] for step in motor.AUTO_STEPS), 30)
        for index in range(len(motor.AUTO_STEPS) + 1):
            seconds, percent, gear = motor.AUTO_STEPS[index % len(motor.AUTO_STEPS)]
            c.status_at = now
            payload, reason = c.next_payload(now)
            self.assertIn("AUTO step", reason)
            self.assertEqual(payload, motor.command_bytes(percent, gear, 0, (index * 2) % 16))
            self.assertEqual(payload[3:], b"\0\0\0\0\0")
            c.status_at = now + seconds / 2
            self.assertIsNone(c.next_payload(c.status_at)[1])
            now += seconds
        self.assertTrue(c.auto_active)
        self.assertEqual(c.auto_index, 0)

    def test_auto_stop_fault_loss_and_no_restart(self):
        for failure in ("stale", "failsafe", "off"):
            with self.subTest(failure=failure):
                c = self.auto_controller()
                c.next_payload(10)
                if failure == "stale":
                    now = 10.151
                else:
                    now = 10.01
                    c.status["state"] = 3 if failure == "failsafe" else 0
                payload, reason = c.next_payload(now)
                self.assertIn("AUTO stopped", reason)
                self.assertEqual(payload[:3], bytes.fromhex("000010"))
                self.assertEqual(payload[4:6], b"\0\0")
                self.assertFalse(c.auto_active)
                c.status = {"state": 1, "alive": 0}
                c.status_at = 100
                self.assertEqual(c.next_payload(100)[0][:2], b"\0\0")
        c = self.auto_controller()
        c.next_payload(10)
        c.set_command(motor.parse_command("s"), now=10.01)
        self.assertFalse(c.auto_active)
        self.assertEqual(c.next_payload(10.02)[0][4:6], b"\0\0")

    def test_auto_pause_loss_manual_override_and_late_tick(self):
        c = self.auto_controller()
        c.auto_index = 4
        payload, _ = c.next_payload(10)  # P/zero/center pause before reverse.
        self.assertEqual(payload[:3], b"\0\0\0")
        self.assertIsNotNone(c.next_payload(10.151)[1])
        self.assertFalse(c.auto_active)  # Even a stationary pause must disarm.
        c = self.auto_controller()
        c.next_payload(10)
        with self.assertRaisesRegex(ValueError, "not defined by the current DBC"):
            c.set_command(motor.parse_command("left 20 5"), now=10.01)
        payload, _ = c.next_payload(10.02)
        self.assertTrue(c.auto_active)
        self.assertEqual(payload[4:6], b"\0\0")
        c = self.auto_controller()
        c.next_payload(10)
        c.status_at = 100
        c.next_payload(100)
        self.assertEqual(c.auto_index, 1)  # Advance one step; no stale replay.
        self.assertEqual(c.auto_deadline, 105)

    def test_auto_requires_ready_status(self):
        self.assertEqual(motor.parse_command("auto"), ("auto",))
        c = motor.Controller(MockAPI(), 256)
        with self.assertRaises(ValueError):
            c.set_command(("auto",), now=10)
        c.status_at = 10
        c.status = {"state": 1, "alive": 0}
        c.set_command(("auto",), now=10)
        self.assertTrue(c.auto_active)

    def test_canonical_dbc_and_nonoverlapping_layout(self):
        local = SCRIPT.with_name("motor_ecu.dbc")
        canonical = SCRIPT.parents[3] / "network/can/CAN__DB_펌웨어 전 최종본_v0.1.dbc"
        self.assertEqual(local.read_bytes(), canonical.read_bytes())
        messages = {}
        for line in canonical.read_text(encoding="utf-8").splitlines():
            msg = re.match(r"BO_ (\d+) (\w+): (\d+)", line)
            if msg:
                current = int(msg[1])
                messages[current] = {}
            sig = re.match(r"\s*SG_ (\w+)\s*:\s*(\d+)\|(\d+)@1([+-])", line)
            if sig:
                messages[current][sig[1]] = (int(sig[2]), int(sig[3]), sig[4])
        self.assertNotIn("SteeringAngle", messages[0x100])
        self.assertEqual(messages[0x100]["TorqueRequest"], (0, 16, "+"))
        self.assertEqual(messages[0x100]["Gear"], (16, 3, "+"))
        self.assertEqual(messages[0x100]["Brake"], (19, 1, "+"))
        self.assertEqual(messages[0x100]["AliveCounter"], (20, 4, "+"))
        for signals in messages.values():
            occupied = set()
            for start, length, _ in signals.values():
                bits = set(range(start, start + length))
                self.assertLessEqual(start + length, 64)
                self.assertFalse(bits & occupied)
                occupied |= bits
        payload = motor.command_bytes(25, 2, 0, 15)
        self.assertEqual(payload[3:], b"\0\0\0\0\0")
        with self.assertRaisesRegex(ValueError, "not defined by the current DBC"):
            motor.command_bytes(25, 2, 0, 15, 5)

    def test_dbc_vectors(self):
        self.assertEqual(motor.command_bytes(10, 2, 0, 0).hex(), "a00f020000000000")
        self.assertEqual(motor.command_bytes(25, 3, 0, 15).hex(), "1027f30000000000")
        self.assertEqual(motor.command_bytes(100, 2, 1, 10).hex(), "409caa0000000000")
        self.assertEqual(motor.decode_status(bytes.fromhex("b004a00f3e000000")),
                         {"rpm": 1200, "torque_nm": 400, "state": 2, "alive": 15})

    def test_parser(self):
        self.assertEqual(motor.parse_command("d 10 5"), ("drive", 10, 2, 0, 5))
        self.assertEqual(motor.parse_command("r 25"), ("drive", 25, 3, 0, 5))
        for text in ("d nan", "d inf", "d -1", "d 101", "r 10 0", "r 10 61",
                     "d 10 nan", "d", "s extra", "wat"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                motor.parse_command(text)

    def test_direction_orders(self):
        self.assertEqual(motor.parse_command("forward 25 3"), ("drive", 25, 2, 0, 3))
        self.assertEqual(motor.parse_command("reverse 10 5"), ("drive", 10, 3, 0, 5))
        self.assertEqual(motor.parse_command("torque R 400 5"), ("drive", 10, 3, 0, 5))
        self.assertEqual(motor.parse_command("torque D 4000 1"), ("drive", 100, 2, 0, 1))
        for i, gear in enumerate("PNDR"):
            self.assertEqual(motor.parse_command("gear " + gear), ("stop", 0, i, 0, 0))
        for text in ("gear left", "gear D 10", "left 90", "servo 90",
                     "torque R -1", "torque D 4001", "torque D nan", "torque N 100"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                motor.parse_command(text)

    def test_direction_payload_and_alive(self):
        c = motor.Controller(MockAPI(), 256)
        c.status = {"state": 1, "alive": 0}
        c.status_at = 10
        c.set_command(motor.parse_command("reverse 25 3"), now=10)
        self.assertEqual(c.next_payload(10.01)[0], bytes.fromhex("1027030000000000"))
        c.set_command(motor.parse_command("gear D"), now=10.02)
        self.assertEqual(c.next_payload(10.02)[0], bytes.fromhex("0000120000000000"))

    def test_steering_encoding_and_retention(self):
        for angle in (-45, -20, 0, 20, 45):
            if angle:
                with self.subTest(angle=angle), self.assertRaisesRegex(
                        ValueError, "not defined by the current DBC"):
                    motor.command_bytes(10, 2, 0, 0, angle)
        for text in ("left 20 5", "right 20", "steer -20 5", "center",
                     "drive d 25 -20 5"):
            with self.subTest(text=text), self.assertRaisesRegex(
                    ValueError, "not defined by the current DBC"):
                motor.parse_command(text)

    def test_drive_uses_current_dbc_signals_only(self):
        parsed = motor.parse_command("drive d 25 5")
        self.assertEqual(parsed, ("drive", 25, 2, 0, 5))
        c = motor.Controller(MockAPI(), 256)
        c.status_at = 10
        c.status = {"state": 1, "alive": 0}
        c.set_command(parsed, now=10)
        self.assertEqual(c.next_payload(10.01)[0], bytes.fromhex("1027020000000000"))
        c.status_at = 15
        payload, _ = c.next_payload(15)
        self.assertEqual(payload[:2], b"\0\0")
        for text in ("drive d 25 -20 5", "drive n 25 20 5", "drive d 25 nan"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                motor.parse_command(text)

    def test_startup_and_alive(self):
        c = motor.Controller(MockAPI(), 256)
        for n in range(34):
            payload, reason = c.next_payload(n / 100)
            self.assertEqual(payload[0:2], b"\0\0")
            self.assertEqual(payload[2], (n % 16) << 4)
            self.assertIsNone(reason)
        with self.assertRaises(ValueError):
            c.set_command(motor.parse_command("d 10 5"), now=1)

    def test_duration_status_loss_and_no_restart(self):
        c = motor.Controller(MockAPI(), 256)
        c.status = {"state": 1, "firmware_revision": 4}
        c.status_at = 10
        c.set_command(motor.parse_command("d 10 5"), now=10)
        payload, _ = c.next_payload(10.01)
        self.assertEqual(payload[0:2], bytes.fromhex("a00f"))
        payload, reason = c.next_payload(10.151)
        self.assertEqual(payload[0:2], b"\0\0")
        self.assertIn("reply lost", reason)
        c.status_at = 11
        self.assertEqual(c.next_payload(11)[0][0:2], b"\0\0")
        c.set_command(motor.parse_command("r 10 5"), now=11)
        c.status_at = 16
        payload, reason = c.next_payload(16)
        self.assertEqual(payload[0:2], b"\0\0")
        self.assertIn("Duration", reason)
        c.set_command(motor.parse_command("d 10"), now=16)
        c.status["state"] = 3
        self.assertEqual(c.next_payload(16.01)[0][0:2], b"\0\0")

    def test_send_and_normal_quit(self):
        api = MockAPI()
        c = motor.Controller(api, 256)
        c.send_payload(motor.command_bytes(10, 2, 0, 0))
        self.assertEqual(api.sent[0], (256, 0x100, bytes.fromhex("a00f020000000000")))
        c.close()
        self.assertTrue(all(data[:2] == b"\0\0" for _, _, data in api.sent[1:]))

    def test_script_main_no_motion_without_drive(self):
        api = MockAPI()
        with patch.dict(sys.modules, {"cangaroo": api}), \
                patch("builtins.input", side_effect=["status", "bad command", "quit"]):
            motor.main()
        self.assertTrue(api.sent)
        self.assertTrue(all(iid == 256 and canid == 0x100 and data[:2] == b"\0\0"
                            for iid, canid, data in api.sent))


if __name__ == "__main__":
    unittest.main()
