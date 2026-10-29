"""PC→VCU UART GUI smoke without opening serial or CAN hardware."""
import argparse
import json
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from pc_diagnostic.gui.window import MainWindow


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    window = MainWindow()
    try:
        window.show()
        app.processEvents()
        view = window.driver_control_view
        assert view.uart_button.isEnabled() and view.uart_button.text() == "Connect VCU UART"
        assert not view.uart_log_button.isEnabled()
        assert view.keyboard_toggle.isEnabled()
        assert not view.live_tx_button.isEnabled()
        assert "100 ms TX" in view.approval_label.text()
        window.tabs.setCurrentWidget(view)
        view.keyboard_toggle.setChecked(True)
        QTest.keyPress(window, Qt.Key.Key_Right)
        app.processEvents()
        assert view.model.draft.steering_direction == "RIGHT"
        assert view.arrow_indicators["right"].property("pressed") is True
        QTest.keyRelease(window, Qt.Key.Key_Right)
        app.processEvents()
        assert view.model.draft.steering_direction == "CENTER"
        view.uart_port_edit.setText("/dev/cu.not-opened-in-smoke")
        assert view._uart_worker is None  # serial is never opened by this smoke
        view.accelerator_edit.setText("25")
        view.brake_combo.setCurrentText("OFF")
        view.gear_combo.setCurrentText("D")
        receipt = view.apply_mock()
        assert receipt is not None and receipt.command.inputs.accelerator == 25
        assert "Last Mock Accepted" in view.accepted_label.text()
        assert window.worker is None and view._uart_worker is None
        path = output / "driver-uart-ready.png"
        assert window.grab().save(str(path))
        window.close()
        result = {"platform": app.platformName(), "uart_controls_present": True,
                  "keyboard_steering": "RIGHT/CENTER and visual indicator PASS",
                  "serial_opened": False, "can_worker": "not started",
                  "mock_apply": True, "physical_hardware": "NOT VERIFIED"}
        (output / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result))
    finally:
        window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
