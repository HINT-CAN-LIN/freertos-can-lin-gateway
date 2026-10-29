"""Mock Qt Logging 연결/오류/리소스 검증. 기존 화면과 테스트는 보존한다."""
import csv
from dataclasses import replace
from threading import Event
import pytest
pytest.importorskip("PySide6", reason="install .[gui]")
from PySide6.QtCore import Qt, QThread
from PySide6.QtTest import QTest
from pc_diagnostic.gui.demo import make_demo_frame
from pc_diagnostic.gui.logging_session import LoggingSession, LoggingState
from pc_diagnostic.gui.buffer import FrameBuffer
from pc_diagnostic.logger import RawCanLogger, read_jsonl
from test_gui import qt_app, window_factory, wait_until
from test_vehicle_view import select_mapping as select_vehicle, cell as vehicle_cell
from test_ecu_observation_view import select_source as select_ecu, state as ecu_state


def wait_stopped(window):
    # writer 종료와 마지막 UI snapshot 갱신을 모두 기다린다.
    wait_until(lambda: not window.logging_session.snapshot().active)
    window.logging_view.refresh()


def begin(window, path, format="jsonl"):
    # 명시적 파일과 형식 설정은 Receiver Start와 별도이다.
    view = window.logging_view
    assert view.set_output_path(path)
    view.format_combo.setCurrentIndex(view.format_combo.findData(format))
    window.start_monitor()
    QTest.mouseClick(view.start_button, Qt.MouseButton.LeftButton)
    wait_until(lambda: window.logging_session.snapshot().written >= 2)
    return view


def test_logging_idle_no_auto_start_and_requires_receiver(window_factory, tmp_path):
    # GUI/CAN 시작만으로 파일이 생성되지 않는다.
    window = window_factory()
    view = window.logging_view
    assert window.tabs.tabText(3) == "Logging" and view.state_label.text() == "Logging: Idle"
    assert not view.start_button.isEnabled() and not view.stop_button.isEnabled()
    path = tmp_path / "explicit.jsonl"
    assert view.set_output_path(path)
    view.start_recording()
    assert "Start CAN Receiver first" in view.error_area.toPlainText()
    assert not path.exists()
    window.start_monitor()
    wait_until(lambda: window.table.rowCount() > 0)
    assert window.logging_session.snapshot().state is LoggingState.IDLE and not path.exists()


@pytest.mark.parametrize("format", ["jsonl", "csv"])
def test_file_choice_content_and_independent_logging_stop(window_factory, tmp_path, monkeypatch, format):
    # Qt 파일 선택을 모의하며 Logger 출력은 실제 임시 파일로 검증한다.
    window = window_factory()
    view = window.logging_view
    path = tmp_path / ("selected." + format)
    view.format_combo.setCurrentIndex(view.format_combo.findData(format))
    monkeypatch.setattr("pc_diagnostic.gui.logging_view.QFileDialog.getSaveFileName", lambda *args, **kwargs: (str(path), ""))
    QTest.mouseClick(view.choose_button, Qt.MouseButton.LeftButton)
    assert view.path_edit.text() == str(path) and view.path_edit.isReadOnly()
    window.start_monitor()
    QTest.mouseClick(view.start_button, Qt.MouseButton.LeftButton)
    wait_until(lambda: window.logging_session.snapshot().written >= 3)
    assert not view.choose_button.isEnabled() and not view.format_combo.isEnabled()
    old_path = view.path_edit.text()
    view.choose_file()
    assert not view.set_output_path(tmp_path / "forbidden.jsonl") and view.path_edit.text() == old_path
    thread = window.logging_session._thread
    view.start_recording()
    assert window.logging_session._thread is thread
    QTest.mouseClick(view.stop_button, Qt.MouseButton.LeftButton)
    view.stop_recording()
    wait_stopped(window)
    snap = window.logging_session.snapshot()
    assert snap.state is LoggingState.STOPPED and snap.closed
    assert window.worker is not None and window.status_label.text() == "Running"
    before = window.buffer.total_received
    wait_until(lambda: window.buffer.total_received > before)
    assert window.logging_session.snapshot().written == snap.written
    if format == "jsonl":
        frames = list(read_jsonl(path))
        assert len(frames) == snap.written
        assert all(frame.channel == "DEMO/TEST ONLY" and frame.is_rx for frame in frames)
        assert {frame.is_extended_id for frame in frames} == {False, True}
    else:
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        assert len(rows) == snap.written and {row["is_extended_id"] for row in rows} == {"False", "True"}


def test_dialog_cancel_missing_path_and_existing_file_safety(window_factory, tmp_path, monkeypatch):
    # 취소/경로 미선택/기존 파일에서 자동 저장/덮어쓰기를 하지 않는다.
    window = window_factory()
    view = window.logging_view
    monkeypatch.setattr("pc_diagnostic.gui.logging_view.QFileDialog.getSaveFileName", lambda *args, **kwargs: ("", ""))
    view.choose_file()
    assert not view.path_edit.text()
    window.start_monitor()
    view.start_recording()
    assert window.logging_session.snapshot().state is LoggingState.ERROR
    assert "Select an explicit" in view.error_area.toPlainText()
    path = tmp_path / "keep.jsonl"
    path.write_bytes(b"preserve TEST ONLY file")
    view.set_output_path(path)
    view.start_recording()
    wait_until(lambda: window.logging_session.snapshot().state is LoggingState.ERROR and not window.logging_session.snapshot().active)
    view.refresh()
    assert "FileExistsError" in view.error_area.toPlainText() and path.read_bytes() == b"preserve TEST ONLY file"
    assert window.status_label.text() == "Running"
    view.set_output_path(tmp_path / "new.jsonl")
    view.start_recording()
    wait_until(lambda: window.logging_session.snapshot().written >= 1)
    view.stop_recording()
    wait_stopped(window)
    assert window.logging_session.snapshot().state is LoggingState.STOPPED


def test_receiver_stop_drain_and_repeated_sessions(window_factory, tmp_path):
    # CAN Stop은 logging을 자동 seal/drain하되 Start CAN은 다음 기록을 자동 활성화하지 않는다.
    window = window_factory()
    for cycle in range(3):
        path = tmp_path / f"cycle-{cycle}.jsonl"
        begin(window, path)
        window.stop_monitor()
        wait_until(lambda: window.worker is None)
        wait_stopped(window)
        snap = window.logging_session.snapshot()
        assert snap.closed and snap.state is LoggingState.STOPPED and snap.written >= 2
        assert len(list(read_jsonl(path))) == snap.written
        assert snap.received == snap.written + snap.queue_dropped + snap.unconfirmed
    window.start_monitor()
    wait_until(lambda: window.table.rowCount() > 0)
    assert window.logging_session.snapshot().state is LoggingState.STOPPED


def test_display_buffer_drop_does_not_drop_logging_and_clear_preserves_log(window_factory, tmp_path):
    # 실제 Receiver fan-out에서 표시 Buffer 상한만 줄이고 파일 Queue를 독립적으로 검증한다.
    window = window_factory()
    window.buffer = FrameBuffer(capacity=1)
    window.timer.setInterval(1000)
    path = tmp_path / "independent.jsonl"
    view = begin(window, path)
    wait_until(lambda: window.buffer.dropped >= 2)
    before = window.logging_session.snapshot()
    assert before.queue_dropped == 0 and before.written >= 2
    window.clear_monitor()
    after = window.logging_session.snapshot()
    assert after.state is LoggingState.RECORDING and after.received >= before.received
    window.stop_monitor()
    wait_until(lambda: window.worker is None)
    wait_stopped(window)
    snap = window.logging_session.snapshot()
    assert snap.written == snap.received and snap.queue_dropped == snap.unconfirmed == 0
    assert len(list(read_jsonl(path))) == snap.written
    assert "Logging Start" in view.scope_label.text() and "표시 Drop과 파일 Queue Drop은 독립" in view.scope_label.text()


def test_write_error_gui_keeps_can_and_decode_running(window_factory, synthetic_dbc_path, tmp_path, monkeypatch):
    # 기록 오류는 CAN/Decode/Vehicle/ECU를 중지시키지 않는다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    select_vehicle(window.vehicle_view)
    select_ecu(window.ecu_view)
    def fail_write(self, frame):
        # 실제 PySide/Logger 설치는 유지하고 파일 쓰기 실패만 모의한다.
        raise OSError("TEST ONLY disk full")
    with monkeypatch.context() as patch:
        patch.setattr(RawCanLogger, "write", fail_write)
        view = window.logging_view
        view.set_output_path(tmp_path / "partial.jsonl")
        window.start_monitor()
        view.start_recording()
        wait_until(lambda: window.logging_session.snapshot().state is LoggingState.ERROR)
        wait_stopped(window)
    snap = window.logging_session.snapshot()
    assert snap.written == 0 and snap.unconfirmed >= 1 and snap.closed
    assert "disk full" in view.error_area.toPlainText() and "INCOMPLETE" in view.warning_label.text()
    assert window.status_label.text() == "Running" and not window._failed
    wait_until(lambda: vehicle_cell(window.vehicle_view, 7) == "Valid" and ecu_state(window.ecu_view) == "State: Observed")
    view.set_output_path(tmp_path / "recovered.csv")
    view.format_combo.setCurrentIndex(view.format_combo.findData("csv"))
    view.start_recording()
    wait_until(lambda: window.logging_session.snapshot().written >= 2)
    view.stop_recording()
    wait_stopped(window)
    assert window.logging_session.snapshot().state is LoggingState.STOPPED


def test_missing_parent_error_and_normal_close(window_factory, tmp_path):
    # 상위 폴더가 없으면 Error를 표시하며 GUI 종료는 안전하다.
    window = window_factory()
    window.logging_view.set_output_path(tmp_path / "missing" / "out.csv")
    window.start_monitor()
    window.logging_view.start_recording()
    wait_until(lambda: window.logging_session.snapshot().state is LoggingState.ERROR)
    wait_stopped(window)
    assert "FileNotFoundError" in window.logging_view.error_area.toPlainText()
    assert not window.close() and window.isVisible()
    assert window.close() and not window.logging_session.snapshot().active


def test_active_close_releases_both_workers_and_ui_main_thread(window_factory, tmp_path, qt_app, monkeypatch):
    # writer/Receiver를 모두 종료하고 종료 후 UI 갱신을 차단한다.
    window = window_factory()
    view = begin(window, tmp_path / "active-close.jsonl")
    original = view.refresh
    def checked_refresh():
        # writer에서 Logging UI에 직접 접근하면 실패한다.
        assert QThread.currentThread() == qt_app.thread()
        original()
    monkeypatch.setattr(view, "refresh", checked_refresh)
    receiver = window.worker
    writer = window.logging_session._thread
    assert window.close() and not receiver.isRunning() and not writer.is_alive()
    assert window.logging_session.snapshot().closed
    assert not view.timer.isActive() and not view.start_button.isEnabled()
    previous_path = view.path_edit.text()
    assert not view.set_output_path(tmp_path / "after-close.jsonl")
    view.start_recording()
    view.refresh()
    assert view.path_edit.text() == previous_path


def test_close_wait_timeout_keeps_window_until_writer_finishes(window_factory, tmp_path, monkeypatch):
    # Event로 파일 대기를 모의하며 강제 종료/파일 삭제를 하지 않는다.
    entered, release = Event(), Event()
    class Slow(RawCanLogger):
        def write(self, frame):
            # 테스트에서 release하는 유한 대기이다.
            entered.set()
            assert release.wait(3)
            super().write(frame)
    window = window_factory()
    session = LoggingSession(logger_factory=Slow)
    window.logging_session = window.logging_view.session = session
    window.logging_view.set_output_path(tmp_path / "slow.jsonl")
    window.start_monitor()
    window.logging_view.start_recording()
    wait_until(lambda: entered.is_set())
    with monkeypatch.context() as patch:
        patch.setattr(session, "wait", lambda timeout: False)
        try:
            assert not window.close() and window.isVisible()
            assert "Logging stop timed out" in window.error_area.toPlainText()
            assert session.snapshot().state is LoggingState.STOPPING and session.snapshot().active
        finally:
            release.set()
    wait_stopped(window)
    assert window.close() and session.snapshot().closed


def test_logging_queue_drop_warning_is_visible(window_factory, tmp_path):
    # 파일 Queue overflow를 표시 Drop과 독립적으로 보여준다.
    entered, release = Event(), Event()
    class Slow(RawCanLogger):
        def write(self, frame):
            # 파일I/O중 Receiver를 차단하지 않는다.
            entered.set()
            assert release.wait(3)
            super().write(frame)
    window = window_factory()
    session = LoggingSession(capacity=1, logger_factory=Slow)
    window.logging_session = window.logging_view.session = session
    view = window.logging_view
    view.set_output_path(tmp_path / "limited.jsonl")
    window.start_monitor()
    view.start_recording()
    wait_until(lambda: entered.is_set() and session.snapshot().queue_dropped > 0)
    try:
        view.refresh()
        assert "INCOMPLETE" in view.warning_label.text() and "Queue dropped:" in view.count_label.text()
        window.stop_monitor()
        wait_until(lambda: window.worker is None)
    finally:
        release.set()
    wait_stopped(window)
    snap = session.snapshot()
    assert snap.queue_dropped > 0 and snap.received == snap.written + snap.queue_dropped
    assert "INCOMPLETE" in view.warning_label.text()

def test_close_drain_error_is_visible_before_window_disappears(window_factory, tmp_path):
    # 종료 drain 중 파일 오류가 발생하면 첫 close는 오류를 볼 수 있도록 창을 유지해야 한다.
    entered = Event()
    session = None
    class FailsOnStop(RawCanLogger):
        def write(self, frame):
            # 임의 sleep 없이 실제 Stop 상태 전이에 맞춰 write 실패를 재현한다.
            entered.set()
            with session._condition:
                assert session._condition.wait_for(
                    lambda: session.snapshot().state is LoggingState.STOPPING, timeout=3)
            raise OSError("TEST ONLY close-drain write error")
    window = window_factory()
    session = LoggingSession(logger_factory=FailsOnStop)
    window.logging_session = window.logging_view.session = session
    window.logging_view.set_output_path(tmp_path / "close-drain.jsonl")
    window.start_monitor()
    window.logging_view.start_recording()
    wait_until(lambda: entered.is_set())
    receiver = window.worker
    assert not window.close()
    assert not receiver.isRunning() and not session.snapshot().active and session.snapshot().closed
    assert window.isVisible() and session.snapshot().state is LoggingState.ERROR
    assert "close-drain write error" in window.logging_view.error_area.toPlainText()
    assert "close again" in window.error_area.toPlainText()
    assert window.close() and not session.snapshot().active

def test_receiver_error_seals_logging_and_releases_writer(window_factory, tmp_path):
    # 실제 Receiver 예외 경로에서도 Logger는 pending을 drain하고 종료한다.
    from pc_diagnostic.interfaces import CanInterfaceError, MockCanInterface
    fail_receive = Event()
    transports = []
    class FailingReceiver(MockCanInterface):
        def recv(self, timeout=None):
            # 기존 recv 계약을 유지하며 명시적으로 모의 오류를 주입한다.
            if fail_receive.is_set():
                raise CanInterfaceError("TEST ONLY receiver failure")
            return super().recv(timeout)
        def shutdown(self):
            # transport 정상 해제 증거를 보존한다.
            self.released = True
            super().shutdown()
    def factory():
        # mock은 각 CAN Start마다 독립 생성한다.
        transport = FailingReceiver()
        transport.released = False
        transports.append(transport)
        return transport
    window = window_factory(factory)
    path = tmp_path / "receive-error.jsonl"
    begin(window, path)
    fail_receive.set()
    wait_until(lambda: window.worker is None)
    wait_stopped(window)
    snap = window.logging_session.snapshot()
    assert window.status_label.text() == "Error" and snap.state is LoggingState.STOPPED
    assert snap.closed and snap.written == snap.received and transports[0].released
    assert len(list(read_jsonl(path))) == snap.written


def test_receiver_stop_before_logging_click_does_not_start_file(window_factory, tmp_path):
    # Stop과 GUI Logging 클릭 경합은 main-thread guard로 차단한다.
    window = window_factory()
    path = tmp_path / "must-not-start.jsonl"
    view = window.logging_view
    view.set_output_path(path)
    window.start_monitor()
    window.stop_monitor()
    view.start_recording()
    assert window.logging_session.snapshot().state is LoggingState.IDLE and not path.exists()
    assert "Start CAN Receiver first" in view.error_area.toPlainText()
