#!/usr/bin/env python3
"""No third-party dependencies. Build artifacts stay in a temporary directory."""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
TEST = Path(__file__).resolve().parent
FW = ROOT / "firmware/vcu_ECU"
DBC = ROOT / "network/can/CAN__DB_펌웨어 전 최종본_v0.1.dbc"
text = DBC.read_text()
can_source = (FW / "Core/Src/can.c").read_text()
ioc = (FW / "vcu_ECU.ioc").read_text()
assert "hcan1.Init.Mode = CAN_MODE_NORMAL;" in can_source
assert "CAN1.Mode=CAN_MODE_NORMAL" in ioc
block = re.search(r"BO_ 256 VCU_Command: 8 VCU\n(.*?)(?=\nBO_)", text, re.S)
assert block is not None
signals = re.findall(
    r'SG_ (\w+) : (\d+)\|(\d+)@1\+ \(([^,]+),([^\)]+)\) \[([^|]+)\|([^\]]+)\]',
    block[1],
)
assert signals == [
    ("TorqueRequest", "0", "16", "0.1", "0", "0", "4000"),
    ("Gear", "16", "3", "1", "0", "0", "3"),
    ("Brake", "19", "1", "1", "0", "0", "1"),
    ("AliveCounter", "20", "4", "1", "0", "0", "15"),
    ("DoorLockRequest", "28", "2", "1", "0", "0", "2"),
    ("WindowCommand", "30", "2", "1", "0", "0", "2"),
], "DBC changed: review codec before using it"
assert 'BA_ "GenMsgCycleTime" BO_ 256 10;' in text
assert 'VAL_ 256 Gear 0 "P" 1 "N" 2 "D" 3 "R"' in text
assert 'VAL_ 256 DoorLockRequest 0 "NO_ACTION" 1 "LOCK" 2 "UNLOCK" 3 "INVALID"' in text
assert 'VAL_ 256 WindowCommand 0 "STOP" 1 "UP" 2 "DOWN" 3 "INVALID"' in text
assert 'BA_ "GenSigInvalidValue" SG_ 256 DoorLockRequest 3;' in text
assert 'BA_ "GenSigInvalidValue" SG_ 256 WindowCommand 3;' in text
with tempfile.TemporaryDirectory(prefix="vcu-phase1-test-") as temp:
    exe = Path(temp) / "test_phase1"
    subprocess.run([
        "cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
        "-fsanitize=address,undefined", "-I", str(TEST / "stubs"),
        "-I", str(FW / "Core/Inc"), "-include", str(TEST / "stubs/hal.h"),
        str(TEST / "test_phase1.c"),
        *[str(FW / "Core/Src" / name) for name in
          ("vcu_app.c", "vcu_driver_input_mock.c", "vcu_command_codec.c",
           "vcu_serial_protocol.c", "vcu_can.c", "vcu_task.c")],
        "-o", str(exe),
    ], check=True)
    subprocess.run([str(exe)], check=True)
print("PASS: current DBC layout, cycle, and gear/door/window enums")
