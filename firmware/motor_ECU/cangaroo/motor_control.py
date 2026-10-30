"""CANgaroo 0.7.0 Script View: VCU simulator for four DC motors and two SG90 servos.

Load this file into CANgaroo, start a 500 kbit/s measurement, then press Run.
Starts in P/zero torque. Enter auto to repeat speed/steering steps until s.
Commands: drive d 25 -20 5 / left 20 5 / right 20 5 / center / s / status.
10 = PWM percent, 5 = seconds. All four motors get the same command.
No external Python packages; run INSIDE CANgaroo, not regular Python.
"""
import math
import threading
import time

# Set to an integer from the printed interface list if more than one CAN
# interface is present. None auto-selects only when there is exactly one.
INTERFACE_ID = None
PERIOD_S = 0.010
STATUS_TIMEOUT_S = 0.150
DEFAULT_RUN_SECONDS = 5.0
MAX_RUN_SECONDS = 60.0
MAX_PERCENT = 100.0
STATUS_NAMES = ("OFF", "READY", "RUN", "FAIL_SAFE")
GEAR_NAMES = ("P", "N", "D", "R")
SCRIPT_VERSION = "1.5 - repeating automatic speed/steering sequence"
EXPECTED_FIRMWARE_REVISION = 4
# seconds, PWM percent, gear (0=P, 2=D, 3=R), steering degrees.
# One cycle is 30 seconds. Zero-torque centered pauses separate directions.
AUTO_STEPS = (
    (3.0, 20.0, 2, 0.0),
    (3.0, 25.0, 2, -20.0),
    (3.0, 35.0, 2, -40.0),
    (3.0, 20.0, 2, 0.0),
    (3.0, 25.0, 2, 20.0),
    (3.0, 35.0, 2, 40.0),
    (1.0, 0.0, 0, 0.0),
    (3.0, 20.0, 3, -20.0),
    (3.0, 25.0, 3, 0.0),
    (3.0, 20.0, 3, 20.0),
    (2.0, 0.0, 0, 0.0),
)


def command_bytes(percent, gear, brake, alive, steering_deg=0.0):
    """DBC 0x100: TorqueRequest 0|16 Intel factor .1; Gear/Brake/Alive byte2."""
    if not math.isfinite(percent) or not 0 <= percent <= 100:
        raise ValueError("PWM percent must be 0..100")
    if gear not in (0, 1, 2, 3) or brake not in (0, 1) or not 0 <= alive <= 15:
        raise ValueError("Invalid Gear/Brake/Alive")
    if not math.isfinite(steering_deg) or not -45 <= steering_deg <= 45:
        raise ValueError("SteeringAngle must be -45..45 degrees")
    steering_raw = round(steering_deg * 10) & 0xFFFF
    # Firmware demo map: 4000 Nm -> target 12000 RPM -> PWM 100%.
    raw = round(percent * 400)
    return bytes((raw & 255, raw >> 8, gear | (brake << 3) | (alive << 4),
                  0, steering_raw & 255, steering_raw >> 8, 0, 0))


def decode_status(data):
    if len(data) != 8:
        raise ValueError("Motor_Status must have DLC 8")
    return {
        "rpm": int.from_bytes(data[0:2], "little"),
        "torque_nm": int.from_bytes(data[2:4], "little") / 10,
        "state": data[4] & 3,
        "alive": (data[4] >> 2) & 15,
        "steering_echo_deg": int.from_bytes(data[5:7], "little", signed=True) / 10,
        "fault_flags": data[7] & 15,
        "firmware_revision": data[7] >> 4,
    }


def parse_command(text):
    parts = text.lower().split()
    if not parts:
        raise ValueError("Enter help for commands")
    name = parts[0]
    aliases = {"forward": "d", "fwd": "d", "reverse": "r", "rev": "r"}
    name = aliases.get(name, name)
    if name == "auto" and len(parts) == 1:
        return ("auto",)
    if name == "drive":
        if len(parts) not in (4, 5) or parts[1] not in ("d", "r"):
            raise ValueError("Use drive D/R PERCENT STEERING_DEG [SECONDS]")
        seconds = parts[4] if len(parts) == 5 else str(DEFAULT_RUN_SECONDS)
        drive = parse_command(f"{parts[1]} {parts[2]} {seconds}")
        steering = parse_command(f"steer {parts[3]} {seconds}")
        return drive + (steering[1],)
    if name in ("steer", "left", "right"):
        if len(parts) not in (2, 3):
            raise ValueError("Use steer DEGREES [SECONDS], left ANGLE or right ANGLE")
        angle = float(parts[1])
        seconds = float(parts[2]) if len(parts) == 3 else DEFAULT_RUN_SECONDS
        if not math.isfinite(angle) or not -45 <= angle <= 45:
            raise ValueError("SteeringAngle must be -45..45 degrees")
        if name in ("left", "right"):
            if angle < 0:
                raise ValueError("Use a positive angle with left/right")
            angle *= -1 if name == "left" else 1
        if not math.isfinite(seconds) or not 0 < seconds <= MAX_RUN_SECONDS:
            raise ValueError("Duration must be >0 and <=60 seconds")
        return ("steering", angle, seconds)
    if name == "center" and len(parts) == 1:
        return ("steering", 0.0, 0.0)
    if name == "gear":
        if len(parts) != 2 or parts[1] not in ("p", "n", "d", "r"):
            raise ValueError("Use gear P/N/D/R; gear selection always sets zero torque")
        return ("stop", 0.0, GEAR_NAMES.index(parts[1].upper()), 0, 0.0)
    if name == "torque":
        if len(parts) not in (3, 4) or parts[1] not in ("d", "r"):
            raise ValueError("Use torque D/R NM [SECONDS]")
        torque_nm = float(parts[2])
        if not math.isfinite(torque_nm) or not 0 <= torque_nm <= 4000:
            raise ValueError("TorqueRequest must be 0..4000 Nm per DBC")
        # 40 Nm per 1% is the existing firmware demonstrator calibration.
        seconds = parts[3] if len(parts) == 4 else str(DEFAULT_RUN_SECONDS)
        return parse_command(f"{parts[1]} {torque_nm / 40} {seconds}")
    if name in ("d", "r"):
        if len(parts) not in (2, 3):
            raise ValueError("Use d PERCENT [SECONDS] or r PERCENT [SECONDS]")
        percent = float(parts[1])
        seconds = float(parts[2]) if len(parts) == 3 else DEFAULT_RUN_SECONDS
        if not math.isfinite(percent) or not 0 <= percent <= MAX_PERCENT:
            raise ValueError("Percent must be 0..100")
        if not math.isfinite(seconds) or not 0 < seconds <= MAX_RUN_SECONDS:
            raise ValueError("Duration must be >0 and <=60 seconds")
        return ("drive", percent, 2 if name == "d" else 3, 0, seconds)
    if name in ("s", "stop", "p", "n", "b", "brake") and len(parts) == 1:
        return ("stop", 0.0, 1 if name == "n" else 0,
                1 if name in ("b", "brake") else 0, 0.0)
    if name in ("status", "help", "dbc", "quit", "q") and len(parts) == 1:
        return ("quit" if name == "q" else name,)
    raise ValueError("Unknown command; enter help")


class Controller:
    def __init__(self, api, interface_id):
        self.api = api
        self.interface_id = interface_id
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.command = (0.0, 0, 0, 0.0)  # percent, gear, brake, expiry
        self.alive = 0
        self.status = None
        self.status_at = None
        self.error = None
        self.tx_count = 0
        self.rx_count = 0
        self.threads = []
        self.last_payload = None
        self.steering_deg = 0.0
        self.steering_expiry = 0.0
        self.max_tx_gap_ms = 0.0
        self.last_tx_at = None
        self.auto_active = False
        self.auto_index = -1
        self.auto_deadline = 0.0

    def _clear_locked(self):
        self.command = (0.0, 0, 0, 0.0)
        self.steering_deg = self.steering_expiry = 0.0
        self.auto_active = False
        self.auto_index = -1
        self.auto_deadline = 0.0

    def stop_drive(self):
        with self.lock:
            self._clear_locked()

    def _auto_step_locked(self, now):
        self.auto_index = (self.auto_index + 1) % len(AUTO_STEPS)
        seconds, percent, gear, angle = AUTO_STEPS[self.auto_index]
        self.command = (percent, gear, 0, 0.0)
        self.steering_deg, self.steering_expiry = angle, 0.0
        # Skip missed time; never burst-replay past physical commands.
        self.auto_deadline = now + seconds
        return (f"AUTO step {self.auto_index + 1}/{len(AUTO_STEPS)}: "
                f"{GEAR_NAMES[gear]}, PWM={percent:g}%, steer={angle:g} deg, {seconds:g}s")

    def set_command(self, parsed, now=None):
        now = time.monotonic() if now is None else now
        with self.lock:
            if parsed[0] in ("auto", "drive") or (parsed[0] == "steering" and parsed[1] != 0):
                if self.error or self.stop_event.is_set():
                    raise ValueError("Script worker stopped; restart the script")
                if self.status_at is None or now - self.status_at > STATUS_TIMEOUT_S:
                    raise ValueError("No fresh 0x110 reply; verify ECU/interface/500 kbit/s")
                if self.status["state"] in (0, 3):
                    raise ValueError("ECU not ready; keep P commands running, enter status for fault flags")
                revision = self.status.get("firmware_revision", 0)
                if revision != EXPECTED_FIRMWARE_REVISION:
                    raise ValueError(f"ECU firmware revision={revision}; build/download new motor_ECU "
                                     f"firmware (expected {EXPECTED_FIRMWARE_REVISION}) before drive/steer")
            if parsed[0] == "auto":
                # Validate configurable steps before arming any physical output.
                for seconds, percent, gear, angle in AUTO_STEPS:
                    if not math.isfinite(seconds) or not 0 < seconds <= MAX_RUN_SECONDS:
                        raise ValueError("Invalid AUTO step duration")
                    command_bytes(percent, gear, 0, 0, angle)
                if not AUTO_STEPS:
                    raise ValueError("AUTO_STEPS is empty")
                self._clear_locked()
                self.auto_active = True
                return
            if self.auto_active:
                # A manual command takes over from a complete zero state.
                self._clear_locked()
            if parsed[0] == "steering":
                self.steering_deg = parsed[1]
                self.steering_expiry = now + parsed[2] if parsed[1] else 0
                return
            if parsed[0] == "stop":
                self.steering_deg = self.steering_expiry = 0.0
            elif len(parsed) == 6:
                self.steering_deg = parsed[5]
                self.steering_expiry = now + parsed[4] if parsed[5] else 0.0
            self.command = (parsed[1], parsed[2], parsed[3],
                            now + parsed[4] if parsed[0] == "drive" else 0.0)

    def next_payload(self, now):
        with self.lock:
            auto_reason = None
            if self.auto_active:
                if self.status_at is None or now - self.status_at > STATUS_TIMEOUT_S:
                    auto_reason = "AUTO stopped: 0x110 reply lost; enter auto explicitly to restart"
                elif self.status["state"] not in (1, 2):
                    auto_reason = (f"AUTO stopped: ECU {STATUS_NAMES[self.status['state']]} "
                                   f"flags=0x{self.status.get('fault_flags', 0):X}; enter auto to restart")
                elif self.status.get("firmware_revision", 0) != EXPECTED_FIRMWARE_REVISION:
                    auto_reason = "AUTO stopped: firmware revision mismatch"
                if auto_reason:
                    self._clear_locked()
                elif now >= self.auto_deadline:
                    auto_reason = self._auto_step_locked(now)
            percent, gear, brake, expiry = self.command
            reason = auto_reason
            if self.steering_expiry and now >= self.steering_expiry:
                self.steering_deg = self.steering_expiry = 0.0
                reason = "Steering duration finished -> requested angle 0 degrees"
            if percent > 0 or self.steering_deg != 0:
                stop_reason = None
                if percent > 0 and expiry and now >= expiry:
                    stop_reason = "Duration finished -> P/zero torque"
                elif self.status_at is None or now - self.status_at > STATUS_TIMEOUT_S:
                    stop_reason = "0x110 reply lost -> P/zero torque; explicit drive command required"
                elif self.status["state"] == 3:
                    flags = self.status.get("fault_flags", 0)
                    stop_reason = (f"ECU FAIL_SAFE flags=0x{flags:X} "
                                   f"({fault_names(flags)}) -> P/zero torque; enter status")
                if stop_reason:
                    reason = stop_reason
                    self._clear_locked()
                    percent, gear, brake = 0.0, 0, 0
                    self.steering_deg = self.steering_expiry = 0.0
            payload = command_bytes(percent, gear, brake, self.alive, self.steering_deg)
            self.alive = (self.alive + 1) & 15
        return payload, reason

    def send_payload(self, payload):
        msg = self.api.Message()
        msg.id = 0x100
        msg.set_data(payload)
        self.api.send(msg, interface_id=self.interface_id)
        now = time.monotonic()
        if self.last_tx_at is not None:
            self.max_tx_gap_ms = max(self.max_tx_gap_ms, (now - self.last_tx_at) * 1000)
        self.last_tx_at = now
        self.last_payload = payload
        self.tx_count += 1

    def sender(self):
        deadline = time.monotonic()
        try:
            while not self.stop_event.is_set():
                if not self.api.measurement_running():
                    raise RuntimeError("Measurement stopped")
                now = time.monotonic()
                payload, reason = self.next_payload(now)
                if reason:
                    print(reason)
                self.send_payload(payload)
                deadline += PERIOD_S
                # Never burst-replay obsolete commands after a scheduler delay.
                delay = deadline - time.monotonic()
                if delay <= 0:
                    deadline = time.monotonic()
                else:
                    self.stop_event.wait(delay)
        except BaseException as exc:
            self.error = str(exc) or type(exc).__name__
            self.stop_drive()
            self.stop_event.set()
            print("TX stopped:", self.error)

    def receiver(self):
        try:
            while not self.stop_event.is_set():
                for msg in self.api.receive(timeout=0.05):
                    if (msg.id != 0x110 or not msg.is_rx or
                            msg.interface_id != self.interface_id):
                        continue
                    data = msg.get_data()
                    if len(data) != 8:
                        continue
                    with self.lock:
                        self.status = decode_status(data)
                        self.status_at = time.monotonic()
                        self.rx_count += 1
        except BaseException as exc:
            self.error = str(exc) or type(exc).__name__
            self.stop_drive()
            self.stop_event.set()
            print("RX stopped:", self.error)

    def start(self):
        for target in (self.sender, self.receiver):
            thread = threading.Thread(target=target, daemon=True)
            self.threads.append(thread)
            thread.start()

    def close(self):
        self.stop_drive()
        self.stop_event.set()
        for thread in self.threads:
            thread.join(timeout=0.5)
        if any(thread.is_alive() for thread in self.threads):
            print("Worker still stopping; ECU command timeout provides output cutoff")
            return
        # Normal 'quit' path: explicitly send zero before ending. The CANgaroo
        # Stop button can interrupt Python cleanup, so ECU timeout remains vital.
        if self.api.measurement_running():
            for _ in range(4):
                self.send_payload(command_bytes(0, 0, 0, self.alive))
                self.alive = (self.alive + 1) & 15
                time.sleep(PERIOD_S)


def fault_names(flags):
    names = [name for bit, name in ((1, "TIMEOUT"), (2, "ALIVE_SEQUENCE"),
                                  (4, "INVALID_INPUT"), (8, "RX_QUEUE_LOSS"))
             if flags & bit]
    return ",".join(names) if names else "none/unknown"


def print_status(controller):
    with controller.lock:
        status = controller.status.copy() if controller.status else None
        age = None if controller.status_at is None else time.monotonic() - controller.status_at
        command = controller.command
        steering_deg = controller.steering_deg
        auto_info = (controller.auto_active, controller.auto_index)
    print(f"TX={controller.tx_count} RX={controller.rx_count}; command={command[:3]}")
    print(f"AUTO={'ON' if auto_info[0] else 'OFF'}, step={auto_info[1] + 1}/{len(AUTO_STEPS)}")
    print(f"Order: Gear={GEAR_NAMES[command[1]]}, Brake={command[2]}, "
          f"TorqueRequest={command[0] * 40:.1f} Nm, demo PWM={command[0]:g}%")
    print(f"Requested SteeringAngle={steering_deg:g} deg; "
          f"max TX API interval={controller.max_tx_gap_ms:.1f}ms (not bus delivery timing)")
    if controller.last_payload is not None:
        print("Last 0x100 payload:", controller.last_payload.hex(" ").upper())
    if status is None:
        print("No Motor_Status (0x110) received")
    else:
        print(f"Virtual RPM={status['rpm']} TorqueApplied={status['torque_nm']:.1f} Nm "
              f"State={STATUS_NAMES[status['state']]} Alive={status['alive']} age={age:.3f}s")
        revision = status.get("firmware_revision", 0)
        flags = status.get("fault_flags", 0)
        print(f"ECU firmware revision={revision} (expected {EXPECTED_FIRMWARE_REVISION}), "
              f"faults=0x{flags:X} [{fault_names(flags)}]")
        print(f"ECU validated steering target={status.get('steering_echo_deg', 0):g} deg "
              "(not measured SG90 shaft angle)")
    if controller.error:
        print("Worker error:", controller.error)


def print_help():
    print("auto : repeat speed/left/center/right sequence, including reverse; s stops")
    print("AUTO uses PWM 20..35%, steer -40..+40 deg; 30s/cycle, repeats until stopped")
    print("Any manual command cancels AUTO; status/help/dbc only observe")
    print("forward 10 5 / d 10 5 : D, PWM 10%, 5 seconds (all four motors)")
    print("reverse 10 5 / r 10 5 : R, PWM 10%, 5 seconds (all four motors)")
    print("gear P/N/D/R : select gear with ZERO torque; does not start movement")
    print("torque D 400 5 : D, TorqueRequest=400 Nm, 5 seconds (demo PWM=10%)")
    print("s / p  : zero torque + P; n : neutral; b : brake")
    print("status : show 0x110 virtual RPM/state and command")
    print("quit   : send zero and end; help : show commands")
    print("Duration defaults to 5 seconds, maximum 60 seconds")
    print("left 20 5 / right 20 5 : request left/right 20 degrees for 5 seconds")
    print("steer -20 5 / center : signed angle request / angle zero")
    print("drive d 25 -20 5 : DC forward 25% + left20 degrees, both for 5 seconds")
    print("drive r 25 20 5 : DC reverse 25% + right20 degrees, both for 5 seconds")
    print("Requires firmware revision 4; SG90 PWM on PA0/PA1, 50Hz, center 1500us.")
    print("dbc : explain CAN command layout")


def print_dbc_orders():
    print("VCU_Command: standard ID=0x100, DLC=8, period=10ms")
    print("Byte0..1: TorqueRequest raw=Nm*10, Intel/little-endian, range 0..4000 Nm")
    print("Byte2 bits0..2: Gear 0=P, 1=N, 2=D(forward), 3=R(reverse)")
    print("Byte2 bit3: Brake; bits4..7: AliveCounter 0..15, increment each frame")
    print("Byte3: reserved for Gateway Body command candidates; this script sends zero")
    print("Byte4..5: signed Intel SteeringAngle, raw=degrees*10; -45 left..+45 right")
    print("Byte6..7: unused; zero")
    print("Byte2 = (Alive<<4) | (Brake<<3) | Gear")
    print("Single logical angle; no separate SG90 commands or measured angle feedback.")
    print("Motor_Status Byte5..6: validated steering target echo; Byte7 low=FaultFlags, high=FW revision")
    print("LightStatus LEFT_TURN/RIGHT_TURN are indicators, not steering commands.")
    print("Vehicle_Status 0x120.Gear is Gateway feedback, not the Motor ECU command.")


def main():
    import cangaroo
    if not cangaroo.measurement_running():
        raise RuntimeError("Start a 500 kbit/s CAN measurement before Run")
    interfaces = [item for item in cangaroo.interfaces() if item.get("bus_type") == "CAN"]
    for item in interfaces:
        print(f"CAN interface {item['id']}: {item['name']} ({item.get('state', '')})")
    if INTERFACE_ID is None:
        if not interfaces:
            raise RuntimeError("No CAN interfaces configured in Measurement Setup")
        if len(interfaces) == 1:
            interface_id = interfaces[0]["id"]
        else:
            interface_id = int(input("CAN interface id from list above> "))
            if not any(item["id"] == interface_id for item in interfaces):
                raise ValueError("Interface id is not in the CAN interface list")
    else:
        if not any(item["id"] == INTERFACE_ID for item in interfaces):
            raise RuntimeError("Configured INTERFACE_ID is not available")
        interface_id = INTERFACE_ID
    print("VCU_Command=0x100, Motor_Status=0x110, DLC=8, 10ms, incrementing Alive")
    print("Motor script", SCRIPT_VERSION)
    print("Started in P/zero torque. Wait for READY, then enter a drive command.")
    print("Stop any Raw TX/Generator sending 0x100 before using this script.")
    print_help()
    controller = Controller(cangaroo, interface_id)
    controller.start()
    try:
        while not controller.stop_event.is_set():
            try:
                parsed = parse_command(input("motor> "))
                if parsed[0] == "quit":
                    break
                if parsed[0] == "help":
                    print_help()
                elif parsed[0] == "status":
                    print_status(controller)
                elif parsed[0] == "dbc":
                    print_dbc_orders()
                else:
                    controller.set_command(parsed)
                    if parsed[0] == "auto":
                        print("AUTO armed: repeating forward/reverse and steering steps; enter s to stop")
                        continue
                    if parsed[0] == "steering":
                        print(f"SteeringAngle request={parsed[1]:g} deg, "
                              f"duration={parsed[2]:g}s; two SG90 PWM outputs")
                        continue
                    print(f"Order: Gear={GEAR_NAMES[parsed[2]]}({parsed[2]}) "
                          f"TorqueRequest={parsed[1] * 40:.1f} Nm "
                          f"demo PWM={parsed[1]:g}% Brake={parsed[3]} "
                          f"duration={parsed[4]:g}s")
                    if len(parsed) == 6:
                        print(f"Simultaneous steering target={parsed[5]:g} deg")
            except ValueError as exc:
                controller.stop_drive()
                print("Stopped:", exc)
    except (KeyboardInterrupt, EOFError):
        print("Stopping motor script")
    finally:
        controller.close()
        print("Script ended. ECU cuts output on command age >30ms.")


# CANgaroo executes editor text with py::exec; no reliance on __name__.
# Tests import with runpy.run_path(), which deliberately sets __name__ differently.
if __name__ in ("__main__", "builtins"):
    main()
