"""Export 단위 시험. 기존 TEST ONLY/Repository DBC를 읽기 전용 사용한다."""
import csv
import json
from dataclasses import replace
from threading import Event
import pytest
from pc_diagnostic.gui.decode_session import DecodeSession
from pc_diagnostic.decoded_message import DecodedMessage, DecodeStatus
from pc_diagnostic.gui.demo import make_demo_frame
from pc_diagnostic.gui.monitor_history import ObservationHistory
from pc_diagnostic.gui.observation_export import (
    ExportSnapshot, ObservationExport, SnapshotFileWriter, decoded_snapshot, export_rows, fault_snapshot)
from test_fault_history import fault_session, fault_frame, configured, SOURCE, CHANNEL


def history_for(path):
    # 실제 기존 DecodeSession을 사용하며 Source는 관측 당시 고정한다.
    session = DecodeSession()
    session.load(path)
    history = ObservationHistory(500)
    return session, history


def observe(session, history, frame=None, source="Mock / TEST ONLY", mode="Mock"):
    # payload를 직접 해석하거나 Cache에서 값 복구를 하지 않는다.
    return history.record(session.process(frame or make_demo_frame(0)), source, mode)


@pytest.mark.parametrize("format", ["csv", "jsonl"])
def test_decoded_file_values_and_source(tmp_path, synthetic_dbc_path, format):
    # 인코딩/CSV 줄바꿈/JSONL 및 각 Signal의 원래 Raw metadata를 비교한다.
    session, history = history_for(synthetic_dbc_path)
    observe(session, history)
    path = tmp_path / ("관측." + format)
    snapshot = decoded_snapshot(history, session)
    writer = SnapshotFileWriter(path, format=format)
    writer.write(snapshot)
    writer.close()
    if format == "jsonl":
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    else:
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        assert b"\r\n" in path.read_bytes() and b"\r\r\n" not in path.read_bytes()
    row = next(r for r in rows if r["signal_name"] == "Measurement")
    assert float(row["decoded_value"]) == -10 and row["unit"] == "test_unit"
    assert row["source"] == "Mock / TEST ONLY" and row["source_mode"] == "Mock"
    assert row["message_name"] == "TestOnlySample" and row["decode_status"] == "decoded"
    assert float(row["timestamp"]) == history.records[0].observation.frame.timestamp
    assert int(row["arbitration_id"]) == make_demo_frame(0).arbitration_id
    assert len(rows) == snapshot.row_count == 3


@pytest.mark.parametrize("kind", ["invalid", "unknown", "missing-time", "reversed", "processing"])
def test_bad_or_missing_records_do_not_backfill(synthetic_dbc_path, kind):
    # 마지막 정상 Cache와 실패 프레임 Export를 혼합하지 않는다.
    session, history = history_for(synthetic_dbc_path)
    observe(session, history, replace(make_demo_frame(0), timestamp=10))
    frame = make_demo_frame(0)
    if kind == "invalid":
        frame = replace(frame, data=b"", dlc=0)
    elif kind == "unknown":
        # 새 CAN ID 없이 기존 Decode 결과 계약의 UNKNOWN 상태를 명시적으로 주입한다.
        result = DecodedMessage(frame, None, DecodeStatus.UNKNOWN)
        observation = replace(session.process(frame), decoded=result, message_name=None)
        history.record(observation, "Live / INJECTED TEST ONLY", "Live")
    elif kind == "missing-time":
        frame = replace(frame, timestamp=None)
    elif kind == "reversed":
        frame = replace(frame, timestamp=8)
    if kind not in ("unknown",):
        observation = session.process(frame)
        if kind == "processing":
            observation = replace(observation, processing_error="TEST ONLY processing failure")
        history.record(observation, "Live / INJECTED TEST ONLY", "Live")
    snapshot = decoded_snapshot(history, session)
    rows = list(export_rows(snapshot))
    latest = [r for r in rows if r["observation_sequence"] == 2]
    assert all(r["source"] == "Live / INJECTED TEST ONLY" for r in latest)
    if kind in ("invalid", "unknown", "processing"):
        assert len(latest) == 1 and latest[0]["decoded_value"] is None and latest[0]["signal_name"] is None
        if kind == "unknown":
            assert latest[0]["decode_status"] == "unknown"
    else:
        assert latest[0]["timestamp"] == (None if kind == "missing-time" else 8)
    assert len(rows) == snapshot.row_count


@pytest.mark.parametrize("channel", [None, 0, "0"])
def test_channel_type_and_format_not_merged(synthetic_dbc_path, channel):
    # Channel/ID/STD·EXT/동명 Signal을 개별 수신 식별자로 유지한다.
    session, history = history_for(synthetic_dbc_path)
    for i in (0, 1):
        observe(session, history, replace(make_demo_frame(i), channel=channel))
    rows = list(export_rows(decoded_snapshot(history, session)))
    assert {r["is_extended_id"] for r in rows} == {False, True}
    assert {r["channel_type"] for r in rows} == {type(channel).__name__}
    assert all(r["channel"] == channel for r in rows)


def test_no_dbc_empty_reload_and_tx_exclusion(synthetic_dbc_path):
    # No DBC/새 세션/미수신은 마지막 정상값이 존재한다는 뜻이 아니다.
    session = DecodeSession()
    history = ObservationHistory(500)
    with pytest.raises(ValueError, match="No DBC"):
        decoded_snapshot(history, session)
    session.load(synthetic_dbc_path)
    with pytest.raises(ValueError, match="No Data"):
        decoded_snapshot(history, session)
    observe(session, history, replace(make_demo_frame(0), is_rx=False))
    with pytest.raises(ValueError, match="No Data"):
        decoded_snapshot(history, session)
    observe(session, history)
    snapshot = decoded_snapshot(history, session)
    session.load(synthetic_dbc_path)
    with pytest.raises(ValueError, match="No Data"):
        decoded_snapshot(history, session)
    assert len(list(export_rows(snapshot))) == 3


def test_snapshot_stable_after_eviction_clear_and_reload(synthetic_dbc_path):
    # 고정 snapshot은 후속 수신/상한 제외/Source·DBC 변경에 따라 바뀌지 않는다.
    session, history = history_for(synthetic_dbc_path)
    observe(session, history)
    snapshot = decoded_snapshot(history, session)
    original = list(export_rows(snapshot))
    for _ in range(520):
        observe(session, history)
    assert len(history.records) == 500
    history.clear()
    session.reset_observations()
    assert list(export_rows(snapshot)) == original


@pytest.mark.parametrize("format", ["csv", "jsonl"])
def test_fault_fields_node_enum_and_unknown_preserved(tmp_path, fault_session, format):
    # 기존 DBC를 명시적으로 사용한 시험이다. FaultCode0을 Clear로 해석하지 않는다.
    model = configured(fault_session)
    frame = fault_frame(fault_session, code=0, node=1)
    model.record(fault_session.process(frame), fault_session, SOURCE)
    snapshot = fault_snapshot(model)
    rows = list(export_rows(snapshot))
    row = rows[0]
    assert row["signals"]["ECUOffline"] == 1 and row["dbc_choices"]["ECUOffline"] == "VCU"
    assert row["signals"]["FaultCode"] == 0 and row["fault_status"] == "Status Unknown"
    assert row["record_type"] == "fault_observation" and row["source"] == SOURCE
    assert row["signals"]["RecoveryState"] == 0 and row["dbc_choices"]["RecoveryState"] == "ACTIVE"
    assert row["timestamp"] == frame.timestamp and row["receiver_run"] == 1
    path = tmp_path / ("fault." + format)
    writer = SnapshotFileWriter(path, format=format)
    writer.write(snapshot);writer.close()
    if format == "csv":
        with path.open(encoding="utf-8", newline="") as stream:
            stored = next(csv.DictReader(stream))
        assert json.loads(stored["signals"]) == dict(model.entries[0].signals)
        assert json.loads(stored["dbc_choices"])["ECUOffline"] == "VCU"
    else:
        assert json.loads(path.read_text()) == row


def test_fault_empty_failure_and_test_only_fields(fault_session, synthetic_dbc_path):
    # Fault 이력에 없는 필드는 만들지 않는다. 실패 이력에 Cache를 붙이지 않는다.
    model = configured(fault_session)
    with pytest.raises(ValueError, match="No Data"):
        fault_snapshot(model)
    bad = replace(fault_frame(fault_session), data=b"", dlc=0, timestamp=None)
    model.record(fault_session.process(bad), fault_session, SOURCE)
    row = next(export_rows(fault_snapshot(model)))
    assert row["signals"] == {} and row["decode_status"] == "Decode Error"
    assert row["timestamp"] is None and row["fault_status"] == "Status Unknown"


@pytest.mark.parametrize("format", ["csv", "jsonl"])
def test_existing_file_never_overwritten(tmp_path, synthetic_dbc_path, format):
    # 확인 없이 기존 파일/빈 파일을 truncate하지 않는다.
    session, history = history_for(synthetic_dbc_path)
    observe(session, history)
    path = tmp_path / "existing"
    path.write_bytes(b"preserve")
    with pytest.raises(FileExistsError):
        SnapshotFileWriter(path, format=format)
    assert path.read_bytes() == b"preserve"


@pytest.mark.parametrize("phase", ["open", "write", "close"])
def test_export_session_errors_partial_and_cleanup(tmp_path, synthetic_dbc_path, phase):
    # 기존 LoggingSession 경로에서 실패를 주입한다. 실제 ACL/디스크 고갈 시험은 아니다.
    session, history = history_for(synthetic_dbc_path)
    observe(session, history)
    class FailingWriter:
        def __init__(self, *args, **kwargs):
            # 실제 환경을 손상시키지 않고 파일 오류를 모의한다.
            if phase == "open":
                raise PermissionError("TEST ONLY open")
        def write(self, snapshot):
            # 실패 snapshot을 성공 count로 계수하지 않는다.
            if phase == "write":
                raise OSError("TEST ONLY write")
        def close(self):
            # Close 실패도 성공으로 표시하지 않는다.
            if phase == "close":
                raise OSError("TEST ONLY close")
    exporter = ObservationExport(writer_factory=FailingWriter)
    exporter.start(decoded_snapshot(history, session), tmp_path / "capture")
    assert exporter.wait(2)
    result = exporter.writer.snapshot()
    assert result.error and result.state.value == "Error" and not result.active
    if phase != "close":
        assert result.written == 0
    assert result.queue_dropped == 0


def test_export_busy_snapshot_and_repeat(tmp_path, synthetic_dbc_path):
    # 파일 I/O가 막혀도 GUI snapshot/중복 요청은 writer lock으로 교착되지 않는다.
    session, history = history_for(synthetic_dbc_path)
    observe(session, history)
    entered, release = Event(), Event()
    class SlowWriter(SnapshotFileWriter):
        def write(self, snapshot):
            # 이벤트로 동기화하며 임의 sleep에 의존하지 않는다.
            entered.set()
            if not release.wait(3):
                raise TimeoutError("TEST ONLY release not signalled")
            super().write(snapshot)
    exporter = ObservationExport(writer_factory=SlowWriter)
    snapshot = decoded_snapshot(history, session)
    assert exporter.start(snapshot, tmp_path / "one")
    assert entered.wait(2)
    assert not exporter.start(snapshot, tmp_path / "other")
    assert not exporter.wait(0)
    release.set()
    assert exporter.wait(2) and exporter.writer.snapshot().closed
    assert exporter.start(snapshot, tmp_path / "two")
    assert exporter.wait(2) and exporter.writer.snapshot().written == 1


def test_partial_file_write_failure_is_not_success(tmp_path, synthetic_dbc_path):
    # 부분 파일을 삭제하지 않고 오류/미확인 count로 보존한다.
    session, history = history_for(synthetic_dbc_path);observe(session, history)
    path = tmp_path / "partial"
    class PartialWriter(SnapshotFileWriter):
        def write(self, snapshot):
            # 실제 파일에 일부만 쓴 후 오류를 모의한다.
            self.stream.write("{partial")
            self.stream.flush()
            raise OSError("TEST ONLY partial write")
    exporter = ObservationExport(writer_factory=PartialWriter)
    exporter.start(decoded_snapshot(history, session), path)
    assert exporter.wait(2)
    state = exporter.writer.snapshot()
    assert state.error and state.written == 0 and state.unconfirmed == 1
    assert path.read_text() == "{partial"


def test_empty_snapshot_invalid_format_and_missing_directory(tmp_path, synthetic_dbc_path):
    # 빈 데이터는 파일 생성 전에 거부한다.
    exporter = ObservationExport()
    with pytest.raises(ValueError, match="No Data"):
        exporter.start(ExportSnapshot("decoded", ()), tmp_path / "empty")
    assert not (tmp_path / "empty").exists()
    session, history = history_for(synthetic_dbc_path);observe(session, history)
    snapshot = decoded_snapshot(history, session)
    assert not exporter.start(snapshot, tmp_path / "bad", format="xml")
    assert not (tmp_path / "bad").exists()
    exporter.start(snapshot, tmp_path / "missing/capture")
    assert exporter.wait(2) and exporter.writer.snapshot().error
