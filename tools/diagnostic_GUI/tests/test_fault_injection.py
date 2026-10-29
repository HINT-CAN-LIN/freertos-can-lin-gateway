"""Fault TEST facade 단위 시험. 공유 Runner stub로 소유권/입력 guard만 검사한다."""
from dataclasses import replace
from types import SimpleNamespace
import pytest
from pc_diagnostic.gui.automation import catalog, RunnerState, RunResult, MAX_RESULTS
from pc_diagnostic.gui.decode_session import DecodeSession
from pc_diagnostic.gui.fault_injection import FaultInjectionModel
from test_fault_history import REPOSITORY_DBC


class Source:
    def __init__(self):
        # Qt 없이 실제 Source 선택값/설정 snapshot 계약만 제공한다.
        self.mode = "Mock"
        self.channel = ""
        self.mode_combo = SimpleNamespace(currentText=lambda:self.mode)

    def raw_values(self):
        # 호출자에게 가변 설정 객체 자체를 반환하지 않는다.
        return self.mode, self.channel


class StubRunner:
    def __init__(self, owner):
        # 제품 Runner를 대신하지 않는 단위 시험용 상태 제어 도우미다.
        self.owner = owner
        self.scenarios = catalog()
        self.active = False
        self.session = None
        self.state = RunnerState.IDLE
        self.result = None
        self.starts = []
        self.cancels = 0

    def start(self, identifier):
        # 실제 수신/Thread/Bus 없이 facade 전달만 관측한다.
        self.starts.append(identifier)
        self.active = True
        self.state = RunnerState.RUNNING
        self.result = None
        return True

    def cancel(self):
        # 정리 완료 여부를 시험자가 별도로 종료시킨다.
        self.cancels += 1
        return True

    def finish(self, state=RunnerState.PASSED):
        # 실제 Assertion 검증은 별도 기존 Runner 통합 시험에서 수행한다.
        self.active = False
        self.state = state
        self.result = RunResult(self.starts[-1],1,2,state,())


def prepared(path):
    # 명시적 기존 fixture만 로드하고 현재 사용자의 Source 계약을 구성한다.
    owner = SimpleNamespace(connection_view=Source(), decode_session=DecodeSession(),
                            _closing=False, _selecting_dbc=False)
    if path is not None:owner.decode_session.load(path)
    runner = StubRunner(owner)
    return owner, runner, FaultInjectionModel(owner,runner)


def test_catalog_references_existing_three_without_new_ids(synthetic_dbc_path):
    # 기존11개를 바꾸거나 복제하지 않고 객체 identity까지 공유한다.
    owner,runner,model=prepared(synthetic_dbc_path)
    assert len(runner.scenarios)==11 and len(model.scenarios)==3
    assert {s.kind for s in model.scenarios}=={"fault","decode-error","source"}
    assert all(any(s is original for original in runner.scenarios) for s in model.scenarios)
    assert model.selected_id==next(s.scenario_id for s in runner.scenarios if s.kind=="fault")


@pytest.mark.parametrize("identifier",[None,"unknown","HINT48-MOCK-RAW-v1"])
def test_unsupported_selection_never_runs_previous(identifier,synthetic_dbc_path):
    # 잘못된 선택은 이전 유효 ID를 재사용하지 않는다.
    owner,runner,model=prepared(synthetic_dbc_path)
    assert not model.select(identifier) and model.selected_id is None
    assert not model.run() and not runner.starts
    assert model.state is RunnerState.ERROR


@pytest.mark.parametrize("reason",["live","closing","selecting-dbc","no-dbc","wrong-dbc"])
def test_preflight_errors_no_runner_or_bus(reason,synthetic_dbc_path):
    # 버튼과 무관하게 Model 직접 호출에서 실제 현재 조건을 검사한다.
    owner,runner,model=prepared(None if reason=="no-dbc" else REPOSITORY_DBC if reason=="wrong-dbc" else synthetic_dbc_path)
    if reason=="live":owner.connection_view.mode="Live"
    if reason=="closing":owner._closing=True
    if reason=="selecting-dbc":owner._selecting_dbc=True
    assert not model.run() and not runner.starts
    assert model.state is RunnerState.ERROR and model.result is None and model.error


@pytest.mark.parametrize("kind",["empty","not-raw","tx"])
def test_invalid_input_is_rejected(kind,synthetic_dbc_path):
    # 공식 Scenario는 변경하지 않고 단위 시험의 Runner stub만 변조한다.
    owner,runner,model=prepared(synthetic_dbc_path)
    original=next(s for s in runner.scenarios if s.kind=="fault")
    frames=() if kind=="empty" else ("invalid raw",) if kind=="not-raw" else (replace(original.input_frames[0],is_rx=False),)
    bad=replace(original,input_frames=frames)
    runner.scenarios=tuple(bad if s is original else s for s in runner.scenarios)
    assert not model.run() and not runner.starts and model.state is RunnerState.ERROR


def test_shared_busy_cancel_reset_do_not_own_other_run(synthetic_dbc_path):
    # 기존 Automation에서 시작한 실행을 취소/지우지 않는다.
    owner,runner,model=prepared(synthetic_dbc_path)
    runner.active=True
    assert not model.run() and not model.cancel() and not model.reset()
    assert not runner.starts and runner.cancels==0 and not model.active
    runner.active=False
    assert model.reset()


def test_context_change_requests_one_safe_cancel(synthetic_dbc_path):
    # UI를 우회해 설정이 바뀌어도 공유 tick hook에서 한번만 취소한다.
    owner,runner,model=prepared(synthetic_dbc_path)
    assert model.run()
    owner.connection_view.channel="changed"
    model.observe();model.observe()
    assert runner.cancels==1 and model.active and "Source changed" in model.error
    runner.finish(RunnerState.CANCELLED);model.observe()
    assert not model.active and model.history[-1].result.state is RunnerState.CANCELLED
    assert model.history[-1].context_note


def test_bounded_history_reset_does_not_clear_shared_runner(synthetic_dbc_path):
    # Fault TEST history는 기존 RunResult 참조만 유한 보관하고 공통 결과를 지우지 않는다.
    owner,runner,model=prepared(synthetic_dbc_path)
    for _ in range(MAX_RESULTS+2):
        assert model.run()
        runner.finish();model.observe();model.observe()
    assert len(model.history)==MAX_RESULTS
    last=runner.result
    assert model.reset() and model.state is RunnerState.IDLE
    assert not model.history and runner.result is last


def test_runner_owner_binding(synthetic_dbc_path):
    # 다른 창 Runner와의 우발적 결합을 시작 전에 막는다.
    owner,runner,model=prepared(synthetic_dbc_path)
    with pytest.raises(ValueError):FaultInjectionModel(SimpleNamespace(),runner)
