from dataclasses import FrozenInstanceError

import pytest

from pc_diagnostic import RawCanFrame


# IDs and bytes below are synthetic unit-test vectors, not Gateway message definitions.
@pytest.mark.parametrize("identifier,extended", [(0, False), (0x7FF, False), (0x1FFFFFFF, True)])
@pytest.mark.parametrize("length", [0, 8])
def test_protocol_boundaries_and_roundtrip(identifier, extended, length):
    frame = RawCanFrame(identifier, bytes(range(length)), is_extended_id=extended,
                        timestamp=123.25, channel=0, is_rx=False)
    assert frame.dlc == length
    assert RawCanFrame.from_record(frame.to_record()) == frame


@pytest.mark.parametrize("values", [
    {"arbitration_id": -1}, {"arbitration_id": 0x800},
    {"arbitration_id": 0x20000000, "is_extended_id": True},
    {"arbitration_id": True}, {"data": bytes(9)}, {"data": 8},
    {"data": b"\x01", "dlc": 0}, {"dlc": -1}, {"dlc": True},
    {"is_remote_frame": True, "data": b"\x01"},
    {"is_remote_frame": True, "is_error_frame": True},
    {"timestamp": float("nan")}, {"timestamp": float("inf")}, {"timestamp": -1},
    {"timestamp": True}, {"is_extended_id": 1}, {"channel": []},
])
def test_reject_invalid_frame(values):
    with pytest.raises(ValueError):
        RawCanFrame(**({"arbitration_id": 0} | values))


def test_rtr_and_error_capture():
    assert RawCanFrame(0, is_remote_frame=True, dlc=8).data == b""
    assert RawCanFrame(0x10000, is_error_frame=True).is_error_frame


def test_immutable_payload():
    data = bytearray([1])
    frame = RawCanFrame(0, data)
    data[0] = 2
    assert frame.data == b"\x01"
    with pytest.raises(FrozenInstanceError):
        frame.dlc = 2


@pytest.mark.parametrize("record", [[], {}, {"arbitration_id": 0, "data": "GG"},
                                    {"arbitration_id": 0, "signal": "invented"}])
def test_invalid_record(record):
    with pytest.raises(ValueError):
        RawCanFrame.from_record(record)
