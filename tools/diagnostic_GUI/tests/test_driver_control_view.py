"""Mock/Live Driver Control Qt 검증. 실제 CANable/ECU 검증이 아니다."""
import pytest
pytest.importorskip("PySide6", reason="install .[gui] for GUI tests")
from PySide6.QtCore import Qt
from shiboken6 import isValid
from PySide6.QtTest import QTest
from test_gui import qt_app, window_factory, wait_until
from pc_diagnostic.gui.driver_input import DriverInputModel, InputState, HISTORY_CAPACITY
from pc_diagnostic.gui.driver_adapter import MockDriverAdapter
from pc_diagnostic.gui.driver_control_view import DriverControlView
from pc_diagnostic.interfaces import MockCanInterface, PythonCanInterface

CLICK = Qt.MouseButton.LeftButton


def test_panel_initial_state_does_not_require_receiver_or_dbc(window_factory):
    # Receiver 미실행/DBC 미로드여도 Mock 입력만 처리할 수 있다.
    window = window_factory()
    view = window.driver_control_view
    assert window.tabs.tabText(window.tabs.indexOf(view)) == "Driver Control"
    assert view.model.state == InputState.NOT_CONFIGURED
    assert not view.live_tx_button.isEnabled() and view.apply_button.isEnabled()
    assert "Awaiting Interface Approval" in view.approval_label.text()
    assert "ECU Response Not Verified" in view.ecu_label.text()
    assert "No Data" in view.torque_label.text()
    assert window.worker is None
    view.accelerator_edit.setText("25.5")
    assert view.model.state == InputState.MOCK_INPUT and not view.model.applied
    QTest.mouseClick(view.apply_button, CLICK)
    assert view.model.applied and view.model.last_accepted.command.inputs.accelerator == 25.5
    assert window.worker is None and window.buffer.total_received == 0
    assert window.table.rowCount() == 0 and not window.decode_session.loader.is_loaded


@pytest.mark.parametrize("text", ["oops", "-1", "101", "nan", "inf", "True"])
def test_numeric_failure_cannot_resubmit_previous_input(window_factory, text):
    # 이전 수락 이후의 잘못된 편집이 새 Mock 요청으로 처리되면 실패한다.
    view = window_factory().driver_control_view
    view.accelerator_edit.setText("50")
    view.apply_mock()
    previous = view.model.last_accepted.command.sequence
    view.accelerator_edit.setText(text)
    assert view.model.state == InputState.INPUT_ERROR
    assert not view.model.applied and view.error_label.text()
    QTest.mouseClick(view.apply_button, CLICK)
    assert view.model.last_accepted.command.sequence == previous
    assert view.model.draft is None


def test_all_controls_repeat_and_reset_without_can_send(window_factory, monkeypatch):
    # 기존 Sender/Bus/Adapter 전송 경계를 trap으로 감시한다.
    import can
    from pc_diagnostic import sender
    calls = []
    def forbidden(*args, **kwargs):
        # Driver 테스트 중 CAN 생성/송신 호출은 1회라도 실패한다.
        calls.append((args, kwargs))
        raise AssertionError("Driver must not create/send CAN frames")
    monkeypatch.setattr(can, "Bus", forbidden)
    monkeypatch.setattr(can.BusABC, "send", forbidden)
    monkeypatch.setattr(MockCanInterface, "send", forbidden)
    monkeypatch.setattr(PythonCanInterface, "send", forbidden)
    monkeypatch.setattr(sender.RawCanSender, "send", forbidden)
    window = window_factory()
    view = window.driver_control_view
    view.accelerator_slider.setValue(60)
    view.brake_combo.setCurrentText("ON")
    for gear in ("P", "N", "D", "R"):
        view.gear_combo.setCurrentText(gear)
        for button, field, value in (
            (view.window_open_button, "window", "OPEN"), (view.window_close_button, "window", "CLOSE"),
            (view.light_on_button, "light", "ON"), (view.light_off_button, "light", "OFF"),
        ):
            for _ in range(2):
                QTest.mouseClick(button, CLICK)
                assert not view.model.applied
                QTest.mouseClick(view.apply_button, CLICK)
                inputs = view.model.last_accepted.command.inputs
                assert getattr(inputs, field) == value
                assert inputs.accelerator == 60 and inputs.brake is True and inputs.gear == gear
    assert calls == [] and len(view.model.history) <= HISTORY_CAPACITY
    assert view.history_table.rowCount() == len(view.model.history)
    assert "ECU Response Not Verified" in view.ecu_label.text()
    adapter = view.model._adapter
    QTest.mouseClick(view.reset_button, CLICK)
    assert adapter.closed and view.model.state == InputState.NOT_CONFIGURED
    assert not view.model.history and view.history_table.rowCount() == 0
    assert view.accelerator_edit.text() == "" and view.gear_combo.currentData() is None


def test_live_source_discards_mock_and_direct_slots_remain_blocked(window_factory, monkeypatch):
    # disabled 버튼 외에도 직접 Slot 호출 시 Adapter/CAN 개방이 없어야 한다.
    import can
    calls = []
    def forbidden(*args, **kwargs):
        # 실제 transport factory까지 감시하며 물리 연결은 시도하지 않는다.
        calls.append(True)
        raise AssertionError("No transport access")
    monkeypatch.setattr(can, "Bus", forbidden)
    monkeypatch.setattr(can.BusABC, "send", forbidden)
    window = window_factory()
    window._live_interface_factory = forbidden
    view = window.driver_control_view
    view.gear_combo.setCurrentText("D")
    view.apply_mock()
    old_adapter = view.model._adapter
    view.light_combo.setCurrentText("ON")  # 미적용 draft도 폐기 대상이다.
    window.connection_view.mode_combo.setCurrentText("Live")
    assert view.model.mode == "Live" and view.model.state == InputState.LIVE_BLOCKED
    assert old_adapter.closed and view.model.draft is None and view.model.last_accepted is None
    assert not view.model.history and view.accelerator_edit.text() == ""
    view.model._adapter_factory = forbidden
    for _ in range(3):
        assert view.apply_mock() is None and view.model.apply_mock() is None
        view.choose_body(view.window_combo, "OPEN")
        QTest.mouseClick(view.live_tx_button, CLICK)
    assert calls == [] and not view.apply_button.isEnabled()
    assert "Live TX Blocked" in view.state_label.text()
    window.connection_view.mode_combo.setCurrentText("Mock")
    view.model._adapter_factory = MockDriverAdapter
    assert view.model.state == InputState.NOT_CONFIGURED and view.apply_button.isEnabled()
    view.light_combo.setCurrentText("OFF")
    assert view.apply_mock() and view.model.last_accepted.command.source.startswith("Mock")


def test_adapter_error_is_visible_and_reset_recovers(window_factory):
    # CAN 실패로 오인하지 않고 메모리 Adapter 오류를 표시한다.
    window = window_factory()
    class Broken(MockDriverAdapter):
        def accept(self, command):
            raise RuntimeError("test memory failure")
    window.driver_control_view.model._adapter_factory = Broken
    view = window.driver_control_view
    view.window_combo.setCurrentText("CLOSE")
    assert view.apply_mock() is None
    assert "RuntimeError" in view.error_label.text() and view.model.state == InputState.INPUT_ERROR
    assert "ECU Response Not Verified" in view.ecu_label.text()
    view.reset_inputs()
    view.model._adapter_factory = MockDriverAdapter
    view.window_combo.setCurrentText("OPEN")
    assert view.apply_mock()


def test_start_stop_clear_and_close_keep_requests_separate_from_rx(window_factory):
    # PC 입력 이력은 Raw/CAN Logger 데이터와 분리되며 Receiver 재실행과 독립적이다.
    window = window_factory()
    view = window.driver_control_view
    view.gear_combo.setCurrentText("R")
    receipt = view.apply_mock()
    adapter = view.model._adapter
    for _ in range(3):
        before = window.buffer.total_received
        window.start_monitor()
        worker = window.worker
        wait_until(lambda: window.buffer.total_received > before)
        window.stop_monitor()
        wait_until(lambda: window.worker is None)
        assert (not isValid(worker) or not worker.isRunning()) and view.model.last_accepted == receipt
    window.clear_monitor()
    assert view.model.last_accepted == receipt
    assert window.close() and adapter.closed and view.model.closed
    assert view.apply_mock() is None and view.model.last_accepted is None


def test_driver_input_does_not_mutate_observation_graph_fault_or_log(window_factory):
    # Mock 결과를 가상 ECU 신호로 관측 화면에 넣는 결함을 검출한다.
    window = window_factory()
    assert window.table.rowCount() == 0
    before = window.logging_session.snapshot()
    view = window.driver_control_view
    view.light_combo.setCurrentText("ON")
    assert view.apply_mock()
    assert window.table.rowCount() == 0 and window.buffer.total_received == 0
    assert window.logging_session.snapshot() == before
    assert window.tabs.tabText(4) == "Signal Graph" and window.tabs.tabText(5) == "Fault Monitor"
    assert window.signal_table.rowCount() == 0 and window.cache_table.rowCount() == 0
