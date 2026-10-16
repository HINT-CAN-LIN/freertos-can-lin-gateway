"""3K-2 표시/접근성 회귀. Mock/TEST ONLY이며 Hardware 검증이 아니다."""
import pytest
pytest.importorskip("PySide6", reason="install .[gui]")
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from pc_diagnostic.gui.demo import make_demo_frame
from pc_diagnostic.gui.window import frame_cells
from pc_diagnostic.gui.ui_components import ElidedLabel
from test_gui import qt_app, window_factory, wait_until
from test_vehicle_view import show_frame

SIZES = ((800, 600), (1024, 768), (1280, 920))


def expose(window, widget, qt_app):
    # 실제 페이지 스크롤로 버튼 중심을 viewport에 노출한다.
    window.page_scroll.ensureWidgetVisible(widget)
    qt_app.processEvents()
    assert window.page_scroll.viewport().rect().contains(
        widget.mapTo(window.page_scroll.viewport(), widget.rect().center()))


@pytest.mark.parametrize("size", SIZES)
def test_compact_header_preserves_content_and_safety(window_factory, qt_app, size):
    # 이전 260px 시작 위치보다 콘텐츠를 확보하면서 상시 안전 표시를 유지한다.
    window = window_factory()
    qt_app.processEvents()
    window.resize(*size)
    qt_app.processEvents()
    assert (window.width(), window.height()) == size
    assert window.page_scroll.mapTo(window, QPoint()).y() < 210
    assert window.page_scroll.viewport().height() >= size[1] - 240
    for widget in (window.start_button, window.stop_button, window.clear_button,
                   window.dbc_button, window.connection_toggle, window.source_badge,
                   window.hardware_badge, window.tx_badge, window.page_title):
        assert widget.isVisible()
        assert window.rect().contains(widget.mapTo(window, widget.rect().center()))
    assert "NOT VERIFIED" in window.hardware_badge.text()
    assert "BLOCKED" in window.tx_badge.text() and "Pending" in window.tx_badge.text()


@pytest.mark.parametrize("row", range(9))
def test_all_pages_actions_accessible_at_small_size(window_factory, qt_app, row):
    # 페이지별 핵심 액션은 기존 Widget 그대로이며 스크롤/접기 후 접근 가능해야 한다.
    window = window_factory()
    qt_app.processEvents()
    window.resize(800, 600)
    window.navigation.setCurrentRow(row)
    qt_app.processEvents()
    page = window.tabs.currentWidget()
    actions = {
        0: (), 1: (window.driver_control_view.apply_button, window.driver_control_view.reset_button,
                   window.driver_control_view.window_open_button, window.driver_control_view.light_on_button),
        2: (window.monitor_filter.search,), 3: (window.vehicle_view.apply_button,),
        4: (window.ecu_view.apply_button,), 5: (window.fault_monitor_view.add_button, window.fault_monitor_view.clear_button),
        6: (window.graph_view.apply_button, window.graph_view.pause_button, window.graph_view.clear_button),
        7: (window.logging_view.choose_button, window.logging_view.start_button),
        8: (window.automation_view.run_button, window.automation_view.cancel_button),
    }
    for widget in actions[row]:
        assert widget.isVisible()
        expose(window, widget, qt_app)
    for section in getattr(page, "ui_sections", ()):
        section.set_expanded(True)
        qt_app.processEvents()
        assert all(not widget.isHidden() for widget in section.widgets)
        section.set_expanded(False)
        qt_app.processEvents()
        assert all(widget.isHidden() for widget in section.widgets)
    assert window.navigation.count() == 9 and window.worker is None


def test_header_details_and_errors_keep_original_text(window_factory, qt_app):
    # 전체 경고/계수를 지우지 않고 새 오류는 빈 Activity 영역을 즉시 펼친다.
    window = window_factory()
    before = [widget.text() for widget in window.header_details.widgets]
    window.header_details.set_expanded(True)
    qt_app.processEvents()
    assert [widget.text() for widget in window.header_details.widgets] == before
    window.header_details.set_expanded(False)
    assert not window.error_area.isVisible()
    window.show_error("TEST ONLY visible shutdown error")
    assert window.activity_section.button.isChecked() and window.error_area.isVisible()
    assert "TEST ONLY visible shutdown error" in window.error_area.toPlainText()


@pytest.mark.parametrize("name,choice", [("brake", "ON"), ("gear", "R"), ("window", "CLOSE"), ("light", "OFF")])
def test_choice_buttons_reuse_validation_and_reset(window_factory, name, choice):
    # 신규 모델 없이 기존 ComboBox/슬롯을 통과하며 Reset의 미설정 상태를 유지한다.
    window = window_factory()
    view = window.driver_control_view
    window.tabs.setCurrentWidget(view)
    strip = view.choice_strips[name]
    strip.buttons[choice].click()
    assert getattr(view, name + "_combo").currentData() == choice
    assert strip.buttons[choice].isChecked()
    assert view.model.last_accepted is None
    view.reset_inputs()
    assert getattr(view, name + "_combo").currentData() is None
    assert not any(button.isChecked() for button in strip.buttons.values())


def test_accelerator_decimal_not_rounded_by_slider(window_factory):
    # 표시용 정수 thumb 동기화가 실제 입력 소수값/Validation을 바꾸면 안 된다.
    view = window_factory().driver_control_view
    view.accelerator_edit.setText("12.5")
    assert view.accelerator_edit.text() == "12.5"
    assert view.model.draft.accelerator == 12.5
    assert view.accelerator_slider.value() == round(12.5)
    view.accelerator_slider.setValue(40)
    assert view.model.draft.accelerator == 40
    view.accelerator_edit.setText("101")
    assert view.model.error
    assert view.error_label.text() == view.model.error
    assert view.apply_mock() is None


def test_live_selection_disables_all_choice_buttons(window_factory):
    # 표시 버튼은 기존 Live/Automation 잠금을 우회할 수 없다.
    window = window_factory()
    window.connection_view.mode_combo.setCurrentText("Live")
    view = window.driver_control_view
    for strip in view.choice_strips.values():
        assert all(not button.isEnabled() for button in strip.buttons.values())
    assert not view.apply_button.isEnabled() and not view.live_tx_button.isEnabled()
    assert view.apply_mock() is None and view.model.last_accepted is None
    assert "LIVE" in window.source_badge.text() and window.worker is None


def test_raw_timestamp_and_selection_are_not_reformatted(window_factory):
    # 자리수/원본 데이터는 바꾸지 않고 폭·폰트·tooltip으로 가독성만 개선한다.
    window = window_factory()
    frame = make_demo_frame(0)
    show_frame(window, frame)
    window.table.selectRow(0)
    assert window.table.item(0, 0).text() == frame_cells(frame)[0]
    assert window.table.columnWidth(0) >= window.table.fontMetrics().horizontalAdvance(frame_cells(frame)[0])
    assert window.selected_observation().frame == frame


def test_long_source_text_preserved_without_minimum_width_growth(window_factory, qt_app):
    # 긴 DBC Message/Signal 표시를 모의하며 CAN/DBC 파일·매핑 데이터는 변경하지 않는다.
    window = window_factory()
    qt_app.processEvents()
    window.resize(800, 600)
    full = "DBC display TEST ONLY / " + "LongMessage_LongSignal_" * 30
    window.dbc_label.setText(full)
    from pc_diagnostic.gui.workspace import refresh_workspace
    refresh_workspace(window)
    qt_app.processEvents()
    assert window.dbc_summary.full_text == full and window.dbc_summary.toolTip() == full
    assert window.width() == 800
    for view in (window.vehicle_view, window.ecu_view, window.graph_view):
        view.message_combo.addItem(full, None)
        view.message_combo.setCurrentIndex(view.message_combo.count() - 1)
        assert view.message_combo.currentText() == full
    label = ElidedLabel()
    label.resize(120, 20)
    label.set_full_text(full)
    assert label.toolTip() == full and label.minimumSizeHint().width() == 0
