"""Windows Fault TEST Native Smoke. 기존 Scenario/Runner, Mock/Fake 전용이며 HIL 아님."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import can
from PySide6.QtCore import Qt, QSignalBlocker
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from shiboken6 import isValid
from pc_diagnostic.gui.window import MainWindow
from pc_diagnostic.gui.automation import RunnerState, AssertionSpec
from pc_diagnostic.interfaces import MockCanInterface, PythonCanInterface
from gui_native_smoke import wait_until, NATIVE_WAIT_MS

SIZES=((800,600),(1024,768),(1280,920))


def main():
    # 지정 외부 폴더와 실제 Windows 창을 사용하되 모든 실제 CAN 경계를 금지한다.
    parser=argparse.ArgumentParser();parser.add_argument("--output-dir",required=True)
    args=parser.parse_args();output=Path(args.output_dir);assert output.is_dir()
    app=QApplication([]);assert app.platformName()=="windows"
    calls={"open":0,"send":0};captures=[];streams=[]
    def forbidden_open(*args,**kwargs):
        # 사용자 factory/실제 Bus 생성은 이 시험에서 허용하지 않는다.
        calls["open"]+=1
        raise AssertionError("No actual CAN open")
    def forbidden_send(*args,**kwargs):
        # Mock send도 금지하고 ScenarioInput의 FIFO RX만 사용한다.
        calls["send"]+=1
        raise AssertionError("No CAN send")
    can.Bus=forbidden_open
    PythonCanInterface.send=forbidden_send
    MockCanInterface.send=forbidden_send
    window=MainWindow(live_interface_factory=forbidden_open)
    runner=window.automation_view.runner;view=window.fault_injection_view
    def settle():
        # 실제 Qt 이벤트와 layout을 처리하고 아래 상태/geometry로 검증한다.
        for _ in range(5):app.processEvents()
    def expose(widget):
        # 작은 창에서도 주요 조작/표 전체가 scroll viewport에 들어와야 한다.
        window.page_scroll.ensureWidgetVisible(widget);settle()
        rect=widget.rect();rect.moveTopLeft(widget.mapTo(window.page_scroll.viewport(),rect.topLeft()))
        assert window.page_scroll.viewport().rect().contains(rect)
    def capture(name):
        # 데이터 합성 시안이 아닌 실제 QWidget 캡처를 저장한다.
        settle();assert window.grab().save(str(output/name));captures.append(name)
    def choose(kind):
        # 기존 Runner catalog 객체의 ID를 그대로 선택한다.
        item=next(s for s in view.model.scenarios if s.kind==kind)
        view.scenario_combo.setCurrentIndex(view.scenario_combo.findData(item.scenario_id))
        return item
    def run(kind):
        # UI 버튼에서 실행하고 기존 실제 관측 assertions와 자원 정리를 기다린다.
        choose(kind);expose(view.run_button)
        assert view.run_button.isEnabled()
        QTest.mouseClick(view.run_button,Qt.MouseButton.LeftButton)
        wait_until(lambda:not runner.active)
        streams.extend(runner.streams)
    try:
        window.show();assert QTest.qWaitForWindowExposed(window,NATIVE_WAIT_MS)
        assert window.load_dbc(Path(__file__).parent/"fixtures/test_only.dbc")
        window.tabs.setCurrentWidget(window.fault_monitor_view)
        window.fault_injection_section.set_expanded(True)
        assert len(runner.scenarios)==11 and view.scenario_combo.count()==3
        assert view.model.runner is runner and window.navigation.count()==9
        # 사용자 Mock 수신/Logging은 trial의 hidden Fake와 동시에 계속돼야 한다.
        window.start_monitor();wait_until(lambda:window._processed>=2)
        parent_worker=window.worker
        window.logging_view.set_output_path(output/"user-raw.jsonl")
        window.logging_view.start_recording();wait_until(lambda:window.logging_session.snapshot().written>=1)
        before=window._processed
        for kind in ("fault","decode-error","source"):
            run(kind)
            assert view.model.state is RunnerState.PASSED
            assert all(a.passed is True for a in view.model.result.assertions)
            assert view.observation_table.rowCount()==2
            assert all(e.fault_status=="Status Unknown" for e in view.model.observations)
            assert not window.fault_monitor_view.model.entries
        wait_until(lambda:window._processed>before)
        assert window.worker is parent_worker and window.logging_session.snapshot().state.value=="Recording"
        window.stop_monitor();wait_until(lambda:window.worker is None and not window.buffer.pending_count)
        assert all(json.loads(line)["channel"]=="DEMO/TEST ONLY" for line in (output/"user-raw.jsonl").read_text().splitlines())
        for width,height in SIZES:
            window.resize(width,height);settle()
            assert (window.width(),window.height())==(width,height)
            for button in (view.run_button,view.cancel_button,view.reset_button):expose(button)
            capture(f"fault-test-actions-{width}x{height}.png")
            expose(view.assertion_table);capture(f"fault-test-assertions-{width}x{height}.png")
            expose(view.observation_table);capture(f"fault-test-history-{width}x{height}.png")
        original=choose("fault")
        wrong=replace(original,assertions=tuple(AssertionSpec(a.key,()) if a.key=="fault" else a for a in original.assertions))
        runner.scenarios=tuple(wrong if s is original else s for s in runner.scenarios)
        run("fault")
        assert view.model.state is RunnerState.FAILED
        runner.scenarios=tuple(original if s is wrong else s for s in runner.scenarios)
        window.resize(1280,920);expose(view.assertion_table);capture("fault-test-assertion-failed.png")
        # 실제 user Live에서는 버튼/Slot/Model 모두 실행을 거부한다.
        window.connection_view.mode_combo.setCurrentText("Live")
        assert not view.run_button.isEnabled()
        view.run_test();assert not view.model.run() and runner.session is None
        assert view.model.state is RunnerState.ERROR and not window.driver_control_view.live_tx_button.isEnabled()
        expose(view.run_button);capture("fault-test-live-blocked.png")
        window.connection_view.mode_combo.setCurrentText("Mock")
        view.run_test()
        # 잠긴 Source 원복 기능까지 시험자가 우회해 실제 변경 시의 취소 방어를 검증한다.
        blocker=QSignalBlocker(window.connection_view.mode_combo)
        window.connection_view.mode_combo.setCurrentText("Live");del blocker
        view.model.observe();wait_until(lambda:not runner.active);streams.extend(runner.streams)
        assert view.model.state is RunnerState.CANCELLED and "Source changed" in view.model.error
        assert all(a.passed is None for a in view.model.result.assertions)
        window.connection_view.mode_combo.setCurrentText("Mock")
        shared=runner.result
        view.reset_tests();assert not view.model.history and runner.result is shared
        window.start_monitor();wait_until(window.receiver_running)
        view.run_test()
        assert not window.close()
        wait_until(lambda:not window.isVisible())
        streams.extend(runner.streams)
        assert not runner.active and not runner.timer.isActive() and view._closed
        assert not window.timer.isActive() and not window.age_timer.isActive()
        assert all(s.shutdown_calls==1 and s.send_calls==0 and s.closed.is_set() for s in streams)
        assert calls=={"open":0,"send":0}
        print(json.dumps({"platform":app.platformName(),"existing_catalog":11,"referenced_scenarios":3,
            "new_runner_thread_timer":0,"pass_fail_cancel_error":True,"user_rx_logging_preserved":True,
            "fault_history_separate_status_unknown":True,"source_guard":True,"live_slot_model_blocked":True,
            "active_close":True,"streams_released":len(streams),"calls":calls,
            "screenshots":captures,"hardware":"NOT VERIFIED","manual":"NOT VERIFIED",
            "actual_fault_status_injection":"Open","event_replay_resync":"Open"}))
    finally:
        # 실패 시에도 사용자/시험 Receiver를 기존 정리 계약으로 반환한다.
        if runner.active:
            runner.cancel();wait_until(lambda:not runner.active)
        window.stop_monitor()
        if window.worker is not None:assert window.worker.wait(NATIVE_WAIT_MS)
        window.logging_session.stop();assert window.logging_session.wait(NATIVE_WAIT_MS/1000)
        window.export_controls.exporter.writer.stop();assert window.export_controls.exporter.wait(NATIVE_WAIT_MS/1000)
        app.processEvents();window.close()
    return 0


if __name__=="__main__":
    raise SystemExit(main())
