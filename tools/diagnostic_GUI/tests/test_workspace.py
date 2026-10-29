"""UI/UX 전용 회귀. 기존 Mock/DBC fixture이며 실제 ECU/Hardware 검증이 아니다."""
from dataclasses import replace
import pytest
pytest.importorskip("PySide6", reason="install .[gui]")
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from pc_diagnostic.gui.demo import make_demo_frame
from pc_diagnostic.gui.theme import DiagnosticDelegate
from pc_diagnostic.logger import RawCanLogger
from test_gui import qt_app, window_factory, wait_until
from test_vehicle_view import select_mapping, show_frame
from test_ecu_observation_view import select_source


def test_dashboard_initial_no_data_without_auto_mapping(window_factory):
    # 수신/DBC/매핑이 없으면 정상 차량 수치나 ECU 정상 상태를 합성하지 않는다.
    window = window_factory()
    dash = window.dashboard_view
    assert dash.cards["connection"][0].text() == "Disconnected"
    assert dash.cards["frames"][0].text() == "Received: 0"
    assert dash.cards["ecu"][0].text() == dash.cards["fault"][0].text() == "No Data"
    assert dash.cards["vehicle"][0].text() == "No Data"
    assert "No DBC" in dash.cards["vehicle"][1].text()
    assert dash.cards["logging"][0].text() == "Idle"
    assert not window.vehicle_view.model.mappings and not window.ecu_view.model.mappings
    assert window.worker is None and "Not Implemented" in dash.scope_label.text()


@pytest.mark.parametrize("row", range(9))
def test_navigation_preserves_existing_views_and_tab_contract(window_factory, row):
    # 새 탐색과 기존 setCurrentWidget이 같은 객체/페이지를 선택해야 한다.
    window = window_factory()
    assert window.tabs.tabText(3) == "Logging" and window.tabs.tabText(6) == "Test Automation"
    window.navigation.setCurrentRow(row)
    item = window.navigation.item(row)
    assert window.tabs.currentIndex() == item.data(Qt.ItemDataRole.UserRole)
    assert window.page_title.text() == item.text()
    window.tabs.setCurrentWidget(window.driver_control_view)
    assert window.navigation.currentItem().text() == "Driver Control"
    assert window.tabs.currentWidget() is window.driver_control_view


def test_navigation_keyboard_and_connection_disclosure(window_factory):
    # 키보드로 페이지와 설정에 접근하며 설정 표시 자체가 Source/Bus를 바꾸지 않는다.
    window = window_factory()
    settings = window.connection_view.raw_values()
    window.navigation.setCurrentRow(0)
    window.navigation.setFocus()
    QTest.keyClick(window.navigation, Qt.Key.Key_Down)
    assert window.tabs.currentWidget() is window.driver_control_view
    QTest.mouseClick(window.connection_toggle, Qt.MouseButton.LeftButton)
    assert window.connection_panel.isVisible()
    QTest.mouseClick(window.connection_toggle, Qt.MouseButton.LeftButton)
    assert not window.connection_panel.isVisible()
    assert window.connection_view.raw_values() == settings and window.worker is None


def test_dashboard_mirrors_cache_observed_and_decode_failure(window_factory, synthetic_dbc_path):
    # 기존 View의 명시 매핑/마지막 정상값/실패 상태가 같은 의미로 요약돼야 한다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    select_mapping(window.vehicle_view)
    select_source(window.ecu_view)
    frame = make_demo_frame(0)
    show_frame(window, frame)
    dash = window.dashboard_view
    assert dash.cards["ecu"][0].text() == "Observed: 1"
    assert dash.cards["ecu"][1].text() == "VCU"
    assert "-10.0 test_unit" in dash.cards["vehicle"][1].text()
    assert "Valid" in dash.cards["vehicle"][1].text()
    good = window.decode_session.service.cache.snapshot()
    show_frame(window, replace(frame, data=b"", dlc=0))
    assert "Decode Error" in dash.cards["vehicle"][1].text()
    assert "-10.0 test_unit" in dash.cards["vehicle"][1].text()
    assert window.decode_session.service.cache.snapshot() == good
    assert dash.cards["fault"][0].text() == "No Data"


def test_dashboard_clear_reload_and_source_do_not_reuse_old_observation(window_factory, synthetic_dbc_path):
    # Clear의 기존 Cache 유지와 Reload/Source 변경의 격리를 구분한다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    select_mapping(window.vehicle_view)
    select_source(window.ecu_view)
    show_frame(window, make_demo_frame(0))
    window.clear_monitor()
    assert window.dashboard_view.cards["frames"][0].text() == "Received: 0"
    assert window.dashboard_view.cards["ecu"][0].text() == "No Data"
    assert "-10.0 test_unit" in window.dashboard_view.cards["vehicle"][1].text()
    window.load_dbc(synthetic_dbc_path)
    wait_until(lambda: "-10.0" not in window.dashboard_view.cards["vehicle"][1].text())
    window.connection_view.mode_combo.setCurrentText("Live")
    assert "LIVE" in window.source_badge.text()
    assert "Live" in window.dashboard_view.source_label.text()
    assert window.dashboard_view.cards["connection"][0].text() == "Disconnected"
    assert not window.driver_control_view.live_tx_button.isEnabled()
    assert not window.driver_control_view.apply_button.isEnabled()
    assert window.driver_control_view.apply_mock() is None and window.worker is None


@pytest.mark.parametrize("filter_kind", ["text", "STD", "EXT", "errors", "no_match"])
def test_raw_filters_only_hide_rows_and_preserve_cache_counts(window_factory, synthetic_dbc_path, filter_kind):
    # 표시 제외와 수신/Decode/Cache 삭제를 혼동하지 않는다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    frames = [make_demo_frame(0), make_demo_frame(1)]
    frames.append(replace(frames[0], data=b"", dlc=0))
    for frame in frames:
        show_frame(window, frame)
    snapshot = window.decode_session.service.cache.snapshot()
    filters = window.monitor_filter
    if filter_kind == "text":
        filters.search.setText("test only")
        expected = 3
    elif filter_kind in ("STD", "EXT"):
        filters.format_combo.setCurrentText(filter_kind)
        expected = 2 if filter_kind == "STD" else 1
    elif filter_kind == "errors":
        filters.errors_only.setChecked(True)
        expected = 1
    else:
        filters.search.setText("no matching displayed data")
        expected = 0
    assert sum(not window.table.isRowHidden(row) for row in range(3)) == expected
    assert window.table.rowCount() == 3 and window.counter_label.text() == "Received: 3"
    assert window.decode_session.service.cache.snapshot() == snapshot
    filters.search.clear()
    filters.format_combo.setCurrentIndex(0)
    filters.errors_only.setChecked(False)
    assert all(not window.table.isRowHidden(row) for row in range(3))


def test_filters_do_not_change_logging_bytes_or_receiver_lifecycle(window_factory, tmp_path):
    # 실제 Mock 수신 sink를 통해 필터 적용 중에도 기존 CLI Logger byte 계약을 확인한다.
    window = window_factory()
    accepted = []
    original = window.logging_session.accept
    def record(frame):
        # 동일 Writer admission에서 실제 수락한 Raw 객체만 비교 대상으로 수집한다.
        result = original(frame)
        if result:
            accepted.append(frame)
        return result
    window.logging_session.accept = record
    window.start_monitor()
    wait_until(window.receiver_running)
    output = tmp_path / "filtered.jsonl"
    window.logging_view.set_output_path(output)
    window.logging_view.start_recording()
    window.monitor_filter.search.setText("hide all displayed rows")
    wait_until(lambda: window.logging_session.snapshot().written >= 2)
    window.stop_monitor()
    wait_until(lambda: window.worker is None and not window.logging_session.snapshot().active)
    reference = tmp_path / "reference.jsonl"
    with RawCanLogger(reference) as logger:
        for frame in accepted:
            logger.write(frame)
    assert accepted and output.read_bytes() == reference.read_bytes()
    window.dashboard_view.refresh()
    assert window.dashboard_view.cards["logging"][0].text() == "Stopped"
    assert f"Logged: {len(accepted)}" in window.dashboard_view.cards["logging"][1].text()
    assert window.table.rowCount() > 0
    assert all(window.table.isRowHidden(row) for row in range(window.table.rowCount()))


@pytest.mark.parametrize("size", [(800, 600), (1024, 768), (1280, 920)])
def test_small_window_scroll_navigation_and_driver_access(window_factory, qt_app, size):
    # 작은 창에서도 스크롤로 실제 입력/차단 상태에 접근하고 기존 객체를 유지한다.
    window = window_factory()
    # show 직후 Qt style/layout polish를 마친 뒤 실제 사용자 크기 변경을 재현한다.
    qt_app.processEvents()
    window.resize(*size)
    window.tabs.setCurrentWidget(window.driver_control_view)
    wait_until(lambda: window.driver_control_view._compact_layout == (size[0] < 1200))
    assert window.width() <= size[0] and window.height() <= size[1]
    view = window.driver_control_view
    window.page_scroll.ensureWidgetVisible(view.live_tx_button)
    wait_until(lambda: window.page_scroll.viewport().rect().contains(
        view.live_tx_button.mapTo(window.page_scroll.viewport(), view.live_tx_button.rect().center())))
    assert not view.live_tx_button.isEnabled()
    window.navigation.setFocus()
    QTest.keyClick(window.navigation, Qt.Key.Key_End)
    assert window.tabs.currentWidget() is window.automation_view


def test_shared_table_style_preserves_values_and_error_access(window_factory):
    # 스타일이 값/메시지를 다시 쓰거나 오류를 숨기지 않는지 검사한다.
    window = window_factory()
    show_frame(window, make_demo_frame(0))
    assert isinstance(window.table.itemDelegate(), DiagnosticDelegate)
    assert "STD" in window.table.item(0, 2).text()
    window.show_error("TEST ONLY receive failure")
    assert window.error_area.isVisible() and "TEST ONLY receive failure" in window.error_area.toPlainText()
    assert window.dashboard_view.cards["connection"][0].text() == "Error"


def test_workspace_adds_no_timer_and_close_releases_existing_resources(window_factory):
    # Dashboard/필터는 자체 timer/worker를 추가하지 않는다.
    from PySide6.QtCore import QTimer
    window = window_factory()
    assert not window.dashboard_view.findChildren(QTimer)
    assert not window.monitor_filter.findChildren(QTimer)
    window.start_monitor()
    wait_until(window.receiver_running)
    worker = window.worker
    assert window.close()
    assert not worker.isRunning()
    assert not window.timer.isActive() and not window.age_timer.isActive()
    assert not window.logging_view.timer.isActive() and not window.graph_view.timer.isActive()


def test_dashboard_small_width_and_scroll_are_independent_from_other_pages(window_factory, qt_app):
    # 다른 페이지의 최소 폭/스크롤 위치 때문에 Dashboard가 가려지면 실패한다.
    window = window_factory()
    qt_app.processEvents()
    window.resize(800, 600)
    window.tabs.setCurrentWidget(window.driver_control_view)
    window.page_scroll.ensureWidgetVisible(window.driver_control_view.live_tx_button)
    driver_scroll = window.page_scroll
    window.tabs.setCurrentWidget(window.dashboard_view)
    wait_until(lambda: window.dashboard_view._columns == 1)
    assert window.page_scroll is not driver_scroll
    assert window.page_scroll.horizontalScrollBar().maximum() == 0
    assert window.page_scroll.verticalScrollBar().value() == 0
    assert window.dashboard_view.width() <= window.page_scroll.viewport().width()
    window.tabs.setCurrentWidget(window.driver_control_view)
    assert window.page_scroll is driver_scroll


def test_monitor_extended_id_and_format_remain_readable(window_factory):
    # 실제 EXT 표시 문자열 전체 폭과 tooltip을 검증한다. 새 CAN 식별자를 만들지 않는다.
    window = window_factory()
    show_frame(window, make_demo_frame(1))
    item = window.table.item(0, 2)
    assert "EXT" in item.text() and item.toolTip() == item.text()
    assert window.table.columnWidth(2) >= window.table.fontMetrics().horizontalAdvance(item.text())
