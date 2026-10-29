"""Ignition Windows Native UI 검증. 실제 ECU/HIL 결과가 아니다."""
import argparse
import json
from pathlib import Path
import can
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from pc_diagnostic.gui.window import MainWindow
from pc_diagnostic.gui.driver_input import DriverInputs, InputState, IGNITION_CHOICES
from pc_diagnostic.gui.driver_control_view import HISTORY_INPUTS_COLUMN, HISTORY_ROW_HEIGHT, input_summary
from pc_diagnostic.interfaces import MockCanInterface, PythonCanInterface
from pc_diagnostic.sender import RawCanSender
from gui_native_smoke import wait_until, NATIVE_WAIT_MS

SIZES = ((800, 600), (1024, 768), (1280, 920))


def main():
    # 출력은 외부 증적 경로에만 저장하며 transport는 Mock RX만 사용한다.
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    assert app.platformName() == "windows"
    calls = {"open": 0, "tx": 0}
    def block_open(*args, **kwargs):
        # 실제 Bus factory를 부르면 계수 후 즉시 실패한다.
        calls["open"] += 1
        raise AssertionError("physical CAN open forbidden")
    def block_tx(*args, **kwargs):
        # 기존 CLI/Adapter 송신 API도 시험 중에는 모두 감시한다.
        calls["tx"] += 1
        raise AssertionError("CAN TX forbidden")
    can.Bus = block_open
    can.BusABC.send = block_tx
    MockCanInterface.send = block_tx
    PythonCanInterface.send = block_tx
    RawCanSender.send = block_tx
    transports = []
    def factory():
        # Driver Adapter와 무관한 기존 DEMO 수신 전용이다.
        interface = MockCanInterface()
        transports.append(interface)
        return interface
    window = MainWindow(factory, live_interface_factory=block_open)
    captures = []
    try:
        window.show()
        assert QTest.qWaitForWindowExposed(window, NATIVE_WAIT_MS)
        view = window.driver_control_view
        window.tabs.setCurrentWidget(view)
        def expose(widget):
            # 화면 밖 입력/이력은 기존 페이지 scroll로 접근한다.
            window.page_scroll.ensureWidgetVisible(widget)
            app.processEvents()
            assert window.page_scroll.viewport().rect().contains(
                widget.mapTo(window.page_scroll.viewport(), widget.rect().center()))
        def capture(name):
            # QWidget의 실제 Windows rendering을 저장하며 가상 시안을 만들지 않는다.
            app.processEvents()
            path = out / name
            assert window.grab().save(str(path))
            captures.append(path.name)
        for width, height in SIZES:
            window.resize(width, height)
            app.processEvents()
            assert (window.width(), window.height()) == (width, height)
            view.reset_inputs()
            for ignition in IGNITION_CHOICES:
                button = view.choice_strips["ignition"].buttons[ignition]
                expose(button)
                QTest.mouseClick(button, Qt.MouseButton.LeftButton)
                assert view.model.draft.ignition == ignition and view.model.last_accepted is None
                capture(f"driver-ignition-{ignition.lower()}-{width}x{height}.png")
            view.accelerator_edit.setText("53.12345678901234")
            view.brake_combo.setCurrentText("ON")
            view.gear_combo.setCurrentText("R")
            view.window_combo.setCurrentText("CLOSE")
            view.light_combo.setCurrentText("ON")
            expose(view.ignition_combo.parentWidget())
            window.page_scroll.verticalScrollBar().setValue(0)
            capture(f"driver-inputs-{width}x{height}.png")
            expose(view.apply_button)
            QTest.mouseClick(view.apply_button, Qt.MouseButton.LeftButton)
            receipt = view.model.last_accepted
            expected_inputs = DriverInputs(53.12345678901234, True, "R", "CLOSE", "ON", "RUN")
            assert receipt.command.inputs == expected_inputs
            expose(view.observation_label)
            assert "ECU Applied: NOT VERIFIED" in view.observation_label.text()
            assert "UART TX: Disabled / not sent" in view.observation_label.text()
            capture(f"driver-accepted-{width}x{height}.png")
            expose(view.history_table)
            assert view.history_table.rowCount() == len(view.model.history)
            latest_row = view.history_table.rowCount() - 1
            input_item = view.history_table.item(latest_row, HISTORY_INPUTS_COLUMN)
            expected_summary = input_summary(expected_inputs)
            assert input_item.text() == expected_summary and input_item.toolTip() == expected_summary
            assert view.history_table.rowHeight(latest_row) >= HISTORY_ROW_HEIGHT
            for value in ("Ignition=RUN", "53.12345678901234%", "Brake=ON", "Gear=R",
                          "Window=CLOSE", "Light=ON"):
                assert value in input_item.text()
            view.history_table.selectRow(latest_row)
            assert all(value in view.history_detail_text.toPlainText()
                       for value in ("Source: Mock / DEMO / TEST ONLY", "53.12345678901234%",
                                     "Brake=ON", "Gear=R", "Window=CLOSE", "Light=ON"))
            capture(f"driver-history-{width}x{height}.png")
            if width == 1280:
                view.history_table.setColumnWidth(HISTORY_INPUTS_COLUMN, 640)
                assert view.history_table.columnWidth(HISTORY_INPUTS_COLUMN) == 640
                capture("driver-history-expanded-1280x920.png")
                expose(view.history_detail_text)
                capture("driver-history-details-1280x920.png")
            old_adapter = view.model._adapter
            window.connection_view.mode_combo.setCurrentText("Live")
            assert old_adapter.closed and view.model.state == InputState.LIVE_BLOCKED
            assert view.ignition_combo.currentData() is None and not view.model.history
            assert not view.apply_button.isEnabled() and not view.live_tx_button.isEnabled()
            assert view.apply_mock() is None and view.model.apply_mock() is None
            assert not view.model.stage(DriverInputs(ignition="ON"))
            window.page_scroll.verticalScrollBar().setValue(0)
            capture(f"driver-live-blocked-{width}x{height}.png")
            window.connection_view.mode_combo.setCurrentText("Mock")
        window.activateWindow()
        window.raise_()
        assert QTest.qWaitForWindowActive(window, NATIVE_WAIT_MS)
        for i in range(9):
            QTest.keyClick(window, getattr(Qt.Key, "Key_" + str(i + 1)), Qt.KeyboardModifier.AltModifier)
            wait_until(lambda i=i: window.navigation.currentRow() == i)
        assert window.navigation.count() == 9
        view.ignition_combo.setCurrentText("ON")
        receipt = view.apply_mock()
        for _ in range(3):
            before = window.buffer.total_received
            window.start_monitor()
            wait_until(lambda: window.buffer.total_received > before)
            window.stop_monitor()
            wait_until(lambda: window.worker is None)
            assert view.model.last_accepted == receipt
        window.clear_monitor()
        assert view.model.last_accepted == receipt
        adapter = view.model._adapter
        window.start_monitor()
        wait_until(lambda: window.worker is not None and window.worker.isRunning())
        assert window.close() and adapter.closed and view.model.closed
        assert calls == {"open": 0, "tx": 0}
        assert all(not t.sent_frames for t in transports)
        fresh = MainWindow(factory, live_interface_factory=block_open)
        assert fresh.driver_control_view.ignition_combo.currentData() is None
        assert not fresh.driver_control_view.model.history
        assert fresh.close()
        result = {"platform": app.platformName(), "ignition_choices": list(IGNITION_CHOICES),
                  "sizes": SIZES, "captures": captures, "navigation_alt_1_9": True,
                  "apply_reset_history": True, "live_slot_model_blocked": True,
                  "repeat_start_stop": 3, "active_close_reopen": True,
                  "CAN_calls": calls, "hardware": "NOT VERIFIED", "human_manual": "NOT VERIFIED"}
        (out/"result.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
        print(json.dumps(result))
    finally:
        # 실패 시에도 기존 Worker 해제 정책을 지킨다.
        window.stop_monitor()
        if window.worker is not None:
            assert window.worker.wait(NATIVE_WAIT_MS)
        app.processEvents()
        window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
