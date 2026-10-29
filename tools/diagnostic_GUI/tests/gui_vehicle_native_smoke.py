"""Vehicle Status Windows 창 자동 smoke. TEST ONLY 선택이며 사람 확인은 별도."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from pc_diagnostic.gui.demo import make_demo_frame
from pc_diagnostic.gui.vehicle_status import DISPLAY_ITEMS
from pc_diagnostic.gui.window import MainWindow
from pc_diagnostic.interfaces import MockCanInterface
from gui_native_smoke import NATIVE_WAIT_MS, wait_until

OBSERVATION_ITEM = "DBC Observation"
VALUE_COLUMN = 3
STATE_COLUMN = 7


def main():
    # 파일과 출처를 테스트 호출자가 명시한다. 자동 기본 연결은 없다.
    parser = argparse.ArgumentParser()
    parser.add_argument("--dbc", required=True)
    parser.add_argument("--screenshot", required=True)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    assert Path(args.dbc).name == "test_only.dbc"
    app = QApplication([])
    assert app.platformName() == "windows"
    transports = []
    class TrackedMock(MockCanInterface):
        def shutdown(self):
            # 정상 해제와 미송신을 기록한다.
            self.released = True
            super().shutdown()
    def factory():
        # Start마다 독립 Mock을 생성한다.
        transport = TrackedMock()
        transport.released = False
        transports.append(transport)
        return transport
    window = MainWindow(factory)
    view = window.vehicle_view
    row = DISPLAY_ITEMS.index(OBSERVATION_ITEM)
    def cell(column):
        # 실제 표시 셀을 읽는다.
        return view.table.item(row, column).text()
    def choose_mapping():
        # Message/Signal/Channel/확인을 직접 지정한다.
        view.item_combo.setCurrentText(OBSERVATION_ITEM)
        view.message_combo.setCurrentIndex(view.message_combo.findData("TestOnlySample"))
        view.channel_combo.setCurrentIndex(1)
        view.signal_combo.setCurrentText("Measurement")
        view.confirm_box.setChecked(True)
        QTest.mouseClick(view.apply_button, Qt.MouseButton.LeftButton)
    try:
        window.show()
        assert QTest.qWaitForWindowExposed(window, NATIVE_WAIT_MS)
        window.tabs.setCurrentWidget(view)
        assert cell(STATE_COLUMN) == "No DBC"
        assert window.load_dbc(args.dbc)
        assert cell(STATE_COLUMN) == "Ambiguous" and not view.model.mappings
        choose_mapping()
        assert cell(STATE_COLUMN) == "No Data"
        for cycle in range(3):
            before = window.buffer.total_received
            before_stamp = cell(5)
            window.start_monitor()
            wait_until(lambda: window.buffer.total_received > before and cell(STATE_COLUMN) == "Valid" and cell(5) != before_stamp)
            assert cell(VALUE_COLUMN) == "-10.0" and cell(4) == "test_unit"
            window.stop_monitor()
            wait_until(lambda: window.worker is None and window.buffer.pending_count == 0)
            assert transports[cycle].released and not transports[cycle].sent_frames
        before_age = cell(6)
        wait_until(lambda: cell(6) != before_age)
        assert window.grab().save(args.screenshot)
        stamp = cell(5)
        window.clear_monitor()
        assert window.table.rowCount() == 0 and cell(STATE_COLUMN) == "Valid" and cell(5) == stamp
        window.buffer.append(replace(make_demo_frame(0), data=bytes(3), dlc=3))
        window.refresh_frames()
        assert cell(STATE_COLUMN) == "Decode Error" and cell(VALUE_COLUMN) == "-10.0" and cell(5) == stamp
        assert window.load_dbc(args.dbc)
        assert cell(STATE_COLUMN) == "Ambiguous" and cell(VALUE_COLUMN) == "No Data"
        choose_mapping()
        assert cell(STATE_COLUMN) == "No Data"
        before = window.buffer.total_received
        window.start_monitor()
        wait_until(lambda: window.buffer.total_received > before and cell(STATE_COLUMN) == "Valid")
        worker = window.worker
        assert window.close() and not worker.isRunning()
        assert window.worker is None and not view.apply_button.isEnabled()
        assert all(t.released and not t.sent_frames for t in transports)
        print(json.dumps({"platform": app.platformName(), "window_exposed": True,
                          "tab": "Vehicle Status", "explicit_test_only_mapping": True,
                          "observed_signal": "TestOnlySample.Measurement", "value": -10.0,
                          "unit": "test_unit", "cycles": 3, "age_changes_stopped": True,
                          "clear_retains_cache": True, "decode_error_retains_value": True,
                          "reload_clears_mapping": True, "active_close": True,
                          "transports_released": len(transports), "human_manual": "NOT VERIFIED",
                          "physical_vehicle_measurement": "NOT VERIFIED", "hardware": "NOT VERIFIED"}))
    finally:
        # 실패 시에도 활성 Worker를 정상 정리한다.
        window.stop_monitor()
        if window.worker is not None:
            assert window.worker.wait(NATIVE_WAIT_MS)
        app.processEvents()
        window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
