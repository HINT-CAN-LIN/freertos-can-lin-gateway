"""48-second dashboard bench demo. Run inside CANgaroo's Script window."""
import time
import cangaroo


def scenario(seconds):
    t = seconds % 48.0
    speed = round(2500 * (t / 24 if t <= 24 else (48 - t) / 24))
    rpm = round(speed * 12000 / 2500)
    gear = (0, 1, 2, 3)[min(int(t // 12), 3)]
    door = 2 if 8 <= t < 16 else 1
    window = 1 if 8 <= t < 16 else 2 if 16 <= t < 24 else 0
    lamps = 1 if 8 <= t < 16 else 32 if 16 <= t < 24 else 0
    brake = int(16 <= t < 24)
    system = 3 if 24 <= t < 40 else 2 if 40 <= t < 44 else 0
    stage = 1 if 24 <= t < 32 else 2 if 32 <= t < 40 else 3 if 40 <= t < 44 else 4 if t >= 44 else 0
    return speed, rpm, gear, door, window, lamps, brake, system, stage


def payloads(seconds, alive):
    speed, rpm, gear, door, window, lamps, brake, system, stage = scenario(seconds)
    vehicle = speed.to_bytes(2, 'little') + rpm.to_bytes(2, 'little') + bytes([gear | (brake << 3) | (system << 4), 0, 0, 0])
    vcu = bytes([0xE8, 3, gear | (brake << 3) | (alive[0] << 4), 0, 0, 0, 0, 0])
    motor = rpm.to_bytes(2, 'little') + bytes([0xE8, 3, 2 | (alive[1] << 2), 0, 0, 0])
    body = bytes([int(door >= 2) << 1, door, lamps, window, 0, 0, 0, 0])
    gateway = bytes([alive[4], 20, 0, 0, 0, 0, 0, 0])
    return [vcu, motor, vehicle, body, gateway], stage


def run():
    assert cangaroo.measurement_running(), 'Press Start/F5 first.'
    ports = [p for p in cangaroo.interfaces() if p['name'] == 'COM7' and p['bus_type'] == 'CAN']
    assert len(ports) == 1, 'COM7 not found. Check Setup Interface.'
    channel = ports[0]['id']

    def send(can_id, data):
        assert len(data) == 8
        msg = cangaroo.Message(can_id)
        msg.dlc = 8
        msg.extended = msg.fd = msg.rtr = False
        msg.set_data(bytes(data))
        cangaroo.send(msg, interface_id=channel)

    # Clear only the two faults used by this demo; other faults are not reset.
    send(0x310, [1, 0x11, 0, 0, 0, 0, 0, 0])
    send(0x310, [2, 0x15, 0, 0, 0, 0, 0, 0])
    ids = [0x100, 0x110, 0x120, 0x200, 0x300]
    periods = [0.010, 0.010, 0.020, 0.100, 0.100]
    alive = [0] * 5
    start = time.monotonic()
    due = [start] * 5
    last_stage = -1
    events = {1: [1, 0x61], 2: [2, 0x65], 3: [1, 0x51], 4: [2, 0x15]}
    print('Dashboard demo on COM7: 48s repeat, speed/RPM sweep, P/N/D/R, icons, Fault 1/2/1/0.')
    while cangaroo.measurement_running():
        now = time.monotonic()
        frames, stage = payloads(now - start, alive)
        if stage != last_stage:
            if stage in events:
                send(0x310, events[stage] + [0] * 6)
            print('Phase', stage, '- elapsed', round((now - start) % 48, 1), 's')
            last_stage = stage
        for i, can_id in enumerate(ids):
            if now < due[i]:
                continue
            send(can_id, frames[i])
            alive[i] = (alive[i] + 1) & 15
            due[i] += periods[i]
            if due[i] <= now:
                due[i] = now + periods[i]
        # shortcut: Windows/USB scheduling is approximate; use bus capture for timing validation.
        time.sleep(0.001)


run()
