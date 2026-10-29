"""Windows ECU/Statistics/Fault 실제 창 자동 검증. Mock / TEST ONLY 전용."""
import argparse
import json
from pathlib import Path
import sys
from dataclasses import replace
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from pc_diagnostic.gui.demo import make_demo_frame
from pc_diagnostic.gui.ecu_observation import ECU_NAMES
from pc_diagnostic.gui.observation_view import FAULT_TARGET
from pc_diagnostic.gui.window import MainWindow
from pc_diagnostic.interfaces import MockCanInterface
from gui_native_smoke import NATIVE_WAIT_MS, wait_until


def choose_source(view, target):
    # UI에서 Message/Channel/출처 확인을 명시적으로 선택한다.
    view.target_combo.setCurrentText(target)
    view.message_combo.setCurrentIndex(view.message_combo.findData("TestOnlySample"))
    view.channel_combo.setCurrentIndex(1)
    view.confirm_box.setChecked(True)
    QTest.mouseClick(view.apply_button, Qt.MouseButton.LeftButton)


def main():
    # 검증용 fixture와 screenshot 경로는 호출자가 지정한다.
    parser = argparse.ArgumentParser()
    parser.add_argument("--dbc", required=True)
    parser.add_argument("--screenshot-prefix", required=True)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    assert Path(args.dbc).name == "test_only.dbc"
    app = QApplication([])
    assert app.platformName() == "windows"
    transports = []
    class Tracked(MockCanInterface):
        def shutdown(self):
            # 실제 transport 해제와 미송신 증거를 남긴다.
            self.released += 1
            super().shutdown()
    def factory():
        # 매 실행 독립 Mock을 생성한다.
        transport = Tracked()
        transport.released = 0
        transports.append(transport)
        return transport
    window = MainWindow(factory)
    view = window.ecu_view
    try:
        window.show()
        assert QTest.qWaitForWindowExposed(window, NATIVE_WAIT_MS)
        window.tabs.setCurrentWidget(view)
        assert len(view.cards) == 7
        assert all(card["state"].text() == "State: Not Configured" for card in view.cards.values())
        assert window.load_dbc(args.dbc)
        choose_source(view, "VCU")
        choose_source(view, FAULT_TARGET)
        assert view.cards["VCU"]["state"].text() == "State: No Data"
        assert "No Data" in view.fault_label.text()
        for cycle in range(3):
            before = view.model.observe("VCU", window.decode_session, now=window._clock()).count
            window.start_monitor()
            worker = window.worker
            window.start_monitor()
            assert window.worker is worker
            wait_until(lambda: view.model.observe("VCU", window.decode_session, now=window._clock()).count >= before + 2)
            assert view.cards["VCU"]["state"].text() == "State: Observed"
            window.stop_monitor()
            wait_until(lambda: window.worker is None and window.buffer.pending_count == 0)
            assert transports[cycle].released == 1 and not transports[cycle].sent_frames
        before_time = view.cards["VCU"]["time"].text()
        wait_until(lambda: view.cards["VCU"]["time"].text() != before_time)
        assert view.statistics_table.rowCount() == 2
        assert {view.statistics_table.item(row, 2).text() for row in range(2)} == {"STD", "EXT"}
        assert view.fault_table.rowCount() == 3
        for index, name in enumerate(("dashboard", "statistics", "fault")):
            view.tabs.setCurrentIndex(index)
            app.processEvents()
            assert window.grab().save(args.screenshot_prefix + "-" + name + ".png")
        good_stamp = window.decode_session.service.cache.last_timestamp("TestOnlySample", channel="DEMO/TEST ONLY")
        window.buffer.append(replace(make_demo_frame(0), data=bytes(3), dlc=3))
        window.refresh_frames()
        assert "Decode Error" in view.fault_label.text()
        assert view.cards["VCU"]["state"].text() == "State: Decode Error"
        assert window.decode_session.service.cache.last_timestamp("TestOnlySample", channel="DEMO/TEST ONLY") == good_stamp
        QTest.mouseClick(window.clear_button, Qt.MouseButton.LeftButton)
        assert not view.model.statistics.entries and view.fault_table.rowCount() == 0
        assert view.model.mappings and view.model.fault_mapping
        assert view.cards["VCU"]["state"].text() == "State: No Data"
        assert window.load_dbc(args.dbc)
        assert not view.model.mappings and not view.model.fault_mapping
        choose_source(view, "VCU")
        window.start_monitor()
        wait_until(lambda: view.cards["VCU"]["state"].text() == "State: Observed")
        worker = window.worker
        assert window.close() and not worker.isRunning() and window.worker is None
        assert all(t.released == 1 and not t.sent_frames for t in transports)
        print(json.dumps({"platform": app.platformName(), "window_exposed": True,
                          "ecu_cards": len(ECU_NAMES), "explicit_test_only_source": True,
                          "statistics": True, "fault_read_only_test_only_values": True,
                          "cycles": 3, "age_changes_stopped": True, "decode_error": True,
                          "clear_retains_mapping_and_cache": True, "reload_resets_mapping": True,
                          "active_close": True, "transports_released": len(transports),
                          "human_manual": "NOT VERIFIED", "hardware": "NOT VERIFIED",
                          "actual_fault_propagation": "NOT VERIFIED"}))
    finally:
        # 실패 시에도 활성 Worker를 파괴하기 전에 정상 중지한다.
        window.stop_monitor()
        if window.worker is not None:
            assert window.worker.wait(NATIVE_WAIT_MS)
        app.processEvents()
        window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
