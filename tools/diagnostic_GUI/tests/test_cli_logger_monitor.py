import csv
import json
from unittest.mock import Mock

import pytest

from pc_diagnostic import MockCanInterface, RawCanFrame, RawCanLogger
from pc_diagnostic.cli import main
from pc_diagnostic.logger import read_jsonl
from pc_diagnostic.monitor import capture, format_frame


@pytest.fixture
def fixture_file(tmp_path):
    path = tmp_path / "fixture.jsonl"
    with RawCanLogger(path) as logger:
        logger.write(RawCanFrame(0, b"\x00\xFF", timestamp=1.25, channel="test,channel"))
        logger.write(RawCanFrame(0x1FFFFFFF, is_extended_id=True, is_remote_frame=True, dlc=8))
    return path


def test_jsonl_roundtrip_and_overwrite_protection(fixture_file):
    frames = list(read_jsonl(fixture_file))
    assert frames[0].data == b"\x00\xFF"
    assert frames[0].timestamp == 1.25
    assert frames[1].is_remote_frame and frames[1].dlc == 8
    before = fixture_file.read_bytes()
    with pytest.raises(FileExistsError):
        RawCanLogger(fixture_file)
    assert fixture_file.read_bytes() == before


def test_csv_fields(tmp_path):
    path = tmp_path / "capture.csv"
    frame = RawCanFrame(0, b"\xFF", timestamp=0.5, channel="test,channel", is_rx=False)
    with RawCanLogger(path, format="csv") as logger:
        logger.write(frame)
    with path.open(newline="", encoding="utf-8") as stream:
        row, = list(csv.DictReader(stream))
    assert row["channel"] == frame.channel
    assert row["data"] == "FF" and row["dlc"] == "1"
    assert row["timestamp"] == "0.5" and row["is_rx"] == "False"


def test_bad_json_line(tmp_path):
    path = tmp_path / "bad.jsonl"
    path.write_text('{"arbitration_id": 0}\nnot json\n', encoding="utf-8")
    with pytest.raises(ValueError, match=":2:"):
        list(read_jsonl(path))


def test_monitor_and_logger_cli(fixture_file, tmp_path, capsys):
    assert main(["monitor", "--input", str(fixture_file)]) == 0
    output = capsys.readouterr()
    assert "STD 0x000 DATA DLC=2 00 FF" in output.out
    assert "EXT 0x1FFFFFFF RTR DLC=8" in output.out
    assert "Captured 2" in output.err
    dest = tmp_path / "capture.jsonl"
    assert main(["log", "--input", str(fixture_file), "--output", str(dest)]) == 0
    assert list(read_jsonl(dest)) == list(read_jsonl(fixture_file))
    assert main(["log", "--input", str(fixture_file), "--output", str(dest)]) == 1


def test_send_cli(capsys):
    assert main(["send", "--id", "0x7FF", "--data", "00 FF"]) == 0
    assert "MOCK RECORDED" in capsys.readouterr().out
    assert main(["send", "--id", "0x800"]) == 1
    assert main(["send", "--id", "0", "--data", "GG"]) == 1
    assert main(["send", "--id", "0", "--data", "FF", "--dlc", "8"]) == 1
    assert main(["send", "--id", "0", "--rtr"]) == 1
    assert main(["send", "--id", "0", "--rtr", "--dlc", "8"]) == 0


@pytest.mark.parametrize("args", [
    ["monitor", "--backend", "python-can"],
    ["send", "--id", "0", "--backend", "python-can", "--interface", "pcan", "--channel", "unused"],
    ["monitor", "--bitrate", "1"], ["monitor", "--count", "0"],
    ["monitor", "--duration", "nan"], ["monitor", "--duration", "-1"],
])
def test_invalid_cli_configuration(args):
    with pytest.raises(SystemExit) as exc:
        main(args)
    assert exc.value.code == 2


def test_empty_mock_is_bounded(fixture_file):
    assert main(["monitor"]) == 1
    assert main(["monitor", "--count", "1"]) == 1
    assert main(["monitor", "--duration", "0"]) == 0
    assert main(["monitor", "--input", str(fixture_file), "--count", "3"]) == 1


def test_capture_count_does_not_count_timeouts():
    interface = Mock()
    frames = [RawCanFrame(0), RawCanFrame(1)]
    interface.recv.side_effect = [None, frames[0], None, frames[1]]
    output = []
    assert capture(interface, output.append, count=2) == 2
    assert output == frames


def test_capture_deadline_with_idle_bus():
    with MockCanInterface() as interface:
        assert capture(interface, lambda _: pytest.fail("unexpected frame"), duration=0.01) == 0


def test_cli_cleanup_on_interrupt(monkeypatch, capsys):
    interface = Mock()
    interface.__enter__ = Mock(return_value=interface)
    interface.__exit__ = Mock(return_value=False)
    interface.recv.side_effect = KeyboardInterrupt
    monkeypatch.setattr("pc_diagnostic.cli.MockCanInterface", lambda *_: interface)
    assert main(["monitor", "--duration", "1"]) == 130
    interface.__exit__.assert_called_once()
    assert "Interrupted" in capsys.readouterr().err


def test_cli_validates_before_open(monkeypatch):
    factory = Mock()
    monkeypatch.setattr("pc_diagnostic.cli.PythonCanInterface", factory)
    assert main(["send", "--id", "0x800", "--backend", "python-can",
                 "--interface", "virtual", "--channel", "test"]) == 1
    factory.assert_not_called()


def test_write_error_is_not_reported_as_success(monkeypatch, fixture_file, tmp_path, capsys):
    def fail_write(*_):
        raise OSError("disk full")
    monkeypatch.setattr(RawCanLogger, "write", fail_write)
    assert main(["log", "--input", str(fixture_file), "--output", str(tmp_path / "new.jsonl")]) == 1
    output = capsys.readouterr()
    assert "disk full" in output.err and "Captured" not in output.err


def test_error_frame_display():
    assert "ERROR" in format_frame(RawCanFrame(0, is_error_frame=True))
