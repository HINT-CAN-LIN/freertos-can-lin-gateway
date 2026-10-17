"""Raw 표시 Pause/Resume. TEST ONLY Rx와 기존 데이터 처리 독립성을 검증한다."""
from dataclasses import replace
from time import time
import pytest
pytest.importorskip("PySide6", reason="install .[gui]")
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from pc_diagnostic.gui.demo import make_demo_frame
from pc_diagnostic.gui.monitor_history import ObservationHistory
from pc_diagnostic.gui.window import MAX_TABLE_ROWS
from pc_diagnostic.logger import RawCanLogger
from test_gui import qt_app, window_factory, wait_until
from test_fault_monitor_view import select_fault_source, feed
from test_graph_view import select_graph
from test_vehicle_view import select_mapping


@pytest.mark.parametrize("capacity", [0, -1, True])
def test_history_invalid_capacity(capacity):
    # 자원 제한 오류를 생성 단계에서 거부한다.
    with pytest.raises(ValueError):
        ObservationHistory(capacity)


def test_pause_keeps_raw_cells_and_selection_but_updates_processing(window_factory, synthetic_dbc_path):
    # 표시 행·선택은 고정하고 Cache/Graph/Vehicle/Fault에는 새 관측이 전달돼야 한다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    select_mapping(window.vehicle_view)
    graph = select_graph(window)
    fault = select_fault_source(window)
    first = replace(make_demo_frame(0), timestamp=10)
    feed(window, first)
    window.table.selectRow(0)
    selected = window.selected_observation()
    cells = [window.table.item(0, c).text() for c in range(5)]
    window.set_raw_paused(True)
    feed(window, replace(first, timestamp=11), replace(first, timestamp=12))
    assert window.table.rowCount() == 1
    assert [window.table.item(0, c).text() for c in range(5)] == cells
    assert window.selected_observation() is selected
    cached = window.decode_session.service.cache.get_message("TestOnlySample", channel=first.channel)
    assert cached.timestamp == 12
    assert graph.model.accepted == 3 and len(fault.model.entries) == 3
    assert window.counter_label.text() == "Received: 3" and window._processed == 3
    assert window.vehicle_view.table.item(5, 7).text() == "Valid"
    window.set_raw_paused(False)
    assert window.table.rowCount() == 3 and window.selected_observation() is selected


def test_resume_latest500_once_no_duplicates_or_timestamp_sort(window_factory, synthetic_dbc_path):
    # frame backlog가 아닌 최신 처리 이력500개만 교체하며 이후 신규 수신을 한 번씩 붙인다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    frame = make_demo_frame(0)
    for i in range(5):
        feed(window, replace(frame, timestamp=float(i)))
    window.table.selectRow(0)
    window.set_raw_paused(True)
    for i in range(5, 755):
        feed(window, replace(frame, timestamp=float(i)))
    assert window.table.rowCount() == 5 and len(window.raw_history.records) == MAX_TABLE_ROWS
    assert window.buffer.pending_count == 0 and window.buffer.dropped == 0
    window.set_raw_paused(False)
    stamps = [float(window.table.item(row, 0).text()) for row in range(500)]
    assert stamps == list(map(float, range(255, 755))) and len(set(stamps)) == 500
    assert window.selected_observation() is None  # 상한 제외된 선택은 복원하지 않는다.
    window.set_raw_paused(False)  # 중복 Resume은 다시 붙이지 않는다.
    feed(window, replace(frame, timestamp=755.0))
    assert window.table.rowCount() == 500
    assert float(window.table.item(0, 0).text()) == 256
    assert float(window.table.item(499, 0).text()) == 755
    window.set_raw_paused(True)
    feed(window, replace(frame, timestamp=None), replace(frame, timestamp=1))
    window.set_raw_paused(False)
    assert window.table.item(498, 0).text() == "unknown"
    assert window.table.item(499, 0).text() == "1.000000"


def test_pause_clear_source_reload_and_stop_contract(window_factory, synthetic_dbc_path):
    # Clear는 Pause를 유지하고 Cache를 보존한다. Source 전환은 Pause/관측을 초기화한다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    frame = make_demo_frame(0)
    feed(window, frame)
    good = window.decode_session.service.cache.snapshot()
    window.set_raw_paused(True)
    window.clear_monitor()
    assert window.raw_paused and not window.raw_history.records and window.table.rowCount() == 0
    assert window.decode_session.service.cache.snapshot() == good
    feed(window, frame)
    assert window.table.rowCount() == 0 and window.counter_label.text() == "Received: 1"
    window.load_dbc(synthetic_dbc_path)
    assert window.raw_paused and not window.decode_session.service.cache.snapshot()
    with pytest.raises(ValueError, match="No Data"):
        window.export_controls.capture("decoded")
    window.set_raw_paused(False)
    assert window.table.rowCount() == 1  # 기존 Raw의 과거 DBC 세션 표시는 유지한다.
    window.connection_view.mode_combo.setCurrentText("Live")
    assert not window.raw_paused and not window.raw_history.records and window.table.rowCount() == 0
    assert not window.driver_control_view.live_tx_button.isEnabled() and window.worker is None


@pytest.mark.parametrize("format", ["csv", "jsonl"])
def test_real_mock_pause_keeps_logger_bytes_and_repeat_start_stop(window_factory, tmp_path, format):
    # 실제 Mock Receiver sink와 RawCanLogger byte 계약을 비교한다. 물리 CAN 시험은 아니다.
    window = window_factory()
    accepted = []
    original = window.logging_session.accept
    def record(frame):
        # 실제 Writer admission을 통과한 프레임만 byte 비교에 사용한다.
        result = original(frame)
        if result:
            accepted.append(frame)
        return result
    window.logging_session.accept = record
    window.start_monitor()
    wait_until(window.receiver_running)
    window.set_raw_paused(True)
    frozen = window.table.rowCount()
    path = tmp_path / ("paused." + format)
    window.logging_view.format_combo.setCurrentIndex(window.logging_view.format_combo.findData(format))
    window.logging_view.set_output_path(path)
    window.logging_view.start_recording()
    wait_until(lambda: window.logging_session.snapshot().written >= 3)
    # Writer와 GUI drain은 별도 경로다. GUI 처리 완료도 실제 카운터로 기다린다.
    wait_until(lambda: window._processed >= 3)
    assert window.table.rowCount() == frozen
    assert window.buffer.total_received >= 3 and window._processed >= 3
    window.stop_monitor()
    wait_until(lambda: window.worker is None and not window.logging_session.snapshot().active)
    assert window.raw_paused
    reference = tmp_path / ("reference." + format)
    with RawCanLogger(reference, format=format) as logger:
        for frame in accepted:
            logger.write(frame)
    assert accepted and path.read_bytes() == reference.read_bytes()
    window.set_raw_paused(False)
    assert window.table.rowCount() == len(window.raw_history.records)
    for _ in range(2):
        window.set_raw_paused(True)
        before = window.buffer.total_received
        window.start_monitor()
        wait_until(lambda: window.buffer.total_received > before)
        window.stop_monitor()
        wait_until(lambda: window.worker is None)
        assert window.raw_paused
        window.set_raw_paused(False)
        assert window.table.rowCount() == len(window.raw_history.records)
    window.start_monitor()
    wait_until(window.receiver_running)
    worker = window.worker
    assert window.close() and not worker.isRunning()
    assert not window.timer.isActive() and not window.age_timer.isActive()


def test_filters_while_paused_do_not_change_snapshot_or_cache(window_factory, synthetic_dbc_path):
    # 사용자 표시 필터는 허용하되 처리 이력/Export snapshot은 숨기지 않는다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    feed(window, make_demo_frame(0), make_demo_frame(1))
    window.set_raw_paused(True)
    window.monitor_filter.search.setText("hide all")
    feed(window, make_demo_frame(0))
    assert window.table.rowCount() == 2
    assert all(window.table.isRowHidden(row) for row in range(2))
    assert len(window.export_controls.capture("decoded").records) == 3
    window.set_raw_paused(False)
    assert window.table.rowCount() == 3
    window.monitor_filter.search.clear()
    assert all(not window.table.isRowHidden(row) for row in range(3))
