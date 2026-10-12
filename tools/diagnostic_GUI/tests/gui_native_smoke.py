"""Windows 실제 창 자동 smoke. 사람의 수동 확인 또는 Hardware 검증이 아니다."""
import argparse
import json
import sys
from time import monotonic

from PySide6 import __version__ as qt_python_version
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from pc_diagnostic.gui.window import MainWindow
from pc_diagnostic.interfaces import MockCanInterface

NATIVE_WAIT_MS = 3000
EVENT_STEP_MS = 10


def wait_until(predicate):
    # 실제 창의 Qt 이벤트를 처리하되 실패 시 유한 시간 안에 보고한다.
    deadline = monotonic() + NATIVE_WAIT_MS / 1000
    while not predicate() and monotonic() < deadline:
        QTest.qWait(EVENT_STEP_MS)
    assert predicate(), "native Windows GUI condition timed out"


def main():
    # 스크린샷은 Qt widget 자체를 렌더링한 검증 산출물이다.
    parser = argparse.ArgumentParser()
    parser.add_argument("--screenshot", required=True)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    app = QApplication([])
    assert app.platformName() == "windows", app.platformName()
    transports = []
    class TrackedMock(MockCanInterface):
        def shutdown(self):
            # native smoke에서도 실제 해제 여부와 송신 없음 증거를 남긴다.
            self.released = True
            super().shutdown()
    def factory():
        # 각 실행은 독립된 기존 Mock 인스턴스를 사용한다.
        transport = TrackedMock()
        transport.released = False
        transports.append(transport)
        return transport
    window = MainWindow(factory)
    try:
        window.show()
        assert QTest.qWaitForWindowExposed(window, NATIVE_WAIT_MS)
        assert window.isVisible() and int(window.winId()) != 0
        for cycle in range(3):
            before = window.buffer.total_received
            QTest.mouseClick(window.start_button, Qt.MouseButton.LeftButton)
            wait_until(lambda: window.buffer.total_received >= before + 4)
            wait_until(lambda: int(window.counter_label.text().split()[-1]) >= before + 4)
            if cycle == 0:
                assert window.grab().save(args.screenshot)
            QTest.mouseClick(window.stop_button, Qt.MouseButton.LeftButton)
            wait_until(lambda: window.worker is None)
            assert window.status_label.text() == "Stopped"
        received = window.buffer.total_received
        QTest.mouseClick(window.clear_button, Qt.MouseButton.LeftButton)
        assert window.table.rowCount() == 0 and window.counter_label.text() == "Received: 0"
        window.start_monitor()
        wait_until(lambda: window.table.rowCount() > 0)
        worker = window.worker
        assert window.close() and not worker.isRunning()
        assert all(t.released and not t.sent_frames for t in transports)
        print(json.dumps({"platform": app.platformName(), "PySide6": qt_python_version,
                          "window_exposed": True, "cycles": 3, "received_before_clear": received,
                          "clear": True, "active_close": True, "transports_released": len(transports),
                          "hardware": "NOT VERIFIED", "human_manual": "NOT VERIFIED"}))
    finally:
        # 실패한 smoke라도 활성 thread를 파괴하지 않고 정리한다.
        window.stop_monitor()
        if window.worker is not None:
            assert window.worker.wait(NATIVE_WAIT_MS)
        app.processEvents()
        window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
