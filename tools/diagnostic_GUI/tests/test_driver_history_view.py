"""Driver Input History 전체 값/표시 보존 회귀 테스트. CAN 송신은 없다."""
import pytest

pytest.importorskip("PySide6", reason="install .[gui]")
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView

from test_gui import qt_app, window_factory
from pc_diagnostic.gui.driver_control_view import (
    HISTORY_INPUTS_COLUMN, HISTORY_ROW_HEIGHT, format_pc_local_timestamp, input_summary,
)
from pc_diagnostic.gui.driver_input import DriverInputs, HISTORY_CAPACITY


def test_history_preserves_all_inputs_and_shows_selected_record_detail(window_factory):
    # Model, 표, Tooltip과 상세 패널이 동일한 전체 입력 snapshot을 사용해야 한다.
    window = window_factory()
    view = window.driver_control_view
    expected = DriverInputs(53.12345678901234, True, "D", "OPEN", "OFF", "ON")
    view.ignition_combo.setCurrentText(expected.ignition)
    view.accelerator_edit.setText(str(expected.accelerator))
    view.brake_combo.setCurrentText("ON")
    view.gear_combo.setCurrentText(expected.gear)
    view.window_combo.setCurrentText(expected.window)
    view.light_combo.setCurrentText(expected.light)

    receipt = view.apply_mock()
    assert receipt is not None and receipt.command.inputs == expected
    history = view.model.history
    request_index, request = next((index, record) for index, record in enumerate(history)
                                  if record.action == "request")
    result_index, result = next((index, record) for index, record in enumerate(history)
                                if record.action == "Mock result")
    assert request.inputs == expected and result.inputs == expected
    assert len(history) <= HISTORY_CAPACITY

    expected_text = input_summary(expected)
    item = view.history_table.item(result_index, HISTORY_INPUTS_COLUMN)
    assert item.text() == expected_text
    assert item.toolTip() == expected_text
    for field_value in ("Ignition=ON", "Accelerator=53.12345678901234%", "Brake=ON",
                        "Gear=D", "Window=OPEN", "Light=OFF"):
        assert field_value in item.text()

    view.history_table.selectRow(request_index)
    detail = view.history_detail_text.toPlainText()
    assert "Source: Mock / DEMO / TEST ONLY" in detail
    assert "Action: request" in detail and "State: Mock Input" in detail
    assert all(field_value in detail for field_value in (
        "Ignition=ON", "Accelerator=53.12345678901234%", "Brake=ON",
        "Gear=D", "Window=OPEN", "Light=OFF"))
    assert "Mock result is not an ECU response" in detail
    assert view.history_table.item(request_index, 0).text() == format_pc_local_timestamp(request.timestamp)
    assert f"Unix timestamp: {request.timestamp!r}" in view.history_table.item(request_index, 0).toolTip()
    assert "ECU Response Not Verified" in view.ecu_label.text()


def test_history_long_input_text_and_resizable_column_layout(window_factory):
    # 열 너비는 사용자가 조절할 수 있고 Qt의 좁은 열 생략 모드는 유지한다.
    window = window_factory()
    view = window.driver_control_view
    view.ignition_combo.setCurrentText("RUN")
    view.accelerator_edit.setText("53.12345678901234")
    view.brake_combo.setCurrentText("OFF")
    view.gear_combo.setCurrentText("P")
    view.window_combo.setCurrentText("CLOSE")
    view.light_combo.setCurrentText("ON")
    view.apply_mock()

    header = view.history_table.horizontalHeader()
    assert header.sectionResizeMode(HISTORY_INPUTS_COLUMN) == QHeaderView.ResizeMode.Interactive
    assert view.history_table.wordWrap()
    assert view.history_table.textElideMode() == Qt.TextElideMode.ElideRight
    latest_row = view.history_table.rowCount() - 1
    assert view.history_table.rowHeight(latest_row) >= HISTORY_ROW_HEIGHT
    summary = view.history_table.item(latest_row, HISTORY_INPUTS_COLUMN).text()
    assert summary.count("\n") == 2 and len(summary) > 80
    assert "Accelerator=53.12345678901234%" in summary
    view.history_table.setColumnWidth(HISTORY_INPUTS_COLUMN, 820)
    assert view.history_table.columnWidth(HISTORY_INPUTS_COLUMN) == 820
