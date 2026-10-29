"""UART packet codec shared with the VCU serial contract."""
from .driver_input import DriverInputs

SYNC = b"\xA5\x5A"
VERSION = 2
TYPE_DRIVER_INPUT = 0x01
TYPE_ACK = 0x81
INPUT_SIZE = 15
ACK_SIZE = 8
ACK_STATUS = {
    0: "accepted", 1: "bad version", 2: "bad message type", 3: "bad CRC",
    4: "bad valid-field mask", 5: "invalid signal value", 6: "bad length", 7: "bad sync",
}


def crc8(data):
    """CRC-8/ATM: poly 0x07, init 0, no reflection/final xor."""
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) ^ 0x07) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


def encode_driver_input(sequence, inputs):
    """Encode the 15-byte A5 5A PC→VCU frame documented by the VCU firmware."""
    if type(sequence) is not int or not 0 <= sequence <= 0xFFFF:
        raise ValueError("UART sequence must be in 0..65535.")
    if not isinstance(inputs, DriverInputs):
        raise ValueError("DriverInputs required.")
    inputs.validated()
    mask = 0
    if inputs.ignition is not None:
        mask |= 1 << 0
    if inputs.accelerator is not None:
        if type(inputs.accelerator) not in (int, float) or int(inputs.accelerator) != inputs.accelerator:
            raise ValueError("UART accelerator must be an integer percent (0..100).")
        mask |= 1 << 1
    if inputs.brake is not None:
        mask |= 1 << 2
    if inputs.gear is not None:
        mask |= 1 << 3
    if inputs.door is not None:
        mask |= 1 << 4
    if inputs.window is not None:
        mask |= 1 << 5
    if inputs.steering_direction is not None:
        mask |= 1 << 6
    if not mask:
        raise ValueError("No VCU UART fields selected; Light is Mock-only.")
    ignition = ({"OFF": 0, "ON": 1, "RUN": 2}.get(inputs.ignition, 0)
                if type(inputs.ignition) is str else int(inputs.ignition is True))
    gear = {"P": 0, "N": 1, "D": 2, "R": 3}.get(inputs.gear, 0)
    door = {"LOCK": 1, "UNLOCK": 2}.get(inputs.door, 0)
    window = {"CLOSE": 1, "OPEN": 2}.get(inputs.window, 0)
    steering = {"CENTER": 0, "LEFT": 1, "RIGHT": 2}.get(inputs.steering_direction, 0)
    frame = bytearray((
        0xA5, 0x5A, VERSION, TYPE_DRIVER_INPUT, sequence & 0xFF, sequence >> 8,
        mask, ignition,
        int(inputs.accelerator) if inputs.accelerator is not None else 0,
        int(inputs.brake is True), gear, door, window, steering, 0,
    ))
    frame[-1] = crc8(frame[2:-1])
    return bytes(frame)


def decode_ack(frame):
    """Validate and decode one fixed 8-byte VCU ACK; return (sequence, status)."""
    frame = bytes(frame)
    if len(frame) != ACK_SIZE:
        raise ValueError("VCU ACK must be exactly 8 bytes.")
    if frame[:2] != SYNC:
        raise ValueError("VCU ACK sync mismatch.")
    if frame[2] != VERSION or frame[3] != TYPE_ACK:
        raise ValueError("VCU ACK version/type mismatch.")
    if crc8(frame[2:7]) != frame[7]:
        raise ValueError("VCU ACK CRC mismatch.")
    sequence = frame[4] | (frame[5] << 8)
    return sequence, frame[6]
