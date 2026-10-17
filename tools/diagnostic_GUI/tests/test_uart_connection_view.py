"""UART 상태 패널과 기존 Driver Mock의 분리를 검증한다."""
import pytest
pytest.importorskip("PySide6", reason="install .[gui]")
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from test_gui import qt_app, window_factory, wait_until
from test_visual_polish import expose
from pc_diagnostic.gui.driver_input import InputState


EXPECTED_UART_STATUS = {
    "interface": "Interface: UART",
    "target": "Target: VCU",
    "connection": "Connection: NOT CONFIGURED",
    "protocol": "Protocol: PENDING APPROVAL",
    "tx": "UART TX: DISABLED",
    "rx": "UART RX: NOT VERIFIED",
}


def test_uart_panel_never_connects_and_can_receive_stays_independent(window_factory):
    # CAN Monitor Start/Stop은 별도 Worker를 사용하고 UART 상태는 바꾸지 않는다.
    window = window_factory()
    view = window.driver_control_view
    panel = view.uart_connection_view
    assert panel.status_labels.keys() == EXPECTED_UART_STATUS.keys()
    assert {key: label.text() for key, label in panel.status_labels.items()} == EXPECTED_UART_STATUS
    assert not panel.connect_button.isEnabled() and not panel.disconnect_button.isEnabled()
    assert not panel.request_connect() and not panel.request_disconnect()
    assert panel.status_labels["connection"].text() == "Connection: NOT CONFIGURED"
    assert "VCU Response: NOT IMPLEMENTED / NOT VERIFIED" in panel.response_label.text()
    assert "CAN RX is not a UART response" in panel.can_scope_label.text()
    assert "UART Driver Input payload" in view.policy_label.text()

    before = window.buffer.total_received
    window.start_monitor()
    wait_until(lambda: window.buffer.total_received > before)
    window.stop_monitor()
    wait_until(lambda: window.worker is None)
    assert window.buffer.total_received > before
    assert panel.status_labels["connection"].text() == "Connection: NOT CONFIGURED"

    # CAN Live 수신 설정을 선택해도 UART 연결 상태를 대신 표시하지 않는다.
    window.connection_view.mode_combo.setCurrentText("Live")
    assert panel.status_labels["connection"].text() == "Connection: NOT CONFIGURED"
    assert panel.status_labels["rx"].text() == "UART RX: NOT VERIFIED"
    assert not panel.connect_button.isEnabled()


def test_existing_driver_inputs_remain_mock_only_and_separate_from_uart(window_factory):
    # Apply는 기존 메모리 Mock만 수락하고 UART 응답/전송 상태를 합성하지 않는다.
    window = window_factory()
    view = window.driver_control_view
    panel = view.uart_connection_view
    view.ignition_combo.setCurrentText("RUN")
    view.accelerator_edit.setText("37.5")
    view.brake_combo.setCurrentText("ON")
    view.gear_combo.setCurrentText("R")
    view.window_combo.setCurrentText("OPEN")
    view.light_combo.setCurrentText("ON")
    receipt = view.apply_mock()
    assert receipt is not None and view.model.state == InputState.MOCK_ACCEPTED
    assert receipt.command.inputs.window == "OPEN" and receipt.command.inputs.light == "ON"
    assert "Window/Light는 별도 Mock Body 입력" in view.policy_label.text()
    assert "Last Mock Accepted" in view.accepted_label.text()
    assert "NOT IMPLEMENTED / NOT VERIFIED" in panel.response_label.text()
    assert panel.status_labels["connection"].text() == "Connection: NOT CONFIGURED"
    assert window.buffer.total_received == 0
    view.reset_inputs()
    assert view.model.state == InputState.NOT_CONFIGURED and not view.model.history
    assert panel.status_labels["connection"].text() == "Connection: NOT CONFIGURED"


@pytest.mark.parametrize("size", [(800, 600), (1024, 768), (1280, 920)])
def test_uart_panel_and_mock_actions_are_accessible_at_supported_sizes(window_factory, qt_app, size):
    # 기존 9개 페이지와 창 크기를 유지하며 disabled UART와 Mock 동작을 확인한다.
    window = window_factory()
    window.resize(*size)
    qt_app.processEvents()
    assert (window.width(), window.height()) == size
    view = window.driver_control_view
    panel = view.uart_connection_view
    window.tabs.setCurrentWidget(view)
    for widget in (panel, panel.connect_button, panel.disconnect_button,
                   view.apply_button, view.reset_button, view.ignition_combo,
                   view.accelerator_edit, view.history_table):
        expose(window, widget, qt_app)
    assert panel.isVisible() and not panel.connect_button.isEnabled()
    assert "UART TX DISABLED" in view.approval_label.text() or "UART" in view.approval_label.text()
    assert window.navigation.count() == 9
    QTest.mouseClick(view.apply_button, Qt.MouseButton.LeftButton)
    assert view.model.state == InputState.INPUT_ERROR  # 빈 입력은 기존 Validation대로 거부한다.
    assert panel.status_labels["connection"].text() == "Connection: NOT CONFIGURED"