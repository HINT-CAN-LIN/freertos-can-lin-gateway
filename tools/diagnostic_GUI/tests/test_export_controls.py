"""Export GUI·종료·오류 시험. 외부 CAN/실제 디스크 고갈 결과가 아니다."""
import json
from threading import Event, get_ident
import pytest
pytest.importorskip("PySide6", reason="install .[gui]")
from PySide6.QtWidgets import QFileDialog
from pc_diagnostic.gui.export_controls import ExportControls
from pc_diagnostic.gui.observation_export import ObservationExport, SnapshotFileWriter
from pc_diagnostic.gui.demo import make_demo_frame
from test_gui import qt_app, window_factory, wait_until
from test_fault_monitor_view import select_fault_source, feed


@pytest.mark.parametrize("kind", ["decoded", "fault"])
@pytest.mark.parametrize("format", ["jsonl", "csv"])
def test_gui_snapshot_export_and_activity(window_factory, synthetic_dbc_path, tmp_path, kind, format):
    # 기존 Source/DBC/per-frame 경로를 통과한 실제 snapshot을 내보낸다.
    window = window_factory();window.load_dbc(synthetic_dbc_path)
    select_fault_source(window)
    feed(window, make_demo_frame(0))
    window.set_raw_paused(True)
    feed(window, make_demo_frame(0))
    before = window.decode_session.service.cache.snapshot()
    path = tmp_path / (kind + "." + format)
    controls = window.export_controls
    assert controls.export_to(kind, path, format=format)
    wait_until(lambda: not controls.exporter.writer.snapshot().active)
    controls.refresh()
    assert controls.exporter.writer.snapshot().closed
    assert "Export completed" in window.error_area.toPlainText()
    assert window.activity_section.button.isChecked()
    assert window.decode_session.service.cache.snapshot() == before
    assert window.raw_paused and window.table.rowCount() == 1
    if format == "jsonl":
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        assert len(rows) == (6 if kind == "decoded" else 2)
        assert all(row["source"] == window._source_text for row in rows)


def test_no_data_or_dbc_does_not_create_file(window_factory, tmp_path, synthetic_dbc_path):
    # 빈 snapshot은 파일 dialog/파일 생성 전에 거부한다.
    window = window_factory();controls = window.export_controls
    assert not controls.export_to("decoded", tmp_path / "none")
    assert not controls.export_to("fault", tmp_path / "fault")
    assert not (tmp_path / "none").exists() and not (tmp_path / "fault").exists()
    window.load_dbc(synthetic_dbc_path)
    controls.refresh()
    assert not controls.widgets["decoded"][2].isEnabled()
    assert not controls.widgets["fault"][2].isEnabled()
    assert "No Data" in controls.widgets["decoded"][4].text()
    assert "Event store: Not Implemented" in controls.widgets["fault"][4].text()


def test_file_dialog_cancel_and_snapshot_before_nested_updates(window_factory, synthetic_dbc_path, tmp_path, monkeypatch):
    # 모달 선택 중 수신/Source 변경이 고정된 이전 snapshot의 Source를 바꾸지 않는다.
    window = window_factory();window.load_dbc(synthetic_dbc_path)
    feed(window, make_demo_frame(0))
    controls = window.export_controls
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: ("", ""))
    controls.choose("decoded")
    assert not controls.exporter.writer.snapshot().generation
    path = tmp_path / "snapshot.jsonl"
    def dialog(*args, **kwargs):
        # Qt nested loop의 수신 진행을 모의한다. dialog 전 snapshot만 저장돼야 한다.
        feed(window, make_demo_frame(0))
        window.connection_view.mode_combo.setCurrentText("Live")
        return str(path), ""
    monkeypatch.setattr(QFileDialog, "getSaveFileName", dialog)
    controls.choose("decoded")
    wait_until(lambda: not controls.exporter.writer.snapshot().active)
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(rows) == 3 and all(row["source_mode"] == "Mock" for row in rows)
    assert not window.raw_history.records and window.connection_view.mode_combo.currentText() == "Live"
    assert not window.driver_control_view.live_tx_button.isEnabled()


def test_export_failure_does_not_stop_rx_logging_or_mark_can_error(window_factory, tmp_path, synthetic_dbc_path):
    # Export Error는 CAN Receiver Error와 별개이며 기존 Logging을 중단하지 않는다.
    window = window_factory();window.load_dbc(synthetic_dbc_path)
    window.start_monitor();wait_until(lambda: window.table.rowCount() >= 2)
    path = tmp_path / "raw.jsonl"
    window.logging_view.set_output_path(path);window.logging_view.start_recording()
    wait_until(lambda: window.logging_session.snapshot().written >= 1)
    existing = tmp_path / "protected";existing.write_bytes(b"original")
    window.export_controls.export_to("decoded", existing)
    wait_until(lambda: not window.export_controls.exporter.writer.snapshot().active)
    window.export_controls.refresh()
    before = window.buffer.total_received
    wait_until(lambda: window.buffer.total_received > before)
    assert window.receiver_running() and window.status_label.text() == "Running"
    assert window.logging_session.snapshot().state.value == "Recording"
    assert "Export Error" in window.error_area.toPlainText()
    assert existing.read_bytes() == b"original"
    assert not window.close()  # Export 오류 첫 Close는 원인을 표시하고 창을 유지한다.
    assert window.isVisible()
    assert window.close()


def test_slow_export_main_thread_progress_and_close_retry(window_factory, synthetic_dbc_path, tmp_path):
    # 기존 Writer를 재사용하며 느린 I/O 중 GUI/수신 처리와 종료 재시도를 검증한다.
    window = window_factory();window.load_dbc(synthetic_dbc_path)
    feed(window, make_demo_frame(0))
    controls = window.export_controls
    entered, release = Event(), Event()
    gui_thread = get_ident()
    class SlowWriter(SnapshotFileWriter):
        def write(self, snapshot):
            # 파일 작업이 GUI main thread가 아님을 확인한다.
            assert get_ident() != gui_thread
            entered.set()
            if not release.wait(5):
                raise TimeoutError("TEST ONLY release missing")
            super().write(snapshot)
    controls.exporter = ObservationExport(writer_factory=SlowWriter)
    assert controls.export_to("decoded", tmp_path / "slow.jsonl")
    assert entered.wait(2)
    try:
        feed(window, make_demo_frame(0), make_demo_frame(1))
        assert window.counter_label.text() == "Received: 3"
        assert not controls.export_to("decoded", tmp_path / "duplicate")
        assert not window.close() and window.isVisible()
        assert "Export stop timed out" in window.error_area.toPlainText()
    finally:
        release.set()
    assert controls.exporter.wait(2)
    assert window.close()
    assert not window.age_timer.isActive() and not window.graph_view.timer.isActive()


@pytest.mark.parametrize("phase", ["write", "close"])
def test_export_error_on_close_visible_and_second_close_succeeds(window_factory, synthetic_dbc_path, tmp_path, phase):
    # 종료 중 Write/Close 실패는 첫 종료에서 표시하고 재시도 후 자원을 해제한다.
    window = window_factory();window.load_dbc(synthetic_dbc_path)
    feed(window, make_demo_frame(0))
    entered, release = Event(), Event()
    class FailingWriter(SnapshotFileWriter):
        def write(self, snapshot):
            # 먼저 Writer 진입을 알린 뒤 release 시점에만 실패를 발생시킨다.
            entered.set()
            if not release.wait(4):
                raise TimeoutError("TEST ONLY")
            if phase == "write":
                raise OSError("TEST ONLY drain write")
            super().write(snapshot)
        def close(self):
            # 실제 handle은 해제한 뒤 Close 오류를 모의한다.
            super().close()
            if phase == "close":
                raise OSError("TEST ONLY close")
    window.export_controls.exporter = ObservationExport(writer_factory=FailingWriter)
    window.export_controls.export_to("decoded", tmp_path / "error")
    assert entered.wait(2)
    release.set()
    assert not window.close()
    assert window.isVisible() and "Export ended with error" in window.error_area.toPlainText()
    assert not window.export_controls.exporter.writer.snapshot().active
    assert window.close()


def test_close_during_save_dialog_is_deferred(window_factory, synthetic_dbc_path, monkeypatch):
    # nested dialog가 열려 있을 때 창을 파괴하지 않는다.
    window = window_factory();window.load_dbc(synthetic_dbc_path)
    feed(window, make_demo_frame(0))
    def dialog(*args, **kwargs):
        # 부모 Close 요청은 명시적으로 보류되고 취소 후 정상 종료 가능해야 한다.
        assert not window.close() and window.isVisible()
        return "", ""
    monkeypatch.setattr(QFileDialog, "getSaveFileName", dialog)
    window.export_controls.choose("decoded")
    assert not window.export_controls.selecting and window.close()
