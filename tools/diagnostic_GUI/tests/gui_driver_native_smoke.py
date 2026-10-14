"""Windows Driver Control 자동 Smoke. 물리 CAN/사용자 수동 검증이 아니다."""
import argparse
import json
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from pc_diagnostic.gui.window import MainWindow
from pc_diagnostic.gui.driver_input import InputState
from pc_diagnostic.interfaces import MockCanInterface, PythonCanInterface
from pc_diagnostic.sender import RawCanSender
import can
from gui_native_smoke import wait_until, NATIVE_WAIT_MS

CLICK = Qt.MouseButton.LeftButton


def main():
    # 시험 파일은 전용 Temp 아래에만 저장하고 CAN backend는 trap으로 차단한다.
    parser = argparse.ArgumentParser()
    parser.add_argument("--screenshot", required=True)
    args = parser.parse_args()
    app = QApplication([])
    assert app.platformName() == "windows", app.platformName()
    calls = []
    def forbidden(*args, **kwargs):
        # Driver 입력 경로가 물리/Mock 송신 경계를 호출하면 즉시 실패한다.
        calls.append(True)
        raise AssertionError("No CAN open/TX allowed")
    can.Bus = forbidden
    can.BusABC.send = forbidden
    MockCanInterface.send = forbidden
    PythonCanInterface.send = forbidden
    RawCanSender.send = forbidden
    transports = []
    def factory():
        # 수신만 기존 Mock fixture로 수행하며 Driver Adapter와 분리한다.
        transport = MockCanInterface()
        transports.append(transport)
        return transport
    window = MainWindow(factory, live_interface_factory=forbidden)
    try:
        window.show()
        assert QTest.qWaitForWindowExposed(window, NATIVE_WAIT_MS)
        view = window.driver_control_view
        window.tabs.setCurrentWidget(view)
        view.accelerator_slider.setValue(30)
        view.brake_combo.setCurrentText("ON")
        view.gear_combo.setCurrentText("D")
        for button in (view.window_open_button, view.window_close_button,
                       view.light_on_button, view.light_off_button):
            QTest.mouseClick(button, CLICK)
            assert view.model.state == InputState.MOCK_INPUT
            QTest.mouseClick(view.apply_button, CLICK)
            assert view.model.state == InputState.MOCK_ACCEPTED
        receipt = view.model.last_accepted
        adapter = view.model._adapter
        assert receipt.command.inputs.accelerator == 30 and receipt.command.inputs.brake is True
        assert "ECU Response Not Verified" in view.ecu_label.text()
        assert window.grab().save(args.screenshot)
        for _ in range(3):
            before = window.buffer.total_received
            window.start_monitor()
            wait_until(lambda: window.buffer.total_received > before)
            window.stop_monitor()
            wait_until(lambda: window.worker is None)
            assert view.model.last_accepted == receipt
        window.clear_monitor()
        assert view.model.last_accepted == receipt
        window.connection_view.mode_combo.setCurrentText("Live")
        assert adapter.closed and view.model.last_accepted is None
        assert view.model.state == InputState.LIVE_BLOCKED
        assert not view.apply_button.isEnabled() and not view.live_tx_button.isEnabled()
        assert view.apply_mock() is None and view.model.apply_mock() is None
        window.connection_view.mode_combo.setCurrentText("Mock")
        view.light_combo.setCurrentText("OFF")
        assert view.apply_mock()
        active_adapter = view.model._adapter
        QTest.mouseClick(view.reset_button, CLICK)
        assert active_adapter.closed and view.model.state == InputState.NOT_CONFIGURED
        view.gear_combo.setCurrentText("R")
        assert view.apply_mock()
        active_adapter = view.model._adapter
        window.start_monitor()
        wait_until(lambda: window.worker is not None and window.worker.isRunning())
        assert window.close() and active_adapter.closed and view.model.closed
        assert not calls and all(not transport.sent_frames for transport in transports)
        print(json.dumps({"platform": app.platformName(), "window_exposed": True,
                          "all_driver_inputs": True, "simultaneous_inputs_preserved": True,
                          "repeat_rx_start_stop": 3, "source_reset": True, "direct_live_blocked": True,
                          "CAN_open_or_TX_calls": len(calls), "active_close": True,
                          "human_manual": "NOT VERIFIED", "hardware": "NOT VERIFIED"}))
    finally:
        # 실패 시에도 활성 Qt Worker를 정상 해제한다.
        window.stop_monitor()
        if window.worker is not None:
            assert window.worker.wait(NATIVE_WAIT_MS)
        app.processEvents()
        window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
