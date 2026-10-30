import time
import cangaroo

# Display validation only: PC/USB timing is not an ECU deadline measurement.
assert cangaroo.measurement_running(), 'Press F5 before Run.'
ports = [p for p in cangaroo.interfaces() if p['name'] == 'COM7' and p['bus_type'] == 'CAN']
assert len(ports) == 1, 'COM7 CAN interface not found; check Setup Interface.'
interface_id = ports[0]['id']
frames = [
    (0x100, 0.010, bytes.fromhex('E8 03 02 00 00 00 00 00'), 2, 4),
    (0x110, 0.010, bytes.fromhex('D2 04 E8 03 02 00 00 00'), 4, 2),
    (0x120, 0.020, bytes.fromhex('58 02 D2 04 02 00 00 00'), None, 0),
    (0x200, 0.100, bytes.fromhex('00 01 01 00 00 00 00 00'), None, 0),
    (0x300, 0.100, bytes.fromhex('00 14 00 00 00 00 00 00'), 0, 0),
]
assert len({f[0] for f in frames}) == 5 and all(len(f[2]) == 8 for f in frames)
assert int.from_bytes(frames[2][2][:2], 'little') / 10 == 60.0
assert int.from_bytes(frames[1][2][:2], 'little') == 1234
next_due = [time.monotonic()] * len(frames)
alive = [0] * len(frames)
print('Sending five cyclic IDs on COM7. Stop script to stop transmission.')
while cangaroo.measurement_running():
    now = time.monotonic()
    for i, (can_id, period, base, byte_index, shift) in enumerate(frames):
        if now < next_due[i]:
            continue
        data = bytearray(base)
        if byte_index is not None:
            data[byte_index] = (data[byte_index] & ~(15 << shift)) | (alive[i] << shift)
            alive[i] = (alive[i] + 1) & 15
        msg = cangaroo.Message(can_id)
        msg.dlc = 8
        msg.extended = False
        msg.fd = False
        msg.rtr = False
        msg.set_data(bytes(data))
        cangaroo.send(msg, interface_id=interface_id)
        next_due[i] += period
        if next_due[i] <= now:
            next_due[i] = now + period
    time.sleep(0.001)
