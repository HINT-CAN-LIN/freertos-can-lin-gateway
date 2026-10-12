from dataclasses import replace
import json
from unittest.mock import Mock

import pytest

from pc_diagnostic import DecodeService, DecodeStatus, MockCanInterface, RawCanFrame, RawCanLogger
from pc_diagnostic.cli import main
from pc_diagnostic.monitor import capture


def test_mock_decode_cache_pipeline_continues_after_failures(dbc_codec):
    first = replace(dbc_codec.encode("TestOnlySample", {"Measurement": 0, "Mode": 0, "Counter": 0}),
                    is_rx=True, timestamp=1)
    last = replace(dbc_codec.encode("TestOnlySample", {"Measurement": 10, "Mode": 2, "Counter": 7}),
                   is_rx=True, timestamp=4)
    frames = [first, RawCanFrame(0x7FE, b"\xFF", timestamp=2),
              RawCanFrame(1617, b"\x00", timestamp=3), last]
    service = DecodeService(dbc_codec)
    results = []

    def receive(frame):
        results.append(service.process(frame))

    with MockCanInterface(frames) as interface:
        assert capture(interface, receive, count=4) == 4
        assert interface.sent_frames == ()
    assert [r.decode_status for r in results] == [DecodeStatus.DECODED, DecodeStatus.UNKNOWN,
                                                DecodeStatus.INVALID, DecodeStatus.DECODED]
    assert [r.raw_frame for r in results] == frames
    assert service.cache.get_signal("TestOnlySample", "Measurement") == 10
    assert service.cache.last_timestamp("TestOnlySample") == 4


def test_decode_cli_reuses_capture_and_retains_raw(synthetic_dbc_path, tmp_path, capsys):
    source = tmp_path / "test_only_frames.jsonl"
    frames = [RawCanFrame(1617, b"\x28\x00\x01\x07", timestamp=1),
              RawCanFrame(0x7FE), RawCanFrame(1617, b"\x00"),
              RawCanFrame(1617, b"\x00\x00\x02\x01", timestamp=4)]
    with RawCanLogger(source) as logger:
        for frame in frames:
            logger.write(frame)
    assert main(["decode", "--dbc", str(synthetic_dbc_path), "--input", str(source)]) == 0
    output = capsys.readouterr()
    records = [json.loads(line) for line in output.out.splitlines()]
    assert [r["decode_status"] for r in records] == ["decoded", "unknown", "invalid", "decoded"]
    assert [r["raw_frame"] for r in records] == [f.to_record() for f in frames]
    assert "Captured 4" in output.err


def test_encode_cli_is_pure_and_emits_raw_schema(synthetic_dbc_path, monkeypatch, capsys):
    mock_factory = Mock(side_effect=AssertionError("encode must not open a bus"))
    monkeypatch.setattr("pc_diagnostic.cli.MockCanInterface", mock_factory)
    monkeypatch.setattr("pc_diagnostic.cli.PythonCanInterface", mock_factory)
    args = ["encode", "--dbc", str(synthetic_dbc_path), "--message", "TestOnlySample", "--signals",
            '{"Measurement":-10,"Mode":"ONE","Counter":7}']
    assert main(args) == 0
    frame = RawCanFrame.from_record(json.loads(capsys.readouterr().out))
    assert frame.data == b"\x28\x00\x01\x07" and not frame.is_rx
    mock_factory.assert_not_called()


@pytest.mark.parametrize("signals", ['{"Mode":1}', '{"Measurement":101,"Mode":1,"Counter":0}',
                                     'not-json', '[]', '{"Measurement":NaN,"Mode":1,"Counter":0}'])
def test_invalid_encode_cli_has_no_frame_output(synthetic_dbc_path, signals, capsys):
    assert main(["encode", "--dbc", str(synthetic_dbc_path), "--message", "TestOnlySample",
                 "--signals", signals]) == 1
    assert capsys.readouterr().out == ""


def test_failed_dbc_load_does_not_open_transport_or_break_raw(tmp_path, monkeypatch, capsys):
    factory = Mock(side_effect=AssertionError("DBC must load before bus open"))
    monkeypatch.setattr("pc_diagnostic.cli.PythonCanInterface", factory)
    assert main(["decode", "--dbc", str(tmp_path / "missing.dbc"), "--backend", "python-can",
                 "--interface", "virtual", "--channel", "test-only", "--duration", "0"]) == 1
    assert "DBC load failed" in capsys.readouterr().err
    factory.assert_not_called()
    assert main(["monitor", "--duration", "0"]) == 0


@pytest.mark.parametrize("command", ["encode", "decode"])
def test_dbc_path_is_required(command):
    with pytest.raises(SystemExit) as exc:
        main([command])
    assert exc.value.code == 2
