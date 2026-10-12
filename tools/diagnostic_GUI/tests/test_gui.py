"""Mock 전용 Qt 자동화. CANable/실제 ECU 검증이 아니다."""
import os
import subprocess
import sys
from threading import Event
from time import monotonic

import pytest

pytest.importorskip("PySide6", reason="install .[gui] for GUI tests")
from shiboken6 import isValid
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from pc_diagnostic.frame import RawCanFrame
from pc_diagnostic.interfaces import CanInterfaceError, MockCanInterface
from pc_diagnostic.gui.window import MainWindow, MAX_TABLE_ROWS, frame_cells

TEST_WAIT_SECONDS = 3
TEST_EVENT_STEP_MS = 10


def wait_until(predicate):
    # 테스트도 무한 대기하지 않으며 Qt 메인 스레드의 이벤트를 처리한다.
    deadline = monotonic() + TEST_WAIT_SECONDS
    while not predicate() and monotonic() < deadline:
        QTest.qWait(TEST_EVENT_STEP_MS)
    assert predicate(), "Qt condition timed out"


@pytest.fixture(scope="module")
def qt_app():
    # GUI 자동화는 offscreen이며 Windows 실제 창 검증과 별도로 기록한다.
    previous = os.environ.get("QT_QPA_PLATFORM")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    yield app
    app.processEvents()
    if previous is None:
        os.environ.pop("QT_QPA_PLATFORM", None)


@pytest.fixture
def window_factory(qt_app):
    # 실패한 assertion에도 활성 worker를 정리하여 다음 테스트를 보호한다.
    windows = []
    def create(factory=MockCanInterface):
        # 각 테스트에 독립 Mock transport를 제공한다.
        window = MainWindow(factory)
        windows.append(window)
        window.show()
        return window
    yield create
    for window in windows:
        window.stop_monitor()
        if window.worker is not None:
            assert window.worker.wait(1000)
        qt_app.processEvents()
        window.close()
        window.deleteLater()
    qt_app.processEvents()


def test_start_stop_repeat_and_no_duplicate_worker(window_factory):
    # offscreen에서는 실행마다 새 수신/transport 생성을 검증한다. native smoke는 실제 창 검증이다.
    transports = []
    class TrackedMock(MockCanInterface):
        def shutdown(self):
            # 각 실행의 정상 해제 횟수를 독립적으로 기록한다.
            self.shutdown_calls += 1
            super().shutdown()
    def transport_factory():
        # 매 Start에 별도 transport가 생성되어야 한다.
        transport = TrackedMock()
        transport.shutdown_calls = 0
        transports.append(transport)
        return transport
    window = window_factory(transport_factory)
    assert window.status_label.text() == "Disconnected"
    for cycle in range(3):
        previous_received = int(window.counter_label.text().split()[-1])
        QTest.mouseClick(window.start_button, Qt.MouseButton.LeftButton)
        worker = window.worker
        window.start_monitor()
        assert window.worker is worker and not window.start_button.isEnabled()
        # 이전 행이 남아 있어도 이번 실행의 수신 카운터가 증가할 때까지 이벤트를 처리한다.
        wait_until(lambda: int(window.counter_label.text().split()[-1]) > previous_received)
        assert len(transports) == cycle + 1
        assert window.status_label.text() == "Running"
        QTest.mouseClick(window.stop_button, Qt.MouseButton.LeftButton)
        wait_until(lambda: window.worker is None)
        assert not isValid(worker) or not worker.isRunning()
        assert transports[cycle].shutdown_calls == 1
        assert transports[cycle].sent_frames == ()
        assert window.status_label.text() == "Stopped"
        assert window.start_button.isEnabled() and not window.stop_button.isEnabled()
    assert len({id(transport) for transport in transports}) == 3


def test_actual_raw_cells_counter_and_clear(window_factory):
    # 수신된 raw 속성을 표시하며 Clear는 수신 자체를 중지하지 않는다.
    window = window_factory()
    window.start_monitor()
    wait_until(lambda: window.table.rowCount() >= 2)
    window.stop_monitor()
    wait_until(lambda: window.worker is None)
    assert window.table.item(0, 1).text() == "DEMO/TEST ONLY"
    assert window.table.item(0, 2).text() == "0x651 (STD)"
    assert window.table.item(0, 3).text() == "4"
    assert window.table.item(0, 4).text() == "28 00 01 07"
    assert window.table.item(1, 2).text() == "0x00000651 (EXT)"
    assert window.table.item(1, 4).text() == "01 01"
    assert int(window.counter_label.text().split()[-1]) >= 2
    QTest.mouseClick(window.clear_button, Qt.MouseButton.LeftButton)
    assert window.table.rowCount() == 0 and window.counter_label.text() == "Received: 0"
    window.start_monitor()
    wait_until(lambda: window.table.rowCount() > 0)
    window.clear_monitor()
    assert window.status_label.text() == "Running"
    wait_until(lambda: window.table.rowCount() > 0)


@pytest.mark.parametrize("frame,expected", [
    (RawCanFrame(1617, is_remote_frame=True, dlc=4, channel=0), "0x651 (STD RTR)"),
    (RawCanFrame(1617, is_error_frame=True), "0x00000651 (ERROR)"),
])
def test_frame_flags_and_missing_metadata_are_preserved(frame, expected):
    # RTR/오류 ID와 DLC는 프레임 값 그대로 유지한다.
    cells = frame_cells(frame)
    assert cells[0] == "unknown" and cells[2] == expected
    assert cells[1] == ("0" if frame.channel == 0 else "unknown")
    assert cells[3] == str(frame.dlc) and cells[4] == ""


def test_close_stops_active_worker_and_shuts_down_mock(window_factory):
    # 창 종료는 thread 종료와 transport 해제를 함께 확인한다.
    transports = []
    class TrackedMock(MockCanInterface):
        def shutdown(self):
            # 테스트 전용 해제 증거를 기록한다.
            self.released = True
            super().shutdown()
    def factory():
        # worker가 실제로 소유한 transport를 검증한다.
        transport = TrackedMock()
        transport.released = False
        transports.append(transport)
        return transport
    window = window_factory(factory)
    window.start_monitor()
    worker = window.worker
    wait_until(lambda: window.table.rowCount() > 0)
    assert window.close()
    assert not worker.isRunning() and transports[0].released
    assert transports[0].sent_frames == ()


def test_stop_immediately_after_start(window_factory):
    # transport 생성 전 정지도 취소 이벤트를 잃지 않는다.
    window = window_factory()
    window.start_monitor()
    window.stop_monitor()
    wait_until(lambda: window.worker is None)
    assert window.status_label.text() == "Stopped"


@pytest.mark.parametrize("failure", ["receive", "shutdown", "factory"])
def test_worker_exception_is_visible_and_recoverable(window_factory, failure):
    # 생성/수신/해제 실패를 각각 Error로 보여주고 정상 Mock 재시작을 허용한다.
    class BrokenMock(MockCanInterface):
        def recv(self, timeout=None):
            # 수신 장애는 숨기지 않고 원인을 전달한다.
            if failure == "receive":
                raise CanInterfaceError("test receive failure")
            return super().recv(timeout)
        def shutdown(self):
            # 해제 자체의 실패도 UI 오류에 포함한다.
            super().shutdown()
            if failure == "shutdown":
                raise CanInterfaceError("test shutdown failure")
    def factory():
        # open 장애를 테스트한다.
        if failure == "factory":
            raise CanInterfaceError("test factory failure")
        return BrokenMock()
    window = window_factory(factory)
    window.start_monitor()
    if failure == "shutdown":
        wait_until(lambda: window.table.rowCount() > 0)
        window.stop_monitor()
    wait_until(lambda: window.worker is None)
    assert window.status_label.text() == "Error"
    assert f"test {failure} failure" in window.error_area.toPlainText()
    window._interface_factory = MockCanInterface
    window.start_monitor()
    wait_until(lambda: window.table.rowCount() > 0)
    assert window.status_label.text() == "Running"


def test_close_timeout_keeps_window_and_worker_alive(window_factory, monkeypatch):
    # 취소 불응 시 강제 terminate 대신 창을 유지하고 오류를 표시한다.
    from pc_diagnostic.gui import window as window_module
    entered, release = Event(), Event()
    class SlowMock(MockCanInterface):
        def recv(self, timeout=None):
            # 테스트에서만 recv 계약 위반을 주입하고 유한 시간 안에 해제한다.
            entered.set()
            release.wait(TEST_WAIT_SECONDS)
            return super().recv(timeout)
    window = window_factory(SlowMock)
    original_close_wait_ms = window_module.CLOSE_WAIT_MS
    monkeypatch.setattr(window_module, "CLOSE_WAIT_MS", 1)
    window.start_monitor()
    wait_until(entered.is_set)
    try:
        assert not window.close()
        assert window.isVisible() and window.worker.isRunning()
        assert window.status_label.text() == "Error"
        assert "timed out" in window.error_area.toPlainText()
    finally:
        # close timeout 검증 뒤에는 정상 thread 정리 대기를 복원해 1ms 테스트 설정의 영향을 제한한다.
        monkeypatch.setattr(window_module, "CLOSE_WAIT_MS", original_close_wait_ms)
        release.set()
    wait_until(lambda: window.worker is None)
    assert window.close()


def test_display_rows_and_batches_are_bounded(window_factory):
    # 고속 입력에서 buffer 제외와 최대 표시 행 수를 구분한다.
    from pc_diagnostic.gui.demo import make_demo_frame
    window = window_factory()
    for i in range(MAX_TABLE_ROWS * 4):
        window.buffer.append(make_demo_frame(i))
    for _ in range(6):
        window.refresh_frames()
    assert window.table.rowCount() == MAX_TABLE_ROWS
    assert window.counter_label.text() == "Received: 2000"
    assert window.drop_label.text() == "표시 버퍼 제외: 1488"


def test_cli_runs_while_gui_worker_is_active(window_factory):
    # GUI 작업 중 기존 CLI monitor를 별도 process에서 실행한다.
    window = window_factory()
    window.start_monitor()
    wait_until(lambda: window.table.rowCount() > 0)
    result = subprocess.run([sys.executable, "-m", "pc_diagnostic", "monitor",
                             "--backend", "mock", "--count", "1", "--duration", "0.1"],
                            capture_output=True, text=True, timeout=TEST_WAIT_SECONDS)
    assert result.returncode == 0, result.stderr
    assert window.worker is not None and window.worker.isRunning()


def test_gui_entry_help_and_cli_import_do_not_require_qt():
    # 선택적 GUI 의존성을 차단해도 기존 CLI import/도움말은 유지한다.
    script = """import sys, importlib.abc
class NoQt(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith('PySide6'):
            raise ImportError('test optional dependency unavailable')
sys.meta_path.insert(0, NoQt())
import pc_diagnostic.cli
from pc_diagnostic.gui.app import main
assert main([]) == 1
"""
    result = subprocess.run([sys.executable, "-c", script], capture_output=True,
                            text=True, timeout=TEST_WAIT_SECONDS)
    assert result.returncode == 0 and "Install with" in result.stderr
    help_result = subprocess.run([sys.executable, "-m", "pc_diagnostic.gui", "--help"],
                                 capture_output=True, text=True, timeout=TEST_WAIT_SECONDS)
    assert help_result.returncode == 0 and "Mock / DEMO ONLY" in help_result.stdout
