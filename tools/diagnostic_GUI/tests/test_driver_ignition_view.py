"""Ignition GUI tests: Mock only, no physical CAN open or TX."""
import pytest
pytest.importorskip("PySide6", reason="install .[gui]")
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from test_gui import qt_app, window_factory, wait_until
from test_visual_polish import expose
from pc_diagnostic.gui.driver_input import InputState, IGNITION_CHOICES
from pc_diagnostic.interfaces import MockCanInterface, PythonCanInterface
from pc_diagnostic.sender import RawCanSender


@pytest.fixture
def forbidden_can(monkeypatch):
    # UI/Slot/Model 경로에서 물리 Bus 생성과 송신을 차단한다.
    import can
    calls = []
    def forbidden(*args, **kwargs):
        # 경계 호출을 기록한 뒤 즉시 실패시켜 묵시적 송신도 검출한다.
        calls.append(True)
        raise AssertionError("No physical CAN open or TX")
    for obj, name in ((can, "Bus"), (can.BusABC, "send"), (MockCanInterface, "send"),
                      (PythonCanInterface, "send"), (RawCanSender, "send")):
        monkeypatch.setattr(obj, name, forbidden)
    return calls


@pytest.mark.parametrize("ignition", IGNITION_CHOICES)
def test_gui_apply_reset_keeps_other_controls_and_history(window_factory, forbidden_can, ignition):
    # 원래 선택/수치는 새 Ignition 편집 때문에 바뀌면 안 된다.
    window = window_factory()
    view = window.driver_control_view
    window.tabs.setCurrentWidget(view)
    view.accelerator_edit.setText("12.5")
    view.brake_combo.setCurrentText("ON")
    view.gear_combo.setCurrentText("D")
    view.window_combo.setCurrentText("OPEN")
    view.light_combo.setCurrentText("ON")
    view.choice_strips["ignition"].buttons[ignition].click()
    assert view.model.last_accepted is None
    receipt = view.apply_mock()
    assert receipt.command.inputs.ignition == ignition
    assert (receipt.command.inputs.accelerator, receipt.command.inputs.brake, receipt.command.inputs.gear,
            receipt.command.inputs.window, receipt.command.inputs.light) == (12.5, True, "D", "OPEN", "ON")
    assert view.history_table.rowCount() == len(view.model.history)
    assert ignition in view.history_table.item(view.history_table.rowCount()-1, 3).text()
    assert "Mock only" in view.observation_label.text() and "Not sent" in view.observation_label.text()
    assert "NOT VERIFIED" in view.observation_label.text()
    assert window.worker is None and window.buffer.total_received == 0
    adapter = view.model._adapter
    view.reset_inputs()
    assert adapter.closed and view.ignition_combo.currentData() is None
    assert all(not b.isChecked() for b in view.choice_strips["ignition"].buttons.values())
    assert not view.model.history and "No Data" in view.observation_label.text()
    assert not forbidden_can


def test_gui_invalid_direct_selection_live_slot_and_close_reopen(window_factory, forbidden_can):
    # 미승인 값을 직접 설정해도 Validation을 통과하지 못한다.
    window = window_factory()
    view = window.driver_control_view
    view.ignition_combo.addItem("BAD TEST ONLY", "READY")
    view.ignition_combo.setCurrentIndex(view.ignition_combo.count()-1)
    assert view.model.state == InputState.INPUT_ERROR and view.apply_mock() is None
    view.ignition_combo.setCurrentText("ON")
    assert view.apply_mock()
    adapter = view.model._adapter
    window.connection_view.mode_combo.setCurrentText("Live")
    assert adapter.closed and view.ignition_combo.currentData() is None
    assert all(not b.isEnabled() for b in view.choice_strips["ignition"].buttons.values())
    view.choice_strips["ignition"].choose("RUN")
    assert view.apply_mock() is None and view.model.apply_mock() is None
    assert not view.model.history and not view.live_tx_button.isEnabled()
    window.connection_view.mode_combo.setCurrentText("Mock")
    view.ignition_combo.setCurrentText("OFF")
    assert view.apply_mock()
    window.close()
    assert view.model.closed and view.apply_mock() is None
    fresh = window_factory().driver_control_view
    assert fresh.ignition_combo.currentData() is None and not fresh.model.history
    assert not forbidden_can


@pytest.mark.parametrize("size", [(800,600),(1024,768),(1280,920)])
def test_ignition_actions_navigation_and_labels_accessible(window_factory, qt_app, size):
    # 기존 9페이지/단축키와 스크롤 접근성을 유지한다.
    window = window_factory()
    window.resize(*size)
    window.activateWindow()
    window.raise_()
    assert QTest.qWaitForWindowActive(window, 3000)
    for i in range(9):
        QTest.keyClick(window, getattr(Qt.Key, "Key_" + str(i + 1)), Qt.KeyboardModifier.AltModifier)
        qt_app.processEvents()
        assert window.navigation.currentRow() == i
    window.tabs.setCurrentWidget(window.driver_control_view)
    view = window.driver_control_view
    for widget in (*view.choice_strips["ignition"].buttons.values(), view.accelerator_edit,
                   view.apply_button, view.reset_button, view.live_tx_button, view.history_table):
        expose(window, widget, qt_app)
    assert window.navigation.count() == 9 and (window.width(),window.height()) == size
    assert "UART" in view.approval_label.text() and "pending approval" in view.approval_label.text()


def test_monitor_rx_does_not_imply_ignition_applied(window_factory, forbidden_can):
    # 실제 테스트 프레임 RX와 PC 요청은 독립이며 0x100 ACK 등을 합성하지 않는다.
    window = window_factory()
    view = window.driver_control_view
    view.ignition_combo.setCurrentText("RUN")
    receipt = view.apply_mock()
    for _ in range(2):
        before = window.buffer.total_received
        window.start_monitor()
        wait_until(lambda: window.buffer.total_received > before)
        window.stop_monitor()
        wait_until(lambda: window.worker is None)
        assert view.model.last_accepted == receipt
    window.clear_monitor()
    view.refresh()
    assert "ECU Applied: NOT VERIFIED" in view.observation_label.text()
    assert "UART TX: Disabled" in view.observation_label.text() and not forbidden_can
