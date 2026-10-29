"""Windows Logging 실제 창 자동 smoke. Mock TEST ONLY 파일만 생성한다."""
import argparse
import csv
import json
from pathlib import Path
import sys
from unittest.mock import patch
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from pc_diagnostic.gui.window import MainWindow
from pc_diagnostic.gui.logging_session import LoggingState
from pc_diagnostic.interfaces import MockCanInterface
from pc_diagnostic.logger import RawCanLogger, read_jsonl
from gui_native_smoke import NATIVE_WAIT_MS, wait_until


def choose_path(view, path, format):
    # 자동 smoke는 사용자의 명시적 Dialog 선택 결과를 지정한 전용 경로로 모의한다.
    view.format_combo.setCurrentIndex(view.format_combo.findData(format))
    with patch("pc_diagnostic.gui.logging_view.QFileDialog.getSaveFileName", return_value=(str(path), "")):
        QTest.mouseClick(view.choose_button, Qt.MouseButton.LeftButton)
    assert view.path_edit.text() == str(path)


def main():
    # 기존 파일은 생성/삭제/덮어쓰지 않으며 호출자가 새 evidence 폴더를 제공한다.
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    root = Path(args.output_dir)
    assert root.is_dir()
    app = QApplication([])
    assert app.platformName() == "windows"
    transports = []
    class Tracked(MockCanInterface):
        def shutdown(self):
            # 실제 Mock 해제와 미송신을 기록한다.
            self.released += 1
            super().shutdown()
    def factory():
        # CAN 실행마다 새 transport를 생성한다.
        transport = Tracked()
        transport.released = 0
        transports.append(transport)
        return transport
    window = MainWindow(factory)
    view = window.logging_view
    accepted_frames = []
    accept = window.logging_session.accept
    def tracked_accept(frame):
        # Receiver에서 Session으로 전달된 동일 Raw 객체의 순서를 테스트에서만 기록한다.
        accepted = accept(frame)
        if accepted:
            accepted_frames.append(frame)
        return accepted
    window.logging_session.accept = tracked_accept
    results = []
    try:
        window.show()
        assert QTest.qWaitForWindowExposed(window, NATIVE_WAIT_MS)
        window.tabs.setCurrentWidget(view)
        assert view.state_label.text() == "Logging: Idle"
        window.start_monitor()
        wait_until(lambda: window.table.rowCount() > 0)
        assert window.logging_session.snapshot().state is LoggingState.IDLE
        for format in ("jsonl", "csv"):
            accepted_frames.clear()
            path = root / ("native." + format)
            choose_path(view, path, format)
            QTest.mouseClick(view.start_button, Qt.MouseButton.LeftButton)
            wait_until(lambda: window.logging_session.snapshot().written >= 4)
            assert not view.choose_button.isEnabled() and not view.format_combo.isEnabled()
            assert window.grab().save(str(root / ("logging-" + format + ".png")))
            QTest.mouseClick(view.stop_button, Qt.MouseButton.LeftButton)
            wait_until(lambda: not window.logging_session.snapshot().active)
            view.refresh()
            snap = window.logging_session.snapshot()
            assert snap.state is LoggingState.STOPPED and snap.closed and snap.written >= 4
            assert snap.queue_dropped == snap.unconfirmed == 0 and snap.received == snap.written
            baseline = root / ("cli-equivalent." + format)
            with RawCanLogger(baseline, format=format) as logger:
                for frame in accepted_frames:
                    logger.write(frame)
            assert path.read_bytes() == baseline.read_bytes()
            if format == "jsonl":
                assert list(read_jsonl(path)) == accepted_frames
            else:
                with path.open(encoding="utf-8", newline="") as stream:
                    rows = list(csv.DictReader(stream))
                assert len(rows) == snap.written
            results.append({"format": format, "written": snap.written, "cli_bytes_equal": True})
        before = (root / "native.csv").read_bytes()
        view.start_recording()
        wait_until(lambda: window.logging_session.snapshot().state is LoggingState.ERROR
                   and not window.logging_session.snapshot().active)
        view.refresh()
        assert "FileExistsError" in view.error_area.toPlainText()
        assert (root / "native.csv").read_bytes() == before
        accepted_frames.clear()
        close_path = root / "active-close.jsonl"
        choose_path(view, close_path, "jsonl")
        view.start_recording()
        wait_until(lambda: window.logging_session.snapshot().written >= 2)
        window.clear_monitor()
        assert window.logging_session.snapshot().state is LoggingState.RECORDING
        receiver, writer = window.worker, window.logging_session._thread
        assert window.close() and not receiver.isRunning() and not writer.is_alive()
        snap = window.logging_session.snapshot()
        assert snap.closed and snap.state is LoggingState.STOPPED
        assert list(read_jsonl(close_path)) == accepted_frames
        assert snap.written == snap.received == len(accepted_frames)
        assert all(t.released == 1 and not t.sent_frames for t in transports)
        print(json.dumps({"platform": app.platformName(), "window_exposed": True,
                          "logging_auto_start": False, "captures": results,
                          "existing_file_preserved": True, "error_restart": True,
                          "clear_keeps_recording": True, "active_close": True,
                          "writer_closed": snap.closed, "receiver_released": len(transports),
                          "human_manual": "NOT VERIFIED", "hardware": "NOT VERIFIED"}))
    finally:
        # 실패 시에도 file handle과 Receiver를 정상 종료한다.
        window.stop_monitor()
        if window.worker is not None:
            assert window.worker.wait(NATIVE_WAIT_MS)
        window.logging_session.stop()
        assert window.logging_session.wait(NATIVE_WAIT_MS / 1000)
        app.processEvents()
        window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
