"""Fault TEST UI의 실제 기존 Runner 통합 시험. 실제 CAN/ECU Fault 시험 아님."""
from dataclasses import replace
import json
import pytest
pytest.importorskip("PySide6", reason="install .[gui]")
from PySide6.QtCore import Qt, QThread, QSignalBlocker
from PySide6.QtTest import QTest
from shiboken6 import isValid
from pc_diagnostic.gui.automation import RunnerState, AssertionSpec, ScenarioInput
from pc_diagnostic.gui.demo import make_demo_frame
from pc_diagnostic.gui.fault_injection import SUPPORTED_KINDS
from pc_diagnostic.interfaces import CanInterfaceError, MockCanInterface, PythonCanInterface
from test_gui import qt_app, window_factory, wait_until
from test_scenario_runner import automation_window
from test_fault_monitor_view import select_fault_source, feed
from test_graph_view import select_graph
from test_fault_history import REPOSITORY_DBC, configured, fault_frame


def show_test(window, kind="fault"):
    # 기존 Fault Monitor 안의 패널을 열고 기존 Catalog 항목을 exact ID로 선택한다.
    view=window.fault_injection_view
    window.tabs.setCurrentWidget(window.fault_monitor_view)
    window.fault_injection_section.set_expanded(True)
    identifier=next(s.scenario_id for s in view.model.scenarios if s.kind==kind)
    view.scenario_combo.setCurrentIndex(view.scenario_combo.findData(identifier))
    window.page_scroll.ensureWidgetVisible(view.run_button)
    return view


@pytest.fixture
def no_physical_can(monkeypatch):
    # 공개 송신/실제 Bus 생성/사용자 live factory 경계를 계수하고 호출되면 실패시킨다.
    calls={"open":0,"send":0}
    def opened(*args,**kwargs):
        # 실제 장치 생성이 자동 시험에 섞이면 즉시 검출한다.
        calls["open"]+=1
        raise AssertionError("No physical CAN open")
    def sent(*args,**kwargs):
        # Mock 송신도 허용하지 않고 FIFO RX 주입만 허용한다.
        calls["send"]+=1
        raise AssertionError("No CAN send")
    monkeypatch.setattr("can.Bus",opened)
    monkeypatch.setattr(PythonCanInterface,"send",sent)
    monkeypatch.setattr(MockCanInterface,"send",sent)
    yield calls
    assert calls=={"open":0,"send":0}


@pytest.mark.parametrize("kind",SUPPORTED_KINDS)
def test_existing_scenario_pass_and_isolated_fault_rows(automation_window,no_physical_can,kind,qt_app):
    # 주입 성공이 아니라 기존 파이프라인 실제 관측/독립 expected 비교의 PASS를 확인한다.
    window=automation_window;view=show_test(window,kind)
    runner=window.automation_view.runner
    assert view.model.runner is runner and len(runner.scenarios)==11 and view.scenario_combo.count()==3
    parent=(window.connection_view.raw_values(),window.decode_session.session_id,window.network_model.generation)
    assert view.run_button.isEnabled()
    QTest.mouseClick(view.run_button,Qt.MouseButton.LeftButton)
    child=runner.session
    assert child is not window and child.fault_injection_view is None
    wait_until(lambda:not runner.active)
    assert view.model.result.state is RunnerState.PASSED
    assert all(a.passed is True for a in view.model.result.assertions)
    assert view.assertion_table.rowCount()==len(view.model.result.assertions)
    assert view.observation_table.rowCount()==2
    assert all(view.observation_table.item(i,3).text()=="Status Unknown" for i in range(2))
    assert all("TEST ONLY" in view.observation_table.item(i,5).text() for i in range(2))
    assert not window.fault_monitor_view.model.entries and not window.table.rowCount()
    assert (window.connection_view.raw_values(),window.decode_session.session_id,window.network_model.generation)==parent
    assert all(s.send_calls==0 and s.shutdown_calls==1 for s in runner.streams)
    assert not runner.timer.isActive() and len(view.model.history)==1


def test_actual_mismatch_is_failed_with_fault_unknown(automation_window,no_physical_can):
    # 입력/관측을 바꾸지 않고 시험용 expected만 다르게 하여 FAIL 검출을 증명한다.
    window=automation_window;view=show_test(window)
    runner=view.model.runner;original=next(s for s in runner.scenarios if s.kind=="fault")
    wrong=replace(original,assertions=tuple(AssertionSpec(a.key,()) if a.key=="fault" else a for a in original.assertions))
    runner.scenarios=tuple(wrong if s is original else s for s in runner.scenarios)
    view.run_test();wait_until(lambda:not runner.active)
    assert view.model.state is RunnerState.FAILED
    failed=next(a for a in view.model.result.assertions if a.key=="fault")
    assert failed.passed is False and failed.actual!=failed.expected
    assert all(e.fault_status=="Status Unknown" for e in view.model.observations)
    assert any(view.assertion_table.item(i,3).text()=="FAIL" for i in range(view.assertion_table.rowCount()))


@pytest.mark.parametrize("mode",["Live","injected-Live"])
def test_live_slot_model_and_runner_bypass_blocked(automation_window,no_physical_can,mode):
    # 숨긴 버튼의 Slot/Model/기존 Runner 직접 호출도 실제 user Source로 차단한다.
    window=automation_window;view=show_test(window)
    if mode=="injected-Live":
        window._live_interface_factory=lambda settings:pytest.fail("user live factory called")
    window.connection_view.mode_combo.setCurrentText("Live")
    assert not view.run_button.isEnabled()
    view.run_test()
    assert not view.model.runner.active and view.model.state is RunnerState.ERROR
    assert not view.model.run()
    runner=view.model.runner
    runner.start(view.scenario_combo.currentData())
    assert runner.session is None and runner.state is RunnerState.ERROR
    assert "BLOCKED" in runner.result.error
    assert not window.driver_control_view.live_tx_button.isEnabled()


def test_missing_dbc_then_old_success_not_reused(window_factory,synthetic_dbc_path):
    # 준비 오류가 이전 PASS 표로 오인되지 않아야 한다.
    window=window_factory();view=show_test(window)
    view.run_test()
    assert view.model.state is RunnerState.ERROR and view.assertion_table.rowCount()==0
    assert window.load_dbc(synthetic_dbc_path)
    view.run_test();wait_until(lambda:not view.model.runner.active)
    assert view.model.state is RunnerState.PASSED
    assert window.load_dbc(REPOSITORY_DBC)
    view.run_test()
    assert view.model.state is RunnerState.ERROR and view.model.result is None
    assert view.assertion_table.rowCount()==0 and view.observation_table.rowCount()==0
    assert "Unsupported DBC" in view.error_label.text()


def test_missing_fixture_and_invalid_raw_input(automation_window,tmp_path,monkeypatch):
    # 원본 Fixture/Source를 수정하지 않고 잘못된 준비 입력만 모의한다.
    window=automation_window;view=show_test(window)
    monkeypatch.setattr("pc_diagnostic.gui.fault_injection.fixture_path",lambda:tmp_path/"missing.dbc")
    view.run_test()
    assert view.model.state is RunnerState.ERROR and view.model.runner.session is None
    monkeypatch.undo()
    runner=view.model.runner;original=next(s for s in runner.scenarios if s.kind=="fault")
    bad=replace(original,input_frames=())
    runner.scenarios=tuple(bad if s is original else s for s in runner.scenarios)
    view.run_test()
    assert view.model.state is RunnerState.ERROR and runner.session is None


def test_duplicate_cancel_reset_and_legacy_busy_are_separate(automation_window):
    # 같은 Runner를 교체하지 않고 자신의 시험만 취소·Reset한다.
    window=automation_window;view=show_test(window);runner=view.model.runner
    view.run_test();child=runner.session
    view.run_test();view.reset_tests()
    assert runner.session is child and not view.reset_button.isEnabled()
    view.cancel_test();wait_until(lambda:not runner.active)
    assert view.model.state is RunnerState.CANCELLED
    assert all(a.passed is None for a in view.model.result.assertions)
    legacy_result=runner.result;legacy_history=tuple(runner.results)
    view.reset_tests()
    assert view.model.state is RunnerState.IDLE and not view.model.history
    assert runner.result is legacy_result and tuple(runner.results)==legacy_history
    runner.start(next(s.scenario_id for s in runner.scenarios if s.kind=="raw"))
    assert not view.run_button.isEnabled() and not view.cancel_button.isEnabled()
    assert not view.model.cancel() and runner.active
    wait_until(lambda:not runner.active)
    assert not view.model.history


def test_forced_source_change_cancels_only_owned_test(automation_window,no_physical_can):
    # UI는 기존 Source lock을 유지하고 강제 프로그램 변경도 시험을 중단한다.
    window=automation_window;view=show_test(window)
    view.run_test()
    assert not window.connection_view.mode_combo.isEnabled()
    # 기존 ConnectionView의 원복 signal까지 우회하는 시험용 변경을 명시적으로 만든다.
    blocker=QSignalBlocker(window.connection_view.mode_combo)
    window.connection_view.mode_combo.setCurrentText("Live")
    del blocker
    view.model.observe()
    wait_until(lambda:not view.model.runner.active)
    assert view.model.state is RunnerState.CANCELLED
    assert "Source changed" in view.model.error and not window.worker
    assert all(a.passed is None for a in view.model.result.assertions)
    assert all(s.shutdown_calls==1 and s.send_calls==0 for s in view.model.runner.streams)


def test_receive_error_is_error_not_pass(automation_window,no_physical_can):
    # 실제 장치가 아니라 기존 ScenarioInput의 recv 실패를 주입한다.
    window=automation_window;view=show_test(window)
    class Broken(ScenarioInput):
        def recv(self,timeout=None):
            # 기존 Worker 예외/해제 경로를 그대로 검증한다.
            raise CanInterfaceError("TEST ONLY input read failure")
    view.model.runner._stream_factory=Broken
    view.run_test();wait_until(lambda:not view.model.runner.active)
    assert view.model.state is RunnerState.ERROR and view.model.result.error
    assert all(s.closed.is_set() for s in view.model.runner.streams)


def test_parent_observations_and_test_history_reset_are_independent(automation_window):
    # 멈춘 사용자 Raw/Cache/Graph/Fault/Network를 동일 snapshot으로 보존한다.
    window=automation_window;select_fault_source(window);graph=select_graph(window)
    feed(window,make_demo_frame(0));window.set_raw_paused(True)
    parent=(tuple(window.fault_monitor_view.model.entries),window.decode_session.service.cache.snapshot(),
            tuple(graph.model.samples),window.network_model.processed_rx,window.table.rowCount())
    view=show_test(window)
    for kind in ("fault","decode-error"):
        view.scenario_combo.setCurrentIndex(view.scenario_combo.findData(next(s.scenario_id for s in view.model.scenarios if s.kind==kind)))
        view.run_test();wait_until(lambda:not view.model.runner.active)
    assert len(view.model.history)==view.history_combo.count()==2
    view.history_combo.setCurrentIndex(0)
    assert view.observation_table.item(1,2).text()=="Observed"
    view.history_combo.setCurrentIndex(1)
    assert view.observation_table.item(1,2).text()=="Decode Error"
    view.reset_tests()
    assert (tuple(window.fault_monitor_view.model.entries),window.decode_session.service.cache.snapshot(),
            tuple(graph.model.samples),window.network_model.processed_rx,window.table.rowCount())==parent
    assert window.raw_paused


def test_user_rx_logging_graph_continue_during_test(automation_window,tmp_path,no_physical_can):
    # 사용자 Mock 수신·파일·Graph를 중단/재사용하지 않고 hidden Fake만 실행한다.
    window=automation_window;graph=select_graph(window);select_fault_source(window)
    window.set_raw_paused(True);window.start_monitor()
    wait_until(lambda:window._processed>=2)
    worker=window.worker
    path=tmp_path/"user.jsonl";window.logging_view.set_output_path(path);window.logging_view.start_recording()
    wait_until(lambda:window.logging_session.snapshot().written>=1)
    before=(window._processed,graph.model.accepted,window.logging_session.snapshot().written)
    view=show_test(window,"source");view.run_test()
    wait_until(lambda:not view.model.runner.active)
    wait_until(lambda:window._processed>before[0] and graph.model.accepted>before[1] and window.logging_session.snapshot().written>before[2])
    assert window.worker is worker and window.receiver_running()
    assert window.raw_paused and window.table.rowCount()==0
    assert view.model.state is RunnerState.PASSED
    assert all(e.frame.channel=="DEMO/TEST ONLY" for e in window.fault_monitor_view.model.entries)
    window.stop_monitor();wait_until(lambda:window.worker is None and not window.logging_session.snapshot().active)
    assert all(json.loads(line)["channel"]=="DEMO/TEST ONLY" for line in path.read_text().splitlines())


def test_close_active_trial_releases_child_and_own_timer(automation_window,no_physical_can):
    # 기존 request_close 경로가 완료된 뒤 parent와 hidden 창을 닫는다.
    window=automation_window;view=show_test(window);view.run_test()
    child=view.model.runner.session
    timers=(child.timer,child.age_timer,child.graph_view.timer,child.logging_view.timer)
    assert not window.close()
    wait_until(lambda:not window.isVisible())
    assert not view.model.runner.active and not view.model.runner.timer.isActive()
    assert view.model.result.state is RunnerState.CANCELLED and view._closed
    assert all(not isValid(t) or not t.isActive() for t in timers)
    view.run_test()
    assert not view.model.runner.active


@pytest.mark.parametrize("size",[(800,600),(1024,768),(1280,920)])
def test_panel_layout_actions_and_navigation(automation_window,qt_app,size):
    # 기존9페이지와 단축키를 보존하고 작은 창에서 버튼 rect 전체를 스크롤 노출한다.
    window=automation_window;window.resize(*size);view=show_test(window)
    qt_app.processEvents()
    assert window.navigation.count()==9 and window.automation_view.scenario_combo.count()==11
    assert "No physical CAN open / TX" in view.policy_label.text() and "Hardware NOT VERIFIED" in view.policy_label.text()
    for button in (view.run_button,view.cancel_button,view.reset_button):
        window.page_scroll.ensureWidgetVisible(button);qt_app.processEvents()
        rect=button.rect();rect.moveTopLeft(button.mapTo(window.page_scroll.viewport(),rect.topLeft()))
        assert window.page_scroll.viewport().rect().contains(rect)
    assert "FaultCode/ECUOffline/RecoveryState/SystemState are absent" in view.description.toPlainText()
    window.navigation.setCurrentRow(8)
    assert window.tabs.currentWidget() is window.automation_view


def test_existing_fault_enum_contract_readonly(automation_window):
    # Production DBC는 단위 검증에서만 읽고 UI 실행 입력으로 채택하지 않는다.
    window=automation_window
    from pc_diagnostic.gui.decode_session import DecodeSession
    session=DecodeSession();session.load(REPOSITORY_DBC)
    model=configured(session);frame=fault_frame(session,code=0,node=1,recovery=0)
    model.record(session.process(frame),session,"Mock / TEST ONLY")
    entry=model.entries[-1]
    assert entry.signals["FaultCode"]==0 and entry.signals["ECUOffline"]==1
    assert entry.choices["ECUOffline"]=="VCU" and entry.choices["RecoveryState"]=="ACTIVE"
    assert entry.fault_status=="Status Unknown"
    assert len(window.automation_view.runner.scenarios)==11


def test_locked_source_attempt_is_restored_without_changing_session(automation_window):
    # 보통 programmatic 변경도 기존 연결 편집기가 복구하므로 실제 Source 변경이 아니다.
    window=automation_window;view=show_test(window);view.run_test()
    assert not window.connection_view.mode_combo.isEnabled()
    window.connection_view.mode_combo.setCurrentText("Live")
    assert window.connection_view.mode_combo.currentText()=="Mock"
    wait_until(lambda:not view.model.runner.active)
    assert view.model.state is RunnerState.PASSED
    assert not view.model.history[-1].context_note


def test_result_headers_remain_readable_after_styling(automation_window,qt_app):
    # 실제 캡처에서 잘린 새 Header 제목을 글꼴 폭/스크롤 계약으로 회귀 검증한다.
    view=show_test(automation_window);qt_app.processEvents()
    for table in (view.assertion_table,view.observation_table):
        metrics=table.horizontalHeader().fontMetrics()
        for column in range(table.columnCount()):
            title=table.horizontalHeaderItem(column).text()
            assert table.columnWidth(column)>=metrics.horizontalAdvance(title)
            assert table.horizontalHeaderItem(column).toolTip()==title
