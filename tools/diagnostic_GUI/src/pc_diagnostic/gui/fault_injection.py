"""GUI 독립 Fault TEST ONLY facade. 기존 Automation catalog/Runner를 참조하며 송신하지 않는다."""
from collections import deque
from dataclasses import dataclass
from itertools import islice
from .automation import (MAX_RESULTS, MAX_SCENARIO_FRAMES, RunnerState, Scenario, RunResult,
                         validate_catalog, validate_fixture, fixture_path)
from ..frame import RawCanFrame

SUPPORTED_KINDS = ("fault", "decode-error", "source")
SCENARIO_SCOPE = {
    "fault": ("Fault History infrastructure", "반복 TEST ONLY 관측/Status Unknown. ECU Fault 발생·복구 시험 아님"),
    "decode-error": ("Decode failure observation", "길이 오류 Raw 보존/빈 실패 Signal. Fault Code 생성 아님"),
    "source": ("Isolated Source reset", "격리 창 Source 전환 시 History/Cache 초기화. ECU Recovery 아님"),
}


@dataclass(frozen=True, slots=True)
class FaultTestRecord:
    result: RunResult
    observations: tuple
    context_note: str = ""


class FaultInjectionModel:
    def __init__(self, owner, runner):
        # 기존11개 정의/Runner를 그대로 공유하고 자신의 결과 소유권만 관리한다.
        if runner.owner is not owner:
            raise ValueError("Fault test requires the owner's existing Automation Runner")
        self.owner, self.runner = owner, runner
        self.history = deque(maxlen=MAX_RESULTS)
        self.selected_id = next((s.scenario_id for s in self.scenarios if s.kind == "fault"), None)
        self.state, self.error = RunnerState.IDLE, ""
        self.result, self.observations = None, ()
        self._owned = False
        self._aborting = False
        self._context = None

    @property
    def scenarios(self):
        # 새 Scenario/ID를 생성하지 않는다. 기존 Runner 객체의 실제 항목만 반환한다.
        return tuple(s for s in self.runner.scenarios if s.kind in SUPPORTED_KINDS)

    @property
    def active(self):
        # 타 Automation 실행을 자신의 실행으로 표시하지 않는다.
        return self._owned and self.runner.active

    def select(self, scenario_id):
        # 잘못된 선택 뒤 이전 Scenario를 의도치 않게 실행하지 않는다.
        if self.runner.active:
            return False
        selected = next((s for s in self.scenarios if s.scenario_id == scenario_id), None)
        if selected is None:
            self.selected_id = None
            self.reject("NOT SUPPORTED: choose an existing Fault-related TEST ONLY Scenario")
            return False
        self.selected_id = selected.scenario_id
        self.error = ""
        return True

    def reject(self, reason):
        # 준비 실패는 실제 관측/Assertion PASS를 생성하지 않는다.
        self.state, self.error = RunnerState.ERROR, str(reason)
        self.result, self.observations = None, ()

    def validate_input(self):
        # UI 비활성화와 별개로 실제 owner Source/DBC/고정 입력 계약을 검사한다.
        if self.owner.connection_view.mode_combo.currentText() != "Mock" or self.owner._closing:
            raise ValueError("BLOCKED: user Live Source/closing; only isolated Mock/Fake tests are allowed")
        if self.owner._selecting_dbc:
            raise ValueError("BLOCKED: DBC selection is in progress")
        selected = next((s for s in self.scenarios if s.scenario_id == self.selected_id), None)
        if not isinstance(selected, Scenario):
            raise ValueError("NOT SUPPORTED: no selected Scenario")
        validate_catalog((selected,))
        if any(not isinstance(frame, RawCanFrame) or not frame.is_rx for frame in selected.input_frames):
            raise ValueError("Invalid TEST ONLY RX input")
        validate_fixture(fixture_path())
        if not self.owner.decode_session.loader.is_loaded:
            raise ValueError("No DBC: explicitly load unchanged tests/fixtures/test_only.dbc")
        validate_fixture(self.owner.decode_session.loader.status.path)
        return selected

    def run(self):
        # 중복/다른 Automation 작업을 교체하지 않고 기존 Runner의 독립 Live guard도 유지한다.
        if self.runner.active:
            return False
        try:
            selected = self.validate_input()
        except Exception as exc:
            self.reject(f"{type(exc).__name__}: {exc}")
            return False
        self.state, self.error, self.result = RunnerState.RUNNING, "", None
        self.observations = ()
        self._context = self.owner.connection_view.raw_values()
        self._owned, self._aborting = True, False
        started = self.runner.start(selected.scenario_id)
        if not started:
            self._owned = False
            self.reject("Runner is busy; no Fault test started")
        self.observe()
        return started

    def observe(self, *_):
        # 기존 Runner.changed/Qt tick에서만 호출한다. 새 Timer/Thread는 없다.
        if not self._owned:
            return
        if self.runner.active:
            if not self._aborting and (self.owner.connection_view.raw_values() != self._context
                                       or self.owner.connection_view.mode_combo.currentText() != "Mock"):
                self._aborting = True
                self.error = "Source changed: isolated Fault test cancelled; no physical TX"
                self.runner.cancel()
            child = self.runner.session
            if child is not None:
                self.observations = tuple(islice(child.fault_monitor_view.model.entries, MAX_SCENARIO_FRAMES))
            self.state = self.runner.state
            if self.runner.result is not None:
                self.result = self.runner.result  # cleanup 미완료 ERROR도 숨기지 않는다.
            return
        self.result = self.runner.result
        if self.result is None:
            self.reject("Runner ended without a test result")
        else:
            self.state = self.result.state
            self.error = self.error or self.result.error
            self.history.append(FaultTestRecord(self.result, self.observations, self.error))
        self._owned = False

    def cancel(self):
        # 이 패널이 시작한 격리 세션만 취소한다. 사용자/타 Automation 세션에는 접근하지 않는다.
        if not self.active:
            return False
        return self.runner.cancel()

    def reset(self):
        # Test Result만 비우며 Fault Monitor History/ECU 상태/공유 Runner 결과는 지우지 않는다.
        if self.runner.active:
            return False
        self.history.clear()
        self.result, self.observations = None, ()
        self.state, self.error = RunnerState.IDLE, ""
        return True
