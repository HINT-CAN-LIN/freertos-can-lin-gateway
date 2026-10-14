"""Windows Test Automation Native Smoke. Mock/Fake TEST ONLY; 물리 CAN TX 없음."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from pc_diagnostic.gui.automation import AssertionSpec, RunnerState, fixture_path
from pc_diagnostic.gui.window import MainWindow
from gui_native_smoke import wait_until, NATIVE_WAIT_MS


def click(button):
    # Native 창에서도 실제 활성 UI를 클릭한다.
    assert button.isEnabled(), button.text()
    QTest.mouseClick(button, Qt.MouseButton.LeftButton)


def choose(view, kind):
    # Catalog의 exact contract를 선택한다.
    scenario = next(item for item in view.runner.scenarios if item.kind == kind)
    view.scenario_combo.setCurrentIndex(view.scenario_combo.findData(scenario.scenario_id))
    return scenario


def main():
    # 증적은 호출자가 지정한 새 시험 경로에만 만든다. 사용자 수동 확인과는 별개다.
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    root = Path(args.output_dir)
    assert root.is_dir()
    workspace = root/"temporary-workspace"
    workspace.mkdir(exist_ok=False)
    app = QApplication([])
    assert app.platformName() == "windows"
    window = MainWindow()
    view = window.automation_view
    outcomes = []
    all_streams = []
    try:
        window.show()
        assert QTest.qWaitForWindowExposed(window, NATIVE_WAIT_MS)
        window.tabs.setCurrentWidget(view)
        assert window.load_dbc(fixture_path())
        view.folder_edit.setText(str(workspace))  # native 시험자가 명시적으로 지정한 경로
        parent_settings = window.connection_view.raw_values()
        for item in view.runner.scenarios:
            choose(view,item.kind)
            click(view.run_button)
            assert not view.run_button.isEnabled() and view.cancel_button.isEnabled()
            wait_until(lambda: not view.runner.active)
            result = view.runner.result
            assert result.state is RunnerState.PASSED, (item.scenario_id,result.error,result.assertions)
            assert all(check.passed is True for check in result.assertions)
            assert all(view.table.item(row,3).text()=="PASS" for row in range(view.table.rowCount()))
            assert window.connection_view.raw_values()==parent_settings and not window.worker
            assert not list(workspace.iterdir())
            outcomes.append({"scenario":item.scenario_id,"state":result.state.value,
                             "assertions":len(result.assertions),"hardware":result.hardware})
            all_streams.extend(view.runner.streams)
        assert window.grab().save(str(root/"automation-passed.png"))
        # 기대값만 변경하여 GUI의 FAIL/expected/actual/reason 표시를 별도로 검증한다.
        original = choose(view,"raw")
        wrong = replace(original,assertions=(AssertionSpec("raw_frames",()),*original.assertions[1:]))
        view.runner.scenarios=tuple(wrong if item is original else item for item in view.runner.scenarios)
        click(view.run_button)
        wait_until(lambda:not view.runner.active)
        assert view.runner.state is RunnerState.FAILED and view.table.item(0,3).text()=="FAIL"
        assert view.table.item(0,1).text()=="()" and view.table.item(0,2).text()!="()"
        assert window.grab().save(str(root/"automation-failed.png"))
        all_streams.extend(view.runner.streams)
        view.runner.scenarios=tuple(original if item is wrong else item for item in view.runner.scenarios)
        click(view.clear_button)
        assert view.runner.state is RunnerState.IDLE and view.table.rowCount()==0
        # 사용자 Mock 수신/Logging 중에도 독립 시험은 사용자 worker/writer를 중지하지 않는다.
        window.start_monitor()
        wait_until(lambda:window.receiver_running() and window.table.rowCount()>0)
        worker=window.worker
        window.logging_view.set_output_path(root/"user-mock.jsonl")
        window.logging_view.start_recording()
        wait_until(lambda:window.logging_session.snapshot().written>0)
        before=window.logging_session.snapshot().written
        choose(view,"graph")
        click(view.run_button)
        wait_until(lambda:not view.runner.active)
        assert view.runner.state is RunnerState.PASSED and window.worker is worker
        wait_until(lambda:window.logging_session.snapshot().written>before)
        assert window.logging_session.snapshot().active
        all_streams.extend(view.runner.streams)
        window.stop_monitor()
        wait_until(lambda:window.worker is None and not window.logging_session.snapshot().active
                   and window.connection_view.mode_combo.isEnabled())
        window.connection_view.mode_combo.setCurrentText("Live")
        assert not view.run_button.isEnabled()
        view.run_scenario()
        assert view.runner.state is RunnerState.ERROR and not view.runner.streams
        window.connection_view.mode_combo.setCurrentText("Mock")
        # Cancel은 미실행 assertion을 PASS로 만들지 않으며 종료도 같은 cleanup 경로를 사용한다.
        choose(view,"raw")
        click(view.run_button)
        click(view.cancel_button)
        wait_until(lambda:not view.runner.active)
        assert view.runner.state is RunnerState.CANCELLED
        assert all(check.passed is None for check in view.runner.result.assertions)
        all_streams.extend(view.runner.streams)
        click(view.run_button)
        assert not window.close()
        wait_until(lambda:not view.runner.active and not window.isVisible())
        assert view.runner.state is RunnerState.CANCELLED and view._closed
        all_streams.extend(view.runner.streams)
        assert all(stream.send_calls==0 and stream.shutdown_calls==1 and stream.closed.is_set() for stream in all_streams)
        assert not view.runner.timer.isActive() and not list(workspace.iterdir())
        print(json.dumps({"platform":"windows","scenarios":outcomes,
                          "expected_mismatch":"FAILED","cancel_close":"CANCELLED",
                          "user_receiver_logger":"preserved","actual_live":"BLOCKED",
                          "application_tx":sum(stream.send_calls for stream in all_streams),
                          "resources_released":True,"hardware":"NOT VERIFIED"},ensure_ascii=False))
    finally:
        # assertion 실패 시에도 active thread를 방치하지 않고 bounded event 처리를 수행한다.
        if view.runner.active:
            view.runner.cancel()
            wait_until(lambda:not view.runner.active)
        window.stop_monitor()
        wait_until(lambda:window.worker is None and not window.logging_session.snapshot().active)
        window.close()
        window.deleteLater()
        app.processEvents()


if __name__ == "__main__":
    main()
