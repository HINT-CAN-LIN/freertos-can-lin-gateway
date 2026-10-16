"""3K-2 Windows 레이아웃 자동 검증. Mock/TEST ONLY, 실제 CAN/HIL/수동 검증 아님."""
import argparse
import json
from pathlib import Path
import can
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from pc_diagnostic.gui.window import MainWindow
from gui_native_smoke import wait_until, NATIVE_WAIT_MS

CLICK = Qt.MouseButton.LeftButton
SIZES = ((1280, 920), (1024, 768), (800, 600))


def main():
    # 증적은 명시된 외부 폴더에만 저장하며 실제 Backend 생성은 실패시킨다.
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
        # Mock 표시 검증 중 실기 연결을 시도하면 테스트 자체를 실패시킨다.
        bus_calls.append(True)
        raise AssertionError("Real hardware is outside layout smoke")
    can.Bus = forbidden
    window = MainWindow(live_interface_factory=forbidden)
    captures, metrics, action_checks = [], [], []
    def settle():
        # 고정 sleep 대신 Qt 이벤트를 처리하고 아래 실제 geometry/상태를 검사한다.
        for _ in range(5):
            app.processEvents()
    def capture(name):
        # 실제 Windows 위젯의 캡처이며 합성 시안이 아니다.
        settle()
        assert window.grab().save(str(output / name))
        captures.append(name)
    def expose(widget):
        # 페이지 ScrollArea가 실제 버튼 전체를 노출할 수 있어야 한다.
        window.page_scroll.ensureWidgetVisible(widget)
        settle()
        viewport = window.page_scroll.viewport()
        rect = widget.rect()
        rect.moveTopLeft(widget.mapTo(viewport, rect.topLeft()))
        assert viewport.rect().contains(rect), (widget.objectName(), widget.accessibleName(), rect, viewport.rect())
    try:
        window.show()
        assert QTest.qWaitForWindowExposed(window, NATIVE_WAIT_MS)
        actions = {
            0: (), 1: (window.driver_control_view.apply_button, window.driver_control_view.reset_button,
                       window.driver_control_view.window_open_button, window.driver_control_view.light_on_button),
            2: (window.monitor_filter.search,), 3: (window.vehicle_view.apply_button,),
            4: (window.ecu_view.apply_button,), 5: (window.fault_monitor_view.add_button, window.fault_monitor_view.clear_button),
            6: (window.graph_view.apply_button, window.graph_view.pause_button, window.graph_view.clear_button),
            7: (window.logging_view.choose_button, window.logging_view.start_button),
            8: (window.automation_view.run_button, window.automation_view.cancel_button),
        }
        for width, height in SIZES:
            window.resize(width, height)
            settle()
            assert (window.width(), window.height()) == (width, height)
            for row in range(9):
                window.navigation.setCurrentRow(row)
                settle()
                page = window.tabs.currentWidget()
                area = window.page_scroll
                area.verticalScrollBar().setValue(0)
                settle()
                title = window.navigation.item(row).text().replace(" / ", "-").replace(" ", "-").lower()
                capture(f"{title}-{width}x{height}.png")
                metrics.append({"size": [width, height], "page": title, "header_height": window.compact_header.height(),
                    "content_top": area.mapTo(window, QPoint()).y(), "viewport_height": area.viewport().height(),
                    "horizontal_scroll": area.horizontalScrollBar().maximum()})
                for action in actions[row]:
                    assert action.isVisible()
                    expose(action)
                    action_checks.append([width, height, title, action.accessibleName() or action.text()])
                for section in getattr(page, "ui_sections", ()):
                    original = section.button.isChecked()
                    section.set_expanded(not original)
                    settle()
                    assert all(widget.isHidden() == original for widget in section.widgets)
                    section.set_expanded(original)
                    settle()
        # 작은 화면에서 설정을 접은 관측 화면과 설명 펼친 결과도 실제 캡처로 남긴다.
        for row in (3, 4, 5):
            window.navigation.setCurrentRow(row)
            settle()
            section = window.tabs.currentWidget().ui_sections[0]
            section.set_expanded(False)
            window.page_scroll.verticalScrollBar().setValue(0)
            capture(f"observation-mapping-collapsed-page-{row + 1}-800x600.png")
            section.set_expanded(True)
        window.navigation.setCurrentRow(8)
        window.automation_view.ui_sections[0].set_expanded(True)
        capture("automation-description-expanded-800x600.png")
        window.automation_view.ui_sections[0].set_expanded(False)
        # Alt+1..9 및 화살표 탐색은 실제 Window Shortcut/Qt key event로 검증한다.
        window.activateWindow()
        window.raise_()
        assert QTest.qWaitForWindowActive(window, NATIVE_WAIT_MS)
        for row in range(9):
            QTest.keyClick(window, getattr(Qt.Key, "Key_" + str(row + 1)), Qt.KeyboardModifier.AltModifier)
            wait_until(lambda row=row: window.navigation.currentRow() == row)
        window.navigation.setCurrentRow(0)
        window.navigation.setFocus()
        QTest.keyClick(window.navigation, Qt.Key.Key_Down)
        assert window.tabs.currentWidget() is window.driver_control_view
        # 표시 버튼은 기존 Mock ComboBox/Validation/Adapter를 그대로 사용한다.
        driver = window.driver_control_view
        driver.accelerator_edit.setText("37.5")
        assert driver.model.draft.accelerator == 37.5 and driver.accelerator_slider.value() == round(37.5)
        for name, choice in (("brake", "OFF"), ("gear", "D"), ("window", "OPEN"), ("light", "ON")):
            button = driver.choice_strips[name].buttons[choice]
            expose(button)
            QTest.mouseClick(button, CLICK)
            assert button.isChecked()
        expose(driver.apply_button)
        QTest.mouseClick(driver.apply_button, CLICK)
        assert driver.model.last_accepted and "Mock Accepted" in driver.receipt_summary.text()
        assert "Not Verified" in driver.ecu_label.text() and not driver.live_tx_button.isEnabled()
        for size in ((1280, 920), (800, 600)):
            window.resize(*size)
            settle()
            window.page_scroll.verticalScrollBar().setValue(0)
            capture(f"driver-mock-{size[0]}x{size[1]}.png")
        assert window.load_dbc(args.dbc)
        window.tabs.setCurrentIndex(0)
        window.start_monitor()
        wait_until(lambda: window.table.rowCount() >= 3)
        window.stop_monitor()
        wait_until(lambda: window.worker is None)
        window.table.selectRow(0)
        window.resize(1280, 920)
        capture("can-monitor-mock-decode-1280x920.png")
        # 긴 이름은 표시 문자열만 모의한다. DBC 파일/Signal/메시지 계약은 변경하지 않는다.
        long_name = "TEST ONLY display name / " + "LongMessage_LongSignal_" * 30
        original = window.vehicle_view.message_combo.itemText(1)
        data = window.vehicle_view.message_combo.itemData(1)
        window.vehicle_view.message_combo.setItemText(1, long_name)
        window.vehicle_view.message_combo.setCurrentIndex(1)
        window.tabs.setCurrentWidget(window.vehicle_view)
        window.resize(800, 600)
        settle()
        assert window.width() == 800
        assert window.vehicle_view.message_combo.itemData(1) == data
        capture("vehicle-long-display-name-800x600.png")
        window.vehicle_view.message_combo.setItemText(1, original)
        graph = window.graph_view
        graph.message_combo.setCurrentIndex(1)
        signal_index = 1
        signal_text = graph.signal_combo.itemText(signal_index)
        signal_data = graph.signal_combo.itemData(signal_index)
        graph.signal_combo.setItemText(signal_index, long_name)
        graph.signal_combo.setCurrentIndex(signal_index)
        window.tabs.setCurrentWidget(graph)
        settle()
        assert graph.signal_combo.toolTip() == long_name
        assert graph.signal_combo.itemData(signal_index) == signal_data
        assert graph.model.selection is None
        capture("graph-long-signal-display-name-800x600.png")
        graph.signal_combo.setItemText(signal_index, signal_text)

        # Receiver/종료 정책은 기존 구현을 사용한다. 매 반복마다 새 수신을 확인한다.
        for _ in range(3):
            before = window.buffer.total_received
            window.start_monitor()
            wait_until(lambda: window.buffer.total_received > before)
            window.stop_monitor()
            wait_until(lambda: window.worker is None)
        window.clear_monitor()
        assert window.counter_label.text() == "Received: 0"
        window.connection_view.mode_combo.setCurrentText("Live")
        window.tabs.setCurrentWidget(driver)
        assert not driver.apply_button.isEnabled() and not driver.live_tx_button.isEnabled()
        assert all(not b.isEnabled() for s in driver.choice_strips.values() for b in s.buttons.values())
        assert driver.apply_mock() is None
        capture("driver-live-tx-blocked-800x600.png")
        window.connection_view.mode_combo.setCurrentText("Mock")
        window.show_error("TEST ONLY layout error visibility")
        assert window.error_area.isVisible() and window.activity_section.button.isChecked()
        capture("activity-error-visible-800x600.png")
        window.start_monitor()
        wait_until(window.receiver_running)
        worker = window.worker
        assert window.close() and not worker.isRunning()
        assert not window.timer.isActive() and not window.age_timer.isActive()
        assert not window.logging_view.timer.isActive() and not window.graph_view.timer.isActive()
        assert not bus_calls
        result = {"platform": app.platformName(), "sizes": SIZES, "pages": 9, "captures": captures,
                  "metrics": metrics, "device_pixel_ratio": window.devicePixelRatioF(),
                  "action_checks": len(action_checks), "alt_shortcuts": 9,
                  "repeat_start_stop": 3, "active_close": True, "CAN_backend_calls": 0,
                  "long_names": "TEST ONLY display text; DBC/selection data unchanged",
                  "hardware": "NOT VERIFIED", "human_manual": "NOT VERIFIED"}
        (output / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False))
    finally:
        # 실패 경로에서도 기존 자원 해제를 보장한다.
        window.stop_monitor()
        if window.worker is not None:
            assert window.worker.wait(NATIVE_WAIT_MS)
        app.processEvents()
        window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
