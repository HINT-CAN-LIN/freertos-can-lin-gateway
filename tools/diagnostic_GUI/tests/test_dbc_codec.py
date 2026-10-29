from dataclasses import replace
import math

import pytest

from pc_diagnostic import DbcCodec, DbcEncodeError, DbcLoader, DecodeStatus, RawCanFrame


def test_decode_scaled_numeric_choices_and_raw_reference(dbc_codec):
    frame = RawCanFrame(1617, b"\x28\x00\x01\x07", timestamp=12.5, channel="test-only")
    result = dbc_codec.decode(frame)
    assert result.decode_status is DecodeStatus.DECODED
    assert result.message_name == "TestOnlySample"
    assert result.signals == {"Measurement": -10.0, "Mode": 1, "Counter": 7}
    assert result.raw_frame is frame and result.timestamp == 12.5
    assert result.arbitration_id == frame.arbitration_id and result.error is None
    with pytest.raises(TypeError):
        result.signals["Mode"] = 0


def test_encode_strict_and_choice_label(dbc_codec):
    frame = dbc_codec.encode("TestOnlySample", {"Measurement": -10.0, "Mode": "ONE", "Counter": 7})
    assert frame.data == b"\x28\x00\x01\x07"
    assert frame.dlc == 4 and frame.arbitration_id == 1617
    assert not frame.is_rx and not frame.is_extended_id
    assert frame.timestamp is None


@pytest.mark.parametrize("value", [-100.0, -10.0, 0.0, 100.0])
def test_roundtrip_signed_factor_offset(dbc_codec, value):
    signals = {"Measurement": value, "Mode": 2, "Counter": 255}
    frame = dbc_codec.encode("TestOnlySample", signals)
    assert dbc_codec.decode(frame).signals == signals


def test_big_endian_extended_roundtrip(dbc_codec):
    frame = dbc_codec.encode("TestOnlyExtended", {"Reading": 515})
    assert frame.is_extended_id and frame.data == b"\x01\x01"
    assert dbc_codec.decode(frame).signals == {"Reading": 515}
    wrong_format = dbc_codec.decode(replace(frame, is_extended_id=False))
    assert wrong_format.message_name == "TestOnlySample"
    assert wrong_format.decode_status is DecodeStatus.INVALID


def test_unknown_format_does_not_match_standard_definition(dbc_codec):
    frame = RawCanFrame(1618, b"\x00\x01", is_extended_id=True)
    result = dbc_codec.decode(frame)
    assert result.decode_status is DecodeStatus.UNKNOWN
    assert result.raw_frame is frame and result.signals == {} and result.error


@pytest.mark.parametrize("length", [0, 3, 5, 8])
def test_dbc_payload_length_mismatch(dbc_codec, length):
    frame = RawCanFrame(1617, bytes(length))
    result = dbc_codec.decode(frame)
    assert result.decode_status is DecodeStatus.INVALID
    assert result.raw_frame is frame and result.message_name == "TestOnlySample"
    assert "length mismatch" in result.error and not result.signals


def test_inconsistent_dlc_defensively_rejected(dbc_codec):
    frame = RawCanFrame(1617, bytes(4))
    # Simulate a malformed adapter object; normal RawCanFrame construction rejects this.
    object.__setattr__(frame, "dlc", 3)
    assert dbc_codec.decode(frame).decode_status is DecodeStatus.INVALID


def test_unknown_can_id_retains_raw(dbc_codec):
    frame = RawCanFrame(0x7FE, b"\xA5", timestamp=42)
    result = dbc_codec.decode(frame)
    assert result.decode_status is DecodeStatus.UNKNOWN
    assert result.raw_frame is frame and result.message_name is None and not result.signals
    assert result.to_record()["raw_frame"] == frame.to_record()


@pytest.mark.parametrize("flags", [{"is_remote_frame": True, "dlc": 4}, {"is_error_frame": True}])
def test_non_data_frame_is_invalid(dbc_codec, flags):
    frame = RawCanFrame(1617, **flags)
    assert dbc_codec.decode(frame).decode_status is DecodeStatus.INVALID


def test_unloaded_decoder_is_invalid_not_unknown():
    result = DbcCodec(DbcLoader()).decode(RawCanFrame(1617, bytes(4)))
    assert result.decode_status is DecodeStatus.INVALID
    assert "not loaded" in result.error


def test_decode_exception_does_not_escape(dbc_codec, dbc_loader, monkeypatch):
    message = dbc_loader.get_message_by_name("TestOnlySample")

    def fail(*args, **kwargs):
        raise RuntimeError("test-only decode failure")

    monkeypatch.setattr(message, "decode", fail)
    result = dbc_codec.decode(RawCanFrame(1617, bytes(4)))
    assert result.decode_status is DecodeStatus.INVALID and "decode failure" in result.error


@pytest.mark.parametrize("signals", [
    {"Mode": 1, "Counter": 0},
    {"Measurement": 101, "Mode": 1, "Counter": 0},
    {"Measurement": -101, "Mode": 1, "Counter": 0},
    {"Measurement": 0, "Mode": 3, "Counter": 0},
    {"Measurement": 0, "Mode": 1, "Counter": 256},
    {"Measurement": 0, "Mode": "NOT_IN_DBC", "Counter": 0},
    {"Measurement": 0, "Mode": 1, "Counter": 0, "InventedSignal": 1},
    {"Measurement": float("nan"), "Mode": 1, "Counter": 0},
    {"Measurement": float("inf"), "Mode": 1, "Counter": 0},
    {"Measurement": 0, "Mode": True, "Counter": 0},
    {"Measurement": 0, "Mode": None, "Counter": 0},
    [],
])
def test_invalid_encode_raises_without_frame(dbc_codec, signals):
    with pytest.raises(DbcEncodeError, match="DBC encode failed"):
        dbc_codec.encode("TestOnlySample", signals)


def test_missing_message_encode(dbc_codec):
    with pytest.raises(DbcEncodeError, match="unknown DBC message name"):
        dbc_codec.encode("NotDefined", {})


@pytest.mark.parametrize("selector,branch", [(0, "BranchZero"), (1, "BranchOne")])
def test_multiplexed_roundtrip(dbc_codec, selector, branch):
    signals = {"Selector": selector, branch: 25}
    frame = dbc_codec.encode("TestOnlyMux", signals)
    assert dbc_codec.decode(frame).signals == signals


def test_invalid_multiplexer_decode_and_encode(dbc_codec):
    result = dbc_codec.decode(RawCanFrame(1618, b"\x02\x00"))
    assert result.decode_status is DecodeStatus.INVALID
    with pytest.raises(DbcEncodeError):
        dbc_codec.encode("TestOnlyMux", {"Selector": 1, "BranchZero": 25})


def test_no_signal_invalid_or_health_policy_inferred(dbc_codec):
    # Mode raw 255 is outside the fixture's declared encode range. Decode remains
    # an unpack observation; it must not invent project invalid/health semantics.
    result = dbc_codec.decode(RawCanFrame(1617, b"\x00\x00\xFF\x00"))
    assert result.decode_status is DecodeStatus.DECODED and result.signals["Mode"] == 255


def test_unsupported_fd_definition(dbc_codec, dbc_loader, monkeypatch):
    message = dbc_loader.get_message_by_name("TestOnlySample")
    monkeypatch.setattr(message, "is_fd", True)
    result = dbc_codec.decode(RawCanFrame(1617, bytes(4)))
    assert result.decode_status is DecodeStatus.INVALID
    with pytest.raises(DbcEncodeError, match="Classic CAN"):
        dbc_codec.encode("TestOnlySample", {"Measurement": 0, "Mode": 0, "Counter": 0})


def test_nonfinite_decoded_float_is_invalid(dbc_codec, dbc_loader, monkeypatch):
    message = dbc_loader.get_message_by_name("TestOnlySample")
    monkeypatch.setattr(message, "decode", lambda *a, **kw: {"TestOnlyFloat": math.nan})
    assert dbc_codec.decode(RawCanFrame(1617, bytes(4))).decode_status is DecodeStatus.INVALID
