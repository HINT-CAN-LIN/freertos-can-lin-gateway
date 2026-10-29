"""Windows UI/UX 자동 Smoke. Mock TEST ONLY이며 사용자 수동/Hardware 검증과 구분한다."""
import argparse
import json
from pathlib import Path
import can
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from pc_diagnostic.gui.window import MainWindow
from gui_native_smoke import wait_until, NATIVE_WAIT_MS
from test_vehicle_view import select_mapping
from test_ecu_observation_view import select_source

CLICK = Qt.MouseButton.LeftButton


def main():
    # 호출자가 지정한 새 증적 경로에서만 캡처하며 실제 backend 생성은 차단한다.
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--dbc", required=True)
    args = parser.parse_args()
    output = Path(args.output_dir)
    assert output.is_dir()
    app = QApplication([])
    assert app.platformName() == "windows"
    bus_calls = []
    def forbidden(*args, **kwargs):
        # 잘못된 Live 연결이 발생하면 실패시키고 실제 장치에는 접근하지 않는다.
        bus_calls.append(True)
        raise AssertionError("Hardware access is outside UI smoke")
    can.Bus = forbidden
    window = MainWindow(live_interface_factory=forbidden)
    captures = []
    def capture(name):
        # 실제 표시된 Windows Widget의 픽셀을 저장하며 합성 시안을 만들지 않는다.
        app.processEvents()
        assert window.grab().save(str(output / name))
        captures.append(name)
    try:
        window.show()
        assert QTest.qWaitForWindowExposed(window, NATIVE_WAIT_MS)
        window.navigation.setCurrentRow(0)
        assert window.tabs.currentWidget() is window.dashboard_view
        assert window.dashboard_view.cards["vehicle"][0].text() == "No Data"
        capture("dashboard-no-data.png")
        # 키보드 Navigation은 기존 Driver View를 선택해야 한다.
        window.navigation.setFocus()
        QTest.keyClick(window.navigation, Qt.Key.Key_Down)
        assert window.tabs.currentWidget() is window.driver_control_view
        driver = window.driver_control_view
        driver.accelerator_slider.setValue(30)
        driver.brake_combo.setCurrentText("ON")
        driver.gear_combo.setCurrentText("D")
        QTest.mouseClick(driver.window_open_button, CLICK)
        QTest.mouseClick(driver.light_on_button, CLICK)
        QTest.mouseClick(driver.apply_button, CLICK)
        assert driver.model.last_accepted and not driver.live_tx_button.isEnabled()
        window.page_scroll.ensureWidgetVisible(driver.ecu_label)
        assert "Not Verified" in driver.ecu_label.text()
        capture("driver-mock.png")
        assert window.load_dbc(args.dbc)
        # 실제 클릭 검증이므로 매핑 페이지와 Apply 버튼을 먼저 화면에 노출한다.
        window.tabs.setCurrentWidget(window.vehicle_view)
        app.processEvents()
        window.page_scroll.ensureWidgetVisible(window.vehicle_view.apply_button)
        select_mapping(window.vehicle_view)
        window.tabs.setCurrentWidget(window.ecu_view)
        app.processEvents()
        window.page_scroll.ensureWidgetVisible(window.ecu_view.apply_button)
        select_source(window.ecu_view)
        window.start_monitor()
        wait_until(lambda: window.receiver_running() and window.buffer.total_received >= 3)
        wait_until(lambda: window.dashboard_view.cards["ecu"][0].text() == "Observed: 1")
        window.tabs.setCurrentWidget(window.dashboard_view)
        assert "-10.0 test_unit" in window.dashboard_view.cards["vehicle"][1].text()
        capture("dashboard-mock.png")
        window.tabs.setCurrentIndex(0)
        window.monitor_filter.format_combo.setCurrentText("STD")
        wait_until(lambda: window.table.rowCount() >= 3)
        assert any(window.table.isRowHidden(row) for row in range(window.table.rowCount()))
        capture("monitor-filter.png")
        window.stop_monitor()
        wait_until(lambda: window.worker is None)
        window.monitor_filter.format_combo.setCurrentIndex(0)
        window.table.selectRow(0)
        capture("monitor-decode.png")
        # 기존 각 페이지가 같은 navigation/title과 실제 View 객체를 사용한다.
        for row in range(window.navigation.count()):
            window.navigation.setCurrentRow(row)
            assert window.page_title.text() == window.navigation.item(row).text()
            capture(f"page-{row + 1}.png")
        for _ in range(3):
            before = window.buffer.total_received
            QTest.mouseClick(window.start_button, CLICK)
            wait_until(lambda: window.buffer.total_received > before)
            QTest.mouseClick(window.stop_button, CLICK)
            wait_until(lambda: window.worker is None)
        window.clear_monitor()
        assert window.counter_label.text() == "Received: 0"
        window.connection_view.mode_combo.setCurrentText("Live")
        window.tabs.setCurrentWidget(driver)
        assert "LIVE" in window.source_badge.text()
        assert not driver.apply_button.isEnabled() and not driver.live_tx_button.isEnabled()
        assert driver.apply_mock() is None
        window.page_scroll.ensureWidgetVisible(driver.live_tx_button)
        capture("driver-live-blocked.png")
        window.connection_view.mode_combo.setCurrentText("Mock")
        # 실제 800x600 / 1024x768 창에서 스크롤로 입력·차단 상태 접근을 확인한다.
        for width, height in ((800, 600), (1024, 768)):
            window.resize(width, height)
            app.processEvents()
            assert window.width() == width and window.height() == height
            assert driver._compact_layout
            window.page_scroll.ensureWidgetVisible(driver.live_tx_button)
            wait_until(lambda: window.page_scroll.viewport().rect().contains(
                driver.live_tx_button.mapTo(window.page_scroll.viewport(), driver.live_tx_button.rect().center())))
            capture(f"driver-{width}x{height}.png")
            window.navigation.setCurrentRow(0)
            app.processEvents()
            capture(f"dashboard-{width}x{height}.png")
            window.tabs.setCurrentWidget(driver)
        assert not bus_calls
        window.start_monitor()
        wait_until(window.receiver_running)
        worker = window.worker
        assert window.close() and not worker.isRunning()
        assert not window.timer.isActive() and not window.age_timer.isActive()
        print(json.dumps({"platform": app.platformName(), "window_exposed": True,
                          "navigation_pages": window.navigation.count(), "repeat_start_stop": 3,
                          "small_windows": ["800x600", "1024x768"], "captures": captures,
                          "source": "Mock TEST ONLY / Live selection blocked, no bus opened",
                          "CAN_backend_calls": len(bus_calls), "active_close": True,
                          "hardware": "NOT VERIFIED", "human_manual": "NOT VERIFIED"}))
    finally:
        # 실패 경로에서도 기존 Receiver/Writer/Timer 종료 계약을 지킨다.
        window.stop_monitor()
        if window.worker is not None:
            assert window.worker.wait(NATIVE_WAIT_MS)
        app.processEvents()
        window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
