"""CAN을 사용하지 않는 운전자 요청/Mock 수락 계약 검증."""
import pytest
from pc_diagnostic.gui.driver_input import (
    DriverInputModel, DriverInputs, InputState, MockReceipt, HISTORY_CAPACITY,
    APPROVAL_STATUS, ECU_RESPONSE_STATUS)
from pc_diagnostic.gui.driver_adapter import MockDriverAdapter


@pytest.mark.parametrize("inputs", [
    DriverInputs(accelerator=0), DriverInputs(accelerator=100),
    DriverInputs(accelerator=12.5, brake=True), DriverInputs(brake=False),
    *[DriverInputs(gear=g) for g in ("P", "N", "D", "R")],
    DriverInputs(window="OPEN"), DriverInputs(window="CLOSE"),
    DriverInputs(light="ON"), DriverInputs(light="OFF"),
])
def test_explicit_inputs_only_reach_memory_adapter(inputs):
    # VCU 우선순위를 적용하지 않고 명시한 입력을 그대로 수락한다.
    adapter = MockDriverAdapter()
    model = DriverInputModel(adapter_factory=lambda: adapter, clock=lambda: 123.5)
    assert model.state == InputState.NOT_CONFIGURED and model.last_accepted is None
    assert model.stage(inputs) and not adapter.receipts
    assert model.state == InputState.MOCK_INPUT and not model.applied
    receipt = model.apply_mock()
    assert receipt.command.inputs == inputs and receipt.command.timestamp == 123.5
    assert model.state == InputState.MOCK_ACCEPTED and model.applied
    assert adapter.receipts == (receipt,)
    assert model.approval_status == APPROVAL_STATUS
    assert model.ecu_response_status == ECU_RESPONSE_STATUS


@pytest.mark.parametrize("field,value", [
    ("accelerator", -0.01), ("accelerator", 100.01), ("accelerator", True),
    ("accelerator", "12"), ("accelerator", float("nan")), ("accelerator", float("inf")),
    ("accelerator", float("-inf")), ("accelerator", 10 ** 1000),
    ("brake", 0), ("brake", "ON"), ("gear", "S"), ("gear", 2),
    ("window", "STOP"), ("window", "UP"), ("light", "HEAD_LAMP"),
])
def test_invalid_input_cannot_reapply_previous_accepted_request(field, value):
    # 실패 후 Apply가 이전 draft를 재사용하는 결함을 검출한다.
    adapter = MockDriverAdapter()
    model = DriverInputModel(adapter_factory=lambda: adapter)
    assert model.stage(DriverInputs(gear="D")) and model.apply_mock()
    assert not model.stage(DriverInputs(**{field: value}))
    assert model.state == InputState.INPUT_ERROR and model.error
    assert model.draft is None and not model.applied
    assert model.apply_mock() is None and len(adapter.receipts) == 1
    assert model.ecu_response_status == ECU_RESPONSE_STATUS


def test_empty_and_wrong_model_input_are_rejected():
    # 미설정은 0/OFF와 다르며 잘못된 타입을 수락하지 않는다.
    model = DriverInputModel()
    for inputs in (None, "not a model", DriverInputs()):
        assert not model.stage(inputs)
        assert model.apply_mock() is None and model.last_accepted is None


def test_repeat_and_simultaneous_inputs_keep_facts_with_bounded_history():
    # 반복 요청은 개별 PC 번호를 받으며 CAN 주기/Alive나 Brake 우선순위가 아니다.
    adapter = MockDriverAdapter()
    model = DriverInputModel(adapter_factory=lambda: adapter)
    inputs = DriverInputs(accelerator=80, brake=True, gear="R", window="OPEN", light="ON")
    model.stage(inputs)
    commands = [model.apply_mock().command for _ in range(HISTORY_CAPACITY * 2)]
    assert all(c.inputs == inputs for c in commands)
    assert len({c.sequence for c in commands}) == len(commands)
    assert len(model.history) == HISTORY_CAPACITY and len(adapter.receipts) == HISTORY_CAPACITY


@pytest.mark.parametrize("failure", ["open", "accept", "receipt", "reject"])
def test_adapter_failure_is_visible_without_retry_or_ecu_success(failure):
    # 실제 CAN/ECU가 아닌 메모리 장애를 주입한다.
    class Broken(MockDriverAdapter):
        def accept(self, command):
            # 수락 실패/잘못된 수락 결과도 정상 응답으로 표시하지 않는다.
            if failure == "accept":
                raise RuntimeError("test memory error")
            if failure == "receipt":
                return object()
            return MockReceipt(command, accepted=False)
    attempts = []
    def factory():
        # 실패 시 자동 재시도 횟수가 늘어나는지 검출한다.
        attempts.append(True)
        if failure == "open":
            raise RuntimeError("test adapter creation error")
        return Broken()
    model = DriverInputModel(adapter_factory=factory)
    model.stage(DriverInputs(window="CLOSE"))
    assert model.apply_mock() is None
    assert len(attempts) == 1 and model.state == InputState.INPUT_ERROR
    assert not model.applied and model.last_accepted is None
    assert model.ecu_response_status == ECU_RESPONSE_STATUS
    assert model.reset() and model.state == InputState.NOT_CONFIGURED


def test_live_guard_blocks_adapter_creation_and_direct_calls():
    # UI와 독립된 모델 경계에서도 Live를 차단한다.
    calls = []
    model = DriverInputModel(adapter_factory=lambda: calls.append("opened"))
    model.stage(DriverInputs(brake=True))
    model.set_source("Live", "Live TEST ONLY")
    for _ in range(3):
        assert not model.stage(DriverInputs(light="ON"))
        assert model.apply_mock() is None
        model.reject_input("invalid")
    assert calls == [] and model.state == InputState.LIVE_BLOCKED
    assert model.draft is None and model.last_accepted is None


def test_source_change_reset_close_release_and_recovery():
    # 출처 변경은 과거 결과/미처리 입력을 초기화하고 종료 후 입력을 차단한다.
    adapters = []
    def factory():
        # Reset 후 새로운 메모리 Adapter를 만든다.
        adapter = MockDriverAdapter()
        adapters.append(adapter)
        return adapter
    model = DriverInputModel(adapter_factory=factory)
    model.stage(DriverInputs(light="ON"))
    model.apply_mock()
    model.stage(DriverInputs(light="OFF"))
    model.set_source("Live", "Live A")
    assert adapters[0].closed and not model.history and model.draft is None
    assert model.last_accepted is None
    model.set_source("Mock", "Mock B / TEST ONLY")
    model.stage(DriverInputs(window="OPEN"))
    receipt = model.apply_mock()
    assert receipt.command.source == "Mock B / TEST ONLY"
    assert len(adapters) == 2
    assert model.close() and adapters[1].closed
    assert model.close() and model.apply_mock() is None
    assert not model.stage(DriverInputs(gear="D"))


def test_reentrant_apply_does_not_enqueue_duplicate_or_mutate_draft():
    # Adapter 처리 중 재입력을 주입해 무한 재진입/중복 전달을 검출한다.
    nested = []
    class Reentrant(MockDriverAdapter):
        def accept(self, command):
            # GUI 이벤트 루프를 돌리지 않고도 모델의 재입력 차단을 검증한다.
            nested.append(model.apply_mock())
            assert not model.stage(DriverInputs(gear="R"))
            return super().accept(command)
    adapter = Reentrant()
    model = DriverInputModel(adapter_factory=lambda: adapter)
    model.stage(DriverInputs(gear="D"))
    assert model.apply_mock().command.inputs.gear == "D"
    assert nested == [None] and len(adapter.receipts) == 1


@pytest.mark.parametrize("clock_value", [None, float("nan"), True])
def test_bad_clock_cannot_create_accepted_command(clock_value):
    # 생성 시각 오류는 인증/통신 문제가 아니라 PC 입력 오류로 분리한다.
    calls = []
    model = DriverInputModel(clock=lambda: clock_value, adapter_factory=lambda: calls.append(1))
    assert not model.stage(DriverInputs(brake=True))
    assert model.apply_mock() is None and not calls


def test_cleanup_failure_is_reported_and_original_error_detail_is_not_leaked():
    # 메모리 Adapter 해제 오류의 타입은 보여주되 내부 경로/토큰은 노출하지 않는다.
    class Broken(MockDriverAdapter):
        def shutdown(self):
            raise RuntimeError("secret-local-path-token")
    adapter = Broken()
    model = DriverInputModel(adapter_factory=lambda: adapter)
    model.stage(DriverInputs(brake=False))
    model.apply_mock()
    assert not model.reset()
    assert model.state == InputState.INPUT_ERROR and "RuntimeError" in model.error
    assert "secret-local-path-token" not in model.error
    assert model.draft is None and model.last_accepted is None
