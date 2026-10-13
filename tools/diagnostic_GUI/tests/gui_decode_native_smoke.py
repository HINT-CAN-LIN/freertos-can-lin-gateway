"""Phase 3C Windows 실제 창 자동 검증. 파일은 명시적 --dbc 입력이며 Hardware 시험이 아니다."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from pc_diagnostic.gui.demo import make_demo_frame
from pc_diagnostic.gui.window import MainWindow
from pc_diagnostic.interfaces import MockCanInterface
from gui_native_smoke import NATIVE_WAIT_MS, wait_until


def main():
    # 기존 native smoke와 별도로 실제 창에서 Decode/Cache 경계를 확인한다.
    parser = argparse.ArgumentParser()
    parser.add_argument("--dbc", required=True)
    parser.add_argument("--screenshot", required=True)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    app = QApplication([])
    assert app.platformName() == "windows"
    transports = []
    class TrackedMock(MockCanInterface):
        def shutdown(self):
            # 실제 해제 및 미송신을 기록한다.
            self.released = True
            super().shutdown()
    def factory():
        # 각 실행은 기존 Mock을 독립 생성한다.
        transport = TrackedMock()
        transport.released = False
        transports.append(transport)
        return transport
    window = MainWindow(factory)
    try:
        window.show()
        assert QTest.qWaitForWindowExposed(window, NATIVE_WAIT_MS)
        assert not window.decode_session.loader.is_loaded
        window.start_monitor()
        wait_until(lambda: window.table.rowCount() >= 2)
        window.table.selectRow(0)
        assert "Decode disabled" in window.selection_label.text()
        window.stop_monitor()
        wait_until(lambda: window.worker is None and window.buffer.pending_count == 0)
        # 자동 기본값이 아니라 테스트 호출자가 명시한 파일을 로드한다.
        assert Path(args.dbc).name == "test_only.dbc", "This smoke accepts TEST ONLY fixture only"
        assert window.load_dbc(args.dbc)
        window.clear_monitor()
        for cycle in range(3):
            before = window.buffer.total_received
            window.start_monitor()
            wait_until(lambda: window.buffer.total_received >= before + 2)
            wait_until(lambda: int(window.counter_label.text().split()[-1]) >= before + 2)
            window.table.selectRow(0)
            assert window.signal_table.rowCount() == 3
            assert window.cache_table.rowCount() == 3
            assert window.signal_table.item(0, 3).text() == "test_unit"
            assert "TestOnlySample" in window.selection_label.text()
            window.stop_monitor()
            wait_until(lambda: window.worker is None and window.buffer.pending_count == 0)
        assert window.grab().save(args.screenshot)
        good_stamp = window.decode_session.service.cache.last_timestamp("TestOnlySample", channel="DEMO/TEST ONLY")
        # 잘못된 길이를 codec에 그대로 전달하고 정상 Cache는 유지한다.
        bad = replace(make_demo_frame(0), data=b"\x01\x01", dlc=2)
        window.buffer.append(bad)
        window.refresh_frames()
        window.table.selectRow(window.table.rowCount() - 1)
        assert window.signal_table.rowCount() == 0 and window.cache_table.rowCount() == 3
        assert "Latest error:" in window.cache_label.text()
        assert window.decode_session.service.cache.last_timestamp("TestOnlySample", channel="DEMO/TEST ONLY") == good_stamp
        before = window.buffer.total_received
        window.start_monitor()
        wait_until(lambda: window.worker is not None and window.buffer.total_received > before)
        worker = window.worker
        assert window.close() and not worker.isRunning()
        assert window.worker is None and not window.age_timer.isActive()
        assert all(t.released and not t.sent_frames for t in transports)
        print(json.dumps({"platform": app.platformName(), "window_exposed": True,
                          "dbc": Path(args.dbc).name, "explicit_load_api": True,
                          "raw_without_dbc": True, "decode_and_cache": True,
                          "cycles": 3, "invalid_preserves_cache": True,
                          "active_close": True, "transports_released": len(transports),
                          "human_manual_file_dialog": "NOT VERIFIED", "hardware": "NOT VERIFIED"}))
    finally:
        # 실패한 검증에서도 활성 Worker를 정상 정리한다.
        window.stop_monitor()
        if window.worker is not None:
            assert window.worker.wait(NATIVE_WAIT_MS)
        app.processEvents()
        window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
