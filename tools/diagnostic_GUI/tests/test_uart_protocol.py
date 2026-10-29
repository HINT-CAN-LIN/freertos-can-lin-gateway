import pytest

from pc_diagnostic.gui.driver_input import DriverInputs
from pc_diagnostic.gui.uart_protocol import crc8, decode_ack, encode_driver_input, SYNC


def test_crc8_atm_check_vector():
    assert crc8(b"123456789") == 0xF4


def test_driver_input_matches_vcu_uart_layout_and_field_mask():
    packet = encode_driver_input(0x1234, DriverInputs(
        accelerator=75, brake=True, gear="D", ignition=True, door="LOCK", window="OPEN",
        steering_direction="RIGHT"))
    assert len(packet) == 15
    assert packet[:7] == bytes((0xA5, 0x5A, 2, 1, 0x34, 0x12, 0x7F))
    assert packet[7:14] == bytes((1, 75, 1, 2, 1, 2, 2))
    assert crc8(packet[2:14]) == packet[14]


def test_uart_rejects_fractional_accelerator_and_light_only():
    with pytest.raises(ValueError, match="integer percent"):
        encode_driver_input(0, DriverInputs(accelerator=25.5))
    with pytest.raises(ValueError, match="Light is Mock-only"):
        encode_driver_input(0, DriverInputs(light="ON"))


def test_ack_codec_checks_sequence_status_and_crc():
    body = bytes((2, 0x81, 0x78, 0x56, 0))
    frame = SYNC + body + bytes((crc8(body),))
    assert decode_ack(frame) == (0x5678, 0)
    with pytest.raises(ValueError, match="CRC"):
        decode_ack(frame[:-1] + bytes((frame[-1] ^ 1,)))


def test_ignition_enum_encodes_off_on_and_run():
    for state, encoded in (("OFF", 0), ("ON", 1), ("RUN", 2)):
        packet = encode_driver_input(9, DriverInputs(ignition=state))
        assert packet[7] == encoded


def test_uart_rejects_unknown_ignition_state():
    with pytest.raises(ValueError, match="OFF, ON, or RUN"):
        encode_driver_input(0, DriverInputs(ignition="START"))


def test_steering_direction_encodes_center_left_right():
    for direction, encoded in (("CENTER", 0), ("LEFT", 1), ("RIGHT", 2)):
        packet = encode_driver_input(7, DriverInputs(steering_direction=direction))
        assert packet[6] == (1 << 6)
        assert packet[13] == encoded


def test_uart_rejects_invalid_steering_direction():
    with pytest.raises(ValueError, match="Unsupported Mock steering_direction"):
        encode_driver_input(0, DriverInputs(steering_direction="HARD_LEFT"))
