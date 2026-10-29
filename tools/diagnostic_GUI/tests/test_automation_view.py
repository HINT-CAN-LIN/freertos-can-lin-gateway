"""Mock Automation 화면 회귀. 실제 ECU/CANable 검증이 아니다."""
from dataclasses import replace
import pytest
pytest.importorskip("PySide6", reason="install .[gui]")
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from pc_diagnostic.gui.automation import AssertionSpec, RunnerState
from test_gui import qt_app, window_factory, wait_until
from test_scenario_runner import automation_window, scenario_id


def click(button):
    # UI 활성 조건을 먼저 확인하여 직접 함수 호출만으로 화면 검증을 우회하지 않는다.
    assert button.isEnabled()
    QTest.mouseClick(button, Qt.MouseButton.LeftButton)


def choose(view, kind):
    # 고정 Catalog ID를 exact match로 선택한다.
    view.scenario_combo.setCurrentIndex(view.scenario_combo.findData(scenario_id(kind)))


def test_tab_catalog_and_expected_preview(window_factory):
    # 기존 여섯 탭 순서를 유지하고 시험 입력/기대값/Hardware 구분을 표시한다.
    window = window_factory()
    view = window.automation_view
    assert window.tabs.indexOf(view) == 6
    assert window.tabs.tabText(6) == "Test Automation"
    assert view.scenario_combo.count() == 11
    choose(view, "decode")
    preview = view.description.toPlainText()
    assert "0x651 STD" in preview and "0x651 EXT" in preview
    assert "Measurement" in preview and "-10.0" in preview and "515" in preview
    assert "TEST ONLY" in preview and "explicitly load" in preview
    assert view.table.rowCount() == 0 and "IDLE" in view.state_label.text()


def test_run_result_details_and_clear_using_buttons(automation_window):
    # UI 버튼과 관측 테이블의 actual/expected를 검사하며 Clear는 사용자 CAN 상태를 지우지 않는다.
    window = automation_window
    view = window.automation_view
    window.tabs.setCurrentWidget(view)
    choose(view, "decode")
    parent = window.decode_session.session_id
    click(view.run_button)
    assert not view.run_button.isEnabled() and view.cancel_button.isEnabled()
    assert not view.clear_button.isEnabled() and not view.scenario_combo.isEnabled()
    assert not window.connection_view.mode_combo.isEnabled()
    assert not window.dbc_button.isEnabled()
    window.tabs.setCurrentIndex(0)
    wait_until(lambda: not view.runner.active)
    window.tabs.setCurrentWidget(view)
    assert "PASSED" in view.state_label.text() and "End: pending" not in view.time_label.text()
    assert view.table.rowCount() == len(view.runner.result.assertions)
    assert all(view.table.item(row,3).text() == "PASS" for row in range(view.table.rowCount()))
    assert any("Measurement" in view.table.item(row,2).text() for row in range(view.table.rowCount()))
    assert window.decode_session.session_id == parent
    click(view.clear_button)
    assert view.table.rowCount() == 0 and view.runner.state is RunnerState.IDLE
    assert window.decode_session.session_id == parent


def test_cancel_ui_marks_assertions_not_evaluated(automation_window):
    # 취소 후 미관측 항목을 PASS로 오인하지 않고 새 실행을 허용한다.
    view = automation_window.automation_view
    choose(view, "raw")
    click(view.run_button)
    click(view.cancel_button)
    wait_until(lambda: not view.runner.active)
    assert "CANCELLED" in view.state_label.text()
    assert all(view.table.item(row,3).text() == "NOT EVALUATED" for row in range(view.table.rowCount()))
    assert view.run_button.isEnabled() and not view.cancel_button.isEnabled()


def test_gui_failure_shows_expected_actual_and_reason(automation_window):
    # 기대값 변조로 FAIL 표시를 검증하며 입력/실제 결과를 기대값으로 복사하지 않는다.
    view = automation_window.automation_view
    choose(view, "raw")
    original = next(item for item in view.runner.scenarios if item.kind == "raw")
    wrong = replace(original, assertions=(AssertionSpec("raw_frames",()), *original.assertions[1:]))
    view.runner.scenarios = tuple(wrong if item is original else item for item in view.runner.scenarios)
    click(view.run_button)
    wait_until(lambda: not view.runner.active)
    assert "FAILED" in view.state_label.text()
    assert view.table.item(0,1).text() == "()"
    assert view.table.item(0,2).text() != "()"
    assert view.table.item(0,3).text() == "FAIL"
    assert "differ" in view.table.item(0,4).text()


def test_no_dbc_error_is_visible_without_running_receiver(window_factory):
    # DBC 미로드는 ERROR와 설치/선택 원인으로 표시하며 receiver를 만들지 않는다.
    view = window_factory().automation_view
    choose(view, "decode")
    click(view.run_button)
    assert view.runner.state is RunnerState.ERROR and view.runner.session is None
    assert "No DBC" in view.error_label.text()
    assert all(view.table.item(row,3).text() == "NOT EVALUATED" for row in range(view.table.rowCount()))


def test_live_source_blocks_ui_and_direct_run(automation_window, monkeypatch):
    # 실제 backend 생성/송신은 호출되지 않으며 direct slot도 Live guard를 우회하지 못한다.
    import can
    def forbidden_bus(*args, **kwargs):
        raise AssertionError("Actual CAN backend must never be opened")
    monkeypatch.setattr(can, "Bus", forbidden_bus)
    window = automation_window
    view = window.automation_view
    window.connection_view.mode_combo.setCurrentText("Live")
    assert not view.run_button.isEnabled() and "Live Source BLOCKED" in view.state_label.text()
    settings = window.connection_view.raw_values()
    view.run_scenario()
    assert view.runner.state is RunnerState.ERROR and not view.runner.streams
    assert "BLOCKED" in view.error_label.text() and window.connection_view.raw_values() == settings


@pytest.mark.parametrize("selected", ["", "selected"])
def test_logging_folder_is_explicit_and_dialog_protects_run(automation_window, tmp_path, monkeypatch, selected):
    # 폴더 dialog의 nested event loop 중 실행 금지, Cancel이면 파일을 만들지 않는다.
    from pc_diagnostic.gui import automation_view
    view = automation_window.automation_view
    choose(view, "jsonl")
    def select_folder(*args):
        assert view._selecting_folder and not view.run_button.isEnabled()
        view.run_scenario()
        assert not view.runner.active and view.runner.result is None
        return str(tmp_path) if selected else ""
    monkeypatch.setattr(automation_view.QFileDialog, "getExistingDirectory", select_folder)
    click(view.folder_button)
    assert view.folder_edit.isReadOnly() and not list(tmp_path.iterdir())
    if selected:
        click(view.run_button)
        wait_until(lambda: not view.runner.active)
        assert view.runner.state is RunnerState.PASSED and not list(tmp_path.iterdir())
    else:
        assert not view.folder_edit.text() and view.runner.result is None


def test_closing_gui_during_run_cancels_and_cleans(automation_window):
    # 첫 close는 asynchronous cleanup을 기다리고 완료 신호 이후 창을 닫는다.
    window = automation_window
    view = window.automation_view
    choose(view, "raw")
    click(view.run_button)
    assert not window.close()
    wait_until(lambda: not view.runner.active and not window.isVisible())
    assert view.runner.state is RunnerState.CANCELLED
    assert view._closed and not view.runner.timer.isActive()
    assert all(stream.closed.is_set() and stream.shutdown_calls == 1 for stream in view.runner.streams)
