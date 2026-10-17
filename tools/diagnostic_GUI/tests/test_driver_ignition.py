"""Ignition은 PC 내부 문자열 요청이다. CAN Encoding/VCU 상태 전이를 검증하지 않는다."""
import pytest
from pc_diagnostic.gui.driver_input import DriverInputs, DriverInputModel, InputState, IGNITION_CHOICES
from pc_diagnostic.gui.driver_adapter import MockDriverAdapter


@pytest.mark.parametrize("ignition", IGNITION_CHOICES)
def test_ignition_apply_records_exact_memory_command(ignition):
    # 이전 위치 인자와 전체 입력은 그대로이며 새 필드만 마지막에 덧붙는다.
    adapter = MockDriverAdapter()
    model = DriverInputModel(adapter_factory=lambda: adapter, clock=lambda: 123.5)
    inputs = DriverInputs(40, True, "R", "OPEN", "ON", ignition=ignition)
    assert model.stage(inputs) and not adapter.receipts
    receipt = model.apply_mock()
    assert receipt.command.inputs == inputs
    assert receipt.command.inputs.ignition == ignition
    assert adapter.receipts == (receipt,)
    assert [r.action for r in model.history] == ["edit", "request", "Mock result"]
    assert all(r.inputs == inputs for r in model.history)
    assert model.ecu_response_status == "ECU Response Not Verified"


@pytest.mark.parametrize("invalid", ["off", "READY", "DRIVE", "IGN_OFF", "", 0, 1, True, [], {}])
def test_invalid_ignition_rejects_previous_draft(invalid):
    # 잘못된 Ignition 뒤 Apply가 과거 요청을 다시 전달하면 실패한다.
    adapter = MockDriverAdapter()
    model = DriverInputModel(adapter_factory=lambda: adapter)
    assert model.stage(DriverInputs(ignition="ON")) and model.apply_mock()
    assert not model.stage(DriverInputs(ignition=invalid))
    assert model.state == InputState.INPUT_ERROR and model.draft is None
    assert model.apply_mock() is None and len(adapter.receipts) == 1


def test_unset_initial_reset_is_not_off_command_and_preserves_legacy_positions():
    # 승인 근거 없는 OFF 기본값이나 reset 송신을 만들지 않는다.
    model = DriverInputModel()
    assert DriverInputs().ignition is None and model.draft is None
    assert DriverInputs(25, False, "P", "CLOSE", "OFF").ignition is None
    assert model.stage(DriverInputs(ignition="RUN")) and model.apply_mock()
    adapter = model._adapter
    assert model.reset() and adapter.closed
    assert model.draft is None and model.last_accepted is None and not model.history
    assert model.state == InputState.NOT_CONFIGURED
    assert not model.stage(DriverInputs())


@pytest.mark.parametrize("ignition", IGNITION_CHOICES)
def test_no_unapproved_interlock_or_state_transition(ignition):
    # 동시 Brake/Accelerator/Gear를 기록할 뿐 Torque나 ECU 상태를 계산하지 않는다.
    model = DriverInputModel()
    inputs = DriverInputs(accelerator=100, brake=True, gear="R", ignition=ignition)
    assert model.stage(inputs)
    assert model.apply_mock().command.inputs == inputs
    assert not hasattr(model, "vcu_state") and not hasattr(model, "torque_request")


def test_source_and_close_clear_ignition_and_live_direct_model_is_blocked():
    # Live 선택 이후에는 새 Adapter 생성조차 허용하지 않는다.
    model = DriverInputModel()
    assert model.stage(DriverInputs(ignition="ON")) and model.apply_mock()
    adapter = model._adapter
    assert model.set_source("Live", "Live TEST ONLY") and adapter.closed
    model._adapter_factory = lambda: pytest.fail("Live adapter creation forbidden")
    for value in IGNITION_CHOICES:
        assert not model.stage(DriverInputs(ignition=value))
        assert model.apply_mock() is None
    assert not model.history and model.last_accepted is None
    assert model.set_source("Mock", "Mock NEW / TEST ONLY")
    model._adapter_factory = MockDriverAdapter
    assert model.stage(DriverInputs(ignition="OFF"))
    assert model.apply_mock().command.source == "Mock NEW / TEST ONLY"
    assert model.close() and not model.stage(DriverInputs(ignition="RUN"))
