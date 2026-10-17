"""UART Driver Control Windows Native smoke. 실제 UART/CAN Hardware 시험이 아니다."""
import argparse
import json
from pathlib import Path
import can
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from pc_diagnostic.gui.driver_input import InputState
from pc_diagnostic.gui.window import MainWindow
from pc_diagnostic.interfaces import MockCanInterface, PythonCanInterface
from pc_diagnostic.sender import RawCanSender
from gui_native_smoke import wait_until, NATIVE_WAIT_MS

SIZES = ((800, 600), (1024, 768), (1280, 920))


def main():
    # 스크린샷은 요청자가 승인한 외부 증적 폴더에 생성한다.
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    assert app.platformName() == "windows"
    calls = {"can_open": 0, "can_tx": 0}

    def block_can_open(*args, **kwargs):
        calls["can_open"] += 1
        raise AssertionError("physical CAN open forbidden")

    def block_can_tx(*args, **kwargs):
        calls["can_tx"] += 1
        raise AssertionError("CAN TX forbidden")

    can.Bus = block_can_open
    can.BusABC.send = block_can_tx
    MockCanInterface.send = block_can_tx
    PythonCanInterface.send = block_can_tx
    RawCanSender.send = block_can_tx
    interfaces = []

    def mock_factory():
        # CAN 모니터는 기존 DEMO/TEST ONLY Mock Interface만 사용한다.
        interface = MockCanInterface()
        interfaces.append(interface)
        return interface

    window = MainWindow(mock_factory, live_interface_factory=block_can_open)
    screenshots = []
    try:
        window.show()
        assert QTest.qWaitForWindowExposed(window, NATIVE_WAIT_MS)
        view = window.driver_control_view
        panel = view.uart_connection_view
        expected = {
            "interface": "Interface: UART", "target": "Target: VCU",
            "connection": "Connection: NOT CONFIGURED",
            "protocol": "Protocol: PENDING APPROVAL", "tx": "UART TX: DISABLED",
            "rx": "UART RX: NOT VERIFIED",
        }
        assert {key: label.text() for key, label in panel.status_labels.items()} == expected
        assert not panel.connect_button.isEnabled() and not panel.disconnect_button.isEnabled()
        assert not panel.request_connect() and not panel.request_disconnect()
        assert "NOT IMPLEMENTED / NOT VERIFIED" in panel.response_label.text()
        assert "CAN RX is not a UART response" in panel.can_scope_label.text()
        window.tabs.setCurrentWidget(view)

        for width, height in SIZES:
            window.resize(width, height)
            app.processEvents()
            assert (window.width(), window.height()) == (width, height)
            window.page_scroll.verticalScrollBar().setValue(0)
            app.processEvents()
            path = out / f"driver-uart-{width}x{height}.png"
            assert window.grab().save(str(path))
            screenshots.append(path.name)
            assert "Connection: NOT CONFIGURED" in panel.status_labels["connection"].text()
            assert not panel.connect_button.isEnabled()
            view.ignition_combo.setCurrentText("ON")
            view.accelerator_edit.setText("25.5")
            view.brake_combo.setCurrentText("ON")
            view.gear_combo.setCurrentText("D")
            view.window_combo.setCurrentText("CLOSE")
            view.light_combo.setCurrentText("OFF")
            receipt = view.apply_mock()
            assert receipt is not None and view.model.state == InputState.MOCK_ACCEPTED
            assert receipt.command.inputs.window == "CLOSE" and receipt.command.inputs.light == "OFF"
            assert "NOT IMPLEMENTED / NOT VERIFIED" in panel.response_label.text()
            view.reset_inputs()
            assert view.model.state == InputState.NOT_CONFIGURED

        # CAN receive/stop does not mutate or configure the separate UART status panel.
        before = window.buffer.total_received
        window.start_monitor()
        wait_until(lambda: window.buffer.total_received > before)
        window.stop_monitor()
        wait_until(lambda: window.worker is None)
        assert window.buffer.total_received > before
        assert panel.status_labels["connection"].text() == "Connection: NOT CONFIGURED"
        assert calls == {"can_open": 0, "can_tx": 0}
        assert all(not interface.sent_frames for interface in interfaces)

        window.activateWindow()
        window.raise_()
        assert QTest.qWaitForWindowActive(window, NATIVE_WAIT_MS)
        for index in range(9):
            QTest.keyClick(window, getattr(Qt.Key, "Key_" + str(index + 1)), Qt.KeyboardModifier.AltModifier)
            wait_until(lambda index=index: window.navigation.currentRow() == index)
        assert window.navigation.count() == 9
        assert window.close()
        result = {
            "platform": app.platformName(), "screenshots": screenshots,
            "sizes": [list(size) for size in SIZES], "navigation_alt_1_9": True,
            "mock_apply_reset": True, "uart_connect_disconnect": "disabled/no operation",
            "uart_protocol": "PENDING APPROVAL", "uart_tx": "DISABLED",
            "uart_rx": "NOT VERIFIED", "VCU_response": "NOT IMPLEMENTED / NOT VERIFIED",
            "CAN_open_and_TX_calls": calls,
            "UART_serial_open_read_write": "NOT IMPLEMENTED; no call path exercised",
            "hardware": "NOT VERIFIED", "human_manual": "NOT VERIFIED",
        }
        (out / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result))
    finally:
        # 실패 시에도 기존 CAN Worker 종료 계약을 지킨다.
        window.stop_monitor()
        if window.worker is not None:
            assert window.worker.wait(NATIVE_WAIT_MS)
        app.processEvents()
        window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())