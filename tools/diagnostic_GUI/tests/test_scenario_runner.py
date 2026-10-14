"""Mock/Fake TEST ONLY Runner 회귀. 기존 GUI/Worker 경로와 오류/정리 정책 검증."""
from dataclasses import replace
from pathlib import Path
from threading import Event
import pytest
pytest.importorskip("PySide6",reason="install .[gui]")
from PySide6.QtTest import QTest
from shiboken6 import isValid
from pc_diagnostic.interfaces import CanInterfaceError
from pc_diagnostic.gui.automation import (AssertionSpec, MAX_RESULTS, RunnerState, ScenarioInput,
                                         catalog, fixture_path)
from pc_diagnostic.gui.scenario_runner import ScenarioRunner
from pc_diagnostic.logger import read_jsonl
from test_gui import qt_app, window_factory, wait_until


def scenario_id(kind):
    # 고정 Catalog의 exact ID만 선택한다.
    return next(item.scenario_id for item in catalog() if item.kind==kind)


@pytest.fixture
def automation_window(window_factory,synthetic_dbc_path):
    # 각 시험의 사용자 session은 독립 Mock이며 DBC는 시험자가 명시적으로 로드한다.
    window=window_factory()
    assert window.load_dbc(synthetic_dbc_path)
    yield window
    runner=window.automation_view.runner
    if runner.active:
        runner.cleanup_limit=2
        runner.cancel()
        wait_until(lambda:not runner.active)


@pytest.mark.parametrize("kind", [item.kind for item in catalog()])
def test_each_catalog_scenario_uses_pipeline_and_all_assertions(automation_window,tmp_path,kind):
    # Frame 주입만으로 통과하지 않고 원래 GUI table/Cache/View/파일 결과를 각각 확인한다.
    window=automation_window
    runner=window.automation_view.runner
    parent=(window.connection_view.raw_values(),window.decode_session.session_id,window.table.rowCount())
    states=[]
    runner.changed.connect(lambda:states.append((runner.state,runner.phase)))
    assert runner.start(scenario_id(kind),work_dir=tmp_path)
    child=runner.session
    assert child is not window and child.automation_view is None
    child_timers=(child.timer,child.age_timer,child.graph_view.timer,child.logging_view.timer)
    wait_until(lambda:not runner.active)
    assert runner.state is RunnerState.PASSED and runner.result.cleanup_complete
    assert runner.result.assertions and all(item.passed is True for item in runner.result.assertions)
    assert runner.result.hardware=="NOT VERIFIED" and runner.result.ended_at>=runner.result.started_at
    assert any(state is RunnerState.RUNNING for state,phase in states)
    assert (window.connection_view.raw_values(),window.decode_session.session_id,window.table.rowCount())==parent
    assert all(stream.send_calls==0 and stream.shutdown_calls==1 for stream in runner.streams)
    # deleteLater가 처리된 QObject도 해제 성공이다. 삭제된 C++ 객체를 다시 조회하지 않는다.
    assert not runner.timer.isActive()
    assert all(not isValid(timer) or not timer.isActive() for timer in child_timers)
    assert not list(tmp_path.iterdir())


def test_duplicate_start_cancel_and_new_run_do_not_reuse_results(automation_window):
    # 중복 Worker를 만들지 않고 취소된 assertion을 PASS로 표시하지 않는다.
    runner=automation_window.automation_view.runner
    assert runner.start(scenario_id("raw"))
    child=runner.session
    assert not runner.start(scenario_id("decode")) and runner.session is child
    assert runner.cancel()
    wait_until(lambda:not runner.active)
    assert runner.state is RunnerState.CANCELLED and runner.result.cancelled
    assert all(item.passed is None for item in runner.result.assertions)
    previous=runner.result
    assert runner.start(scenario_id("raw"))
    assert runner.result is None and runner.session is not child
    wait_until(lambda:not runner.active)
    assert runner.state is RunnerState.PASSED and runner.result is not previous
    assert runner.clear_results() and runner.state is RunnerState.IDLE and not runner.results


def test_wrong_expected_value_is_failed_not_self_validated(automation_window):
    # 기대값만 변조해 실제 Raw table과 비교하는 실패 검출력을 확인한다.
    runner=automation_window.automation_view.runner
    item=next(item for item in runner.scenarios if item.kind=="raw")
    bad=replace(item,assertions=(AssertionSpec("raw_frames",()),*item.assertions[1:]))
    runner.scenarios=(bad,)
    runner.start(bad.scenario_id)
    wait_until(lambda:not runner.active)
    assert runner.state is RunnerState.FAILED
    failure=runner.result.assertions[0]
    assert failure.expected==() and failure.actual and failure.passed is False
    assert failure.reason=="Expected and actual differ"


def test_changed_actual_transport_order_causes_failed(automation_window):
    # 입력 계획과 실제 수신 순서를 다르게 만들어 expected를 actual로 복사하지 않는지 확인한다.
    runner=automation_window.automation_view.runner
    class ReversedInput(ScenarioInput):
        def __init__(self,frames):
            # 동일 기존 fixture frames만 순서를 바꾼다. 새 ID/Signal 정의 없음.
            super().__init__(tuple(reversed(frames)))
    runner._stream_factory=ReversedInput
    runner.start(scenario_id("raw"))
    wait_until(lambda:not runner.active)
    assert runner.state is RunnerState.FAILED
    assert any(item.key=="raw_frames" and item.passed is False for item in runner.result.assertions)


def test_signal_mismatch_in_actual_decode_is_failed(automation_window,monkeypatch):
    # 기존 codec 호출 결과 경계를 모의해 독립 golden Signal 비교가 실패하는지 확인한다.
    runner=automation_window.automation_view.runner
    runner.start(scenario_id("decode"))
    codec=runner.session.decode_session.service.codec
    original=codec.decode
    def altered(frame):
        # 제품 Decode 구현을 바꾸지 않고 시험의 오류 주입에만 사용한다.
        result=original(frame)
        if result.message_name=="TestOnlySample":
            result=replace(result,signals={**result.signals,"Measurement":0.0})
        return result
    monkeypatch.setattr(codec,"decode",altered)
    wait_until(lambda:not runner.active)
    assert runner.state is RunnerState.FAILED
    signal=next(item for item in runner.result.assertions if item.key=="signals")
    assert signal.expected!=signal.actual and signal.passed is False


def test_no_dbc_and_wrong_dbc_are_error_before_worker(window_factory,tmp_path):
    # DBC 미로드/Production/변경된 fixture를 test_only로 조용히 대체하지 않는다.
    window=window_factory()
    runner=window.automation_view.runner
    runner.start(scenario_id("decode"))
    assert runner.state is RunnerState.ERROR and "No DBC" in runner.result.error and not runner.active
    changed=tmp_path/"changed.dbc"
    changed.write_bytes(fixture_path().read_bytes()+b"\n")
    window.load_dbc(changed)
    before=window.decode_session.loader.status.path
    runner.start(scenario_id("cache"))
    assert runner.state is RunnerState.ERROR and "Unsupported DBC" in runner.result.error
    assert window.decode_session.loader.status.path==before and runner.session is None


def test_real_live_parent_blocks_all_injection_and_bus_calls(automation_window,monkeypatch):
    # 실제 Live 설정만 선택해도 실행을 차단하며 Bus 생성/send를 호출하지 않는다.
    import can
    window=automation_window
    runner=window.automation_view.runner
    monkeypatch.setattr(can,"Bus",lambda *args,**kwargs:pytest.fail("physical Bus opened"))
    called=[]
    runner._stream_factory=lambda frames:called.append(frames)
    window.connection_view.mode_combo.setCurrentText("Live")
    settings=window.connection_view.raw_values()
    runner.start(scenario_id("raw"))
    assert runner.state is RunnerState.ERROR and "BLOCKED" in runner.result.error
    assert not called and runner.session is None and window.worker is None
    assert window.connection_view.raw_values()==settings


def test_running_primary_mock_logger_and_cache_remain_independent(automation_window,tmp_path):
    # 사용자 수신/Logging을 자동 중지하거나 새 Source로 전환하지 않는다.
    window=automation_window
    window.start_monitor()
    wait_until(lambda:window.table.rowCount()>=2)
    user_log=tmp_path/"user.jsonl"
    window.logging_view.set_output_path(user_log)
    window.logging_view.start_recording()
    wait_until(lambda:window.logging_session.snapshot().written>=1)
    primary=window.worker
    writer=window.logging_session._thread
    previous=window.logging_session.snapshot().written
    runner=window.automation_view.runner
    runner.start(scenario_id("graph"))
    wait_until(lambda:not runner.active)
    assert runner.state is RunnerState.PASSED and window.worker is primary and primary.isRunning()
    assert writer.is_alive() and window.connection_view.mode_combo.currentText()=="Mock"
    wait_until(lambda:window.logging_session.snapshot().written>previous)
    assert all(message.raw_frame.channel=="DEMO/TEST ONLY" for message in window.decode_session.service.cache.snapshot().values())
    window.stop_monitor()
    wait_until(lambda:window.worker is None and not window.logging_session.snapshot().active)
    assert len(list(read_jsonl(user_log)))==window.logging_session.snapshot().written


def test_source_and_dbc_edits_are_locked_only_during_automation(automation_window,synthetic_dbc_path):
    # GUI Source 전환/direct setter/DBC reload는 active 시험을 오염시키지 않는다.
    window=automation_window
    runner=window.automation_view.runner
    settings=window.connection_view.raw_values()
    generation=window.decode_session.session_id
    runner.start(scenario_id("raw"))
    assert not window.connection_view.mode_combo.isEnabled() and not window.dbc_button.isEnabled()
    window.connection_view.mode_combo.setCurrentText("Live")
    assert window.connection_view.raw_values()==settings
    assert not window.load_dbc(synthetic_dbc_path) and window.decode_session.session_id==generation
    wait_until(lambda:not runner.active)
    assert window.connection_view.mode_combo.isEnabled() and window.dbc_button.isEnabled()


@pytest.mark.parametrize("failure",["open","receive","shutdown"])
def test_mock_transport_errors_and_shutdown_are_error_not_passed(automation_window,failure):
    # 준비/수신/해제 오류는 Cause를 보존하고 사용자 세션은 유지한다.
    runner=automation_window.automation_view.runner
    if failure=="open":
        def broken(frames):
            # 시험용 factory 오류, 실제 장치 초기화 아님.
            raise CanInterfaceError("TEST ONLY input not ready")
        runner._stream_factory=broken
    else:
        class BrokenInput(ScenarioInput):
            def recv(self,timeout=None):
                # 잘못된 실제 관측을 정상 assertion으로 대체하지 않는다.
                if failure=="receive":
                    raise CanInterfaceError("TEST ONLY receive failed")
                return super().recv(timeout)
            def shutdown(self):
                # 미확인 release 상태를 성공으로 과대 보고하지 않는다.
                super().shutdown()
                if failure=="shutdown":
                    raise CanInterfaceError("TEST ONLY shutdown failed")
        runner._stream_factory=BrokenInput
    runner.start(scenario_id("raw"))
    wait_until(lambda:not runner.active)
    assert runner.state is RunnerState.ERROR and runner.result.error and runner.result.cleanup_complete
    assert automation_window.worker is None and automation_window.connection_view.mode_combo.currentText()=="Mock"
    if failure=="shutdown":
        check=next(item for item in runner.result.assertions if item.key=="resources_released")
        assert check.passed is False


def test_missing_observations_are_error_not_injection_pass(automation_window,monkeypatch):
    # frame이 주입됐더라도 관측점이 불완전하면 PC 실행 제한으로 ERROR 처리한다.
    runner=automation_window.automation_view.runner
    runner.run_limit=.2
    monkeypatch.setattr("pc_diagnostic.gui.scenario_runner.capture_observations",lambda child:())
    runner.start(scenario_id("raw"))
    wait_until(lambda:not runner.active)
    assert runner.state is RunnerState.ERROR and "execution limit" in runner.result.error
    assert not any(item.key=="raw_frames" and item.passed for item in runner.result.assertions)


def test_writer_open_failure_preserves_error_and_cleans_owned_temp(automation_window,tmp_path):
    # 실제 디스크 고갈/ACL 검증이 아닌 logger factory 오류 모의이다.
    runner=automation_window.automation_view.runner
    marker=tmp_path/"user-marker.txt"
    marker.write_text("preserve",encoding="utf-8")
    runner.start(scenario_id("jsonl"),work_dir=tmp_path)
    def failed_logger(*args,**kwargs):
        # 파일 open 실패를 기다림 성공/무손실로 보고하지 않는다.
        raise OSError("TEST ONLY logger open failure")
    runner.session.logging_session._logger_factory=failed_logger
    wait_until(lambda:not runner.active)
    assert runner.state is RunnerState.ERROR and "logger open failure" in runner.result.error
    assert list(tmp_path.iterdir())==[marker] and marker.read_text(encoding="utf-8")=="preserve"


def test_cleanup_timeout_retains_resources_and_allows_explicit_retry(automation_window):
    # 비협조적 recv를 시험 모의해 timeout 후 active QThread 파괴/무한 timer를 방지한다.
    runner=automation_window.automation_view.runner
    entered,release=Event(),Event()
    class SlowInput(ScenarioInput):
        def recv(self,timeout=None):
            # 잘못된 backend 계약을 모의하며 test finally에서 반드시 반환시킨다.
            entered.set()
            assert release.wait(2),"test release not delivered"
            return None
    runner._stream_factory=SlowInput
    runner.cleanup_limit=.05
    try:
        runner.start(scenario_id("raw"))
        wait_until(entered.is_set)
        child=runner.session
        runner.cancel()
        wait_until(lambda:runner.state is RunnerState.ERROR and not runner.timer.isActive())
        assert runner.active and runner.session is child and not runner.result.cleanup_complete
        assert not runner.clear_results() and not runner.start(scenario_id("raw"))
        release.set()
        runner.cleanup_limit=2
        runner.cancel()
        wait_until(lambda:not runner.active)
        assert runner.state is RunnerState.ERROR and runner.result.cleanup_complete
    finally:
        release.set()
        if runner.active:
            runner.cleanup_limit=2
            runner.cancel()
            wait_until(lambda:not runner.active)


def test_close_cancels_automation_then_retries_parent_close(automation_window):
    # Parent Close는 hidden worker/writer 해제 후 진행하며 기존 사용자 종료 계약을 유지한다.
    window=automation_window
    runner=window.automation_view.runner
    runner.start(scenario_id("raw"))
    assert not window.close()
    wait_until(lambda:not runner.active and not window.isVisible())
    assert runner.state is RunnerState.CANCELLED and not runner.timer.isActive()
    assert window.worker is None


def test_results_are_bounded_and_clear_does_not_delete_user_data(automation_window,tmp_path):
    # 메모리 결과만 지우며 report 자동 저장이나 기존 파일 삭제 없음.
    runner=automation_window.automation_view.runner
    marker=tmp_path/"existing.txt"
    marker.write_text("keep",encoding="utf-8")
    for _ in range(MAX_RESULTS+2):
        runner.start("unknown-id")
    assert len(runner.results)==MAX_RESULTS and runner.state is RunnerState.ERROR
    assert runner.clear_results() and not runner.results and runner.result is None
    assert marker.read_text(encoding="utf-8")=="keep"


def test_logging_requires_explicit_workspace(automation_window):
    # 일반 CAN Logger 경로를 자동으로 가져오거나 임시 파일을 무단 생성하지 않는다.
    runner=automation_window.automation_view.runner
    runner.start(scenario_id("csv"))
    assert runner.state is RunnerState.ERROR and "explicit writable test folder" in runner.result.error
    assert runner.session is None and not runner.active


def test_cancel_during_preparation_cleans_new_logging_workspace(automation_window,tmp_path):
    # PREPARING의 동기 상태 signal에서 취소돼도 새 시험 임시 경로를 남기지 않는다.
    runner=automation_window.automation_view.runner
    def cancel_preparing():
        # Qt slot 재진입 경계를 검증한다. 아직 Receiver/Writer는 만들지 않았다.
        if runner.phase=="PREPARING" and not runner._cancelled:
            runner.cancel()
    runner.changed.connect(cancel_preparing)
    assert runner.start(scenario_id("csv"),work_dir=tmp_path)
    assert runner.state is RunnerState.CANCELLED and not runner.active
    assert runner.session is None and not runner.streams
    assert not list(tmp_path.iterdir())
