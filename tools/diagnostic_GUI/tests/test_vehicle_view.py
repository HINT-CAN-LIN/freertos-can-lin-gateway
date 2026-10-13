"""기존 GUI 위의 Vehicle 탭 자동화. 모든 데이터는 Mock / TEST ONLY이다."""
from dataclasses import replace
from copy import deepcopy

import pytest
pytest.importorskip("PySide6", reason="install .[gui] for GUI tests")
from PySide6.QtCore import Qt, QThread
from PySide6.QtTest import QTest
from pc_diagnostic.gui.demo import make_demo_frame
from pc_diagnostic.gui.vehicle_status import DISPLAY_ITEMS
from pc_diagnostic.interfaces import MockCanInterface
from test_gui import qt_app, window_factory, wait_until

ITEM = "DBC Observation"
ROW = DISPLAY_ITEMS.index(ITEM)
VALUE_COLUMN = 3
STATE_COLUMN = 7


def select_mapping(view, message="TestOnlySample", signal="Measurement", *, channel="DEMO/TEST ONLY", confirmed=True):
    # 사용자가 exact 출처와 의미 확인을 선택하는 실제 Qt 경계를 조작한다.
    view.item_combo.setCurrentText(ITEM)
    view.observe_channel(channel)
    view.message_combo.setCurrentIndex(view.message_combo.findData(message) if message else 0)
    for index in range(1, view.channel_combo.count()):
        value = view.channel_combo.itemData(index)
        if type(value) is type(channel) and value == channel:
            view.channel_combo.setCurrentIndex(index)
            break
    view.signal_combo.setCurrentText(signal)
    view.confirm_box.setChecked(confirmed)
    QTest.mouseClick(view.apply_button, Qt.MouseButton.LeftButton)


def cell(view, column, row=ROW):
    # 표시 항목별 상태/값을 검사하며 렌더 좌표에 의존하지 않는다.
    return view.table.item(row, column).text()


def show_frame(window, frame):
    # 기존 Worker→Buffer 다음의 실제 GUI 처리 경계를 사용한다.
    window.buffer.append(frame)
    window.refresh_frames()


def test_vehicle_tab_no_dbc_and_explicit_no_data(window_factory, synthetic_dbc_path):
    # 기존 Monitor 탭은 유지하고 새 탭은 기본 연결 없이 시작한다.
    window = window_factory()
    view = window.vehicle_view
    assert window.tabs.tabText(1) == "Vehicle Status"
    assert all(cell(view, STATE_COLUMN, row) == "No DBC" for row in range(len(DISPLAY_ITEMS)))
    window.load_dbc(synthetic_dbc_path)
    assert not view.model.mappings
    assert cell(view, STATE_COLUMN) == "Ambiguous"
    select_mapping(view)
    assert cell(view, STATE_COLUMN) == "No Data" and cell(view, VALUE_COLUMN) == "No Data"
    assert cell(view, 4) == "test_unit"
    assert "Mock / DEMO / TEST ONLY" in view.source_label.text()


def test_value_age_signal_view_and_raw_are_consistent(window_factory, synthetic_dbc_path):
    # 동일 Cache를 읽되 Raw/선택 프레임과 Vehicle 최신값을 섞지 않는다.
    window = window_factory()
    window._clock = lambda: 14.5
    window.load_dbc(synthetic_dbc_path)
    view = window.vehicle_view
    select_mapping(view)
    frame = replace(make_demo_frame(0), timestamp=12.5)
    show_frame(window, frame)
    window.table.selectRow(0)
    assert cell(view, VALUE_COLUMN) == "-10.0" and cell(view, 4) == "test_unit"
    assert cell(view, 5) == "12.500000" and cell(view, 6) == "2.000"
    assert cell(view, STATE_COLUMN) == "Valid"
    assert window.signal_table.rowCount() == window.cache_table.rowCount() == 3
    assert window.selected_observation().frame is frame
    window._clock = lambda: 17.5
    wait_until(lambda: cell(view, 6) == "5.000")


def test_missing_and_duplicate_mapping_are_visible(window_factory, synthetic_dbc_path, monkeypatch):
    # exact 이름만 검사하고 Message 미선택의 중복 이름은 자동 연결하지 않는다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    view = window.vehicle_view
    select_mapping(view, signal="missing")
    assert cell(view, STATE_COLUMN) == "Not Defined"
    original = window.decode_session.loader.get_messages()
    extra = deepcopy(original[1])
    extra.signals[0].name = "Measurement"
    monkeypatch.setattr(window.decode_session.loader, "get_messages", lambda: (original[0], extra))
    view.message_combo.setCurrentIndex(0)
    view.update_signals()
    select_mapping(view, message=None)
    assert cell(view, STATE_COLUMN) == "Ambiguous"
    assert "2 message" in cell(view, 8)


def test_source_change_requires_new_confirmation(window_factory, synthetic_dbc_path):
    # 이전 Signal의 확인 상태를 변경한 출처에 자동 승계하지 않는다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    view = window.vehicle_view
    select_mapping(view)
    view.signal_combo.setCurrentText("Mode")
    assert not view.confirm_box.isChecked()
    QTest.mouseClick(view.apply_button, Qt.MouseButton.LeftButton)
    assert cell(view, STATE_COLUMN) == "Ambiguous"
    view.confirm_box.setChecked(True)
    view.channel_combo.setCurrentIndex(0)
    assert not view.confirm_box.isChecked()


def test_channels_do_not_mix_values(window_factory, synthetic_dbc_path, dbc_codec):
    # 같은 Signal 이름의 다른 채널 값을 선택한 출처에만 표시한다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    for channel, value in (("A", -10), ("B", 0)):
        frame = replace(dbc_codec.encode("TestOnlySample", {"Measurement": value, "Mode": 1, "Counter": 7}),
                        timestamp=10, channel=channel, is_rx=True)
        show_frame(window, frame)
    select_mapping(window.vehicle_view, channel="A")
    assert cell(window.vehicle_view, VALUE_COLUMN) == "-10.0"
    select_mapping(window.vehicle_view, channel="B")
    assert cell(window.vehicle_view, VALUE_COLUMN) == "0.0"
    select_mapping(window.vehicle_view, channel="missing")
    assert cell(window.vehicle_view, STATE_COLUMN) == "No Data"


def test_decode_error_keeps_value_and_raw_payload(window_factory, synthetic_dbc_path):
    # 실패는 표시하지만 정상 RX 값/시각을 삭제하거나 Offline으로 만들지 않는다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    select_mapping(window.vehicle_view)
    good = replace(make_demo_frame(0), timestamp=10)
    show_frame(window, good)
    bad = replace(good, timestamp=20, data=bytes(3), dlc=3)
    show_frame(window, bad)
    view = window.vehicle_view
    assert cell(view, STATE_COLUMN) == "Decode Error"
    assert cell(view, VALUE_COLUMN) == "-10.0" and cell(view, 5) == "10.000000"
    assert "length mismatch" in cell(view, 8)
    assert view.table.item(ROW, 8).toolTip() == cell(view, 8)
    assert window.table.item(1, 4).text() == "00 00 00"
    show_frame(window, replace(good, timestamp=30))
    assert cell(view, STATE_COLUMN) == "Valid" and cell(view, 5) == "30.000000"


def test_clear_remove_and_reload_have_distinct_effects(window_factory, synthetic_dbc_path, tmp_path):
    # 기존 Clear는 Cache/사용자 연결을 보존하고 새 DBC 세션만 연결을 초기화한다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    view = window.vehicle_view
    select_mapping(view)
    show_frame(window, make_demo_frame(0))
    window.clear_monitor()
    assert cell(view, STATE_COLUMN) == "Valid" and window.table.rowCount() == 0
    QTest.mouseClick(view.remove_button, Qt.MouseButton.LeftButton)
    assert cell(view, STATE_COLUMN) == "Ambiguous"
    assert window.decode_session.service.cache.snapshot()
    select_mapping(view)
    assert window.load_dbc(synthetic_dbc_path)
    assert not view.model.mappings and cell(view, STATE_COLUMN) == "Ambiguous"
    assert view.message_combo.currentData() is None and not view.confirm_box.isChecked()
    select_mapping(view)
    assert cell(view, STATE_COLUMN) == "No Data"
    assert not window.load_dbc(tmp_path / "missing.dbc")
    assert cell(view, STATE_COLUMN) == "No DBC"


def test_repeat_worker_updates_and_close_releases(window_factory, synthetic_dbc_path, qt_app, monkeypatch):
    # 수신마다 Qt 메인 스레드에서만 표시하며 매 실행 새 Mock을 정상 해제한다.
    transports = []
    class Tracked(MockCanInterface):
        def shutdown(self):
            # 해제 횟수는 테스트 전용 증거이다.
            self.released += 1
            super().shutdown()
    def factory():
        # 각 Start는 독립 transport를 생성한다.
        transport = Tracked()
        transport.released = 0
        transports.append(transport)
        return transport
    window = window_factory(factory)
    window.load_dbc(synthetic_dbc_path)
    view = window.vehicle_view
    select_mapping(view)
    refresh = view.refresh
    def checked_refresh():
        # Worker가 위젯을 직접 갱신하면 실패한다.
        assert QThread.currentThread() == qt_app.thread()
        refresh()
    monkeypatch.setattr(view, "refresh", checked_refresh)
    for cycle in range(3):
        before = window.buffer.total_received
        old_stamp = cell(view, 5)
        window.start_monitor()
        wait_until(lambda: window.buffer.total_received > before and cell(view, STATE_COLUMN) == "Valid" and cell(view, 5) != old_stamp)
        window.stop_monitor()
        wait_until(lambda: window.worker is None)
        assert transports[cycle].released == 1 and not transports[cycle].sent_frames
    window.start_monitor()
    wait_until(lambda: len(transports) == 4 and window.table.rowCount() > 0)
    worker = window.worker
    assert window.close() and not worker.isRunning()
    assert all(t.released == 1 for t in transports)
    assert not view.apply_button.isEnabled()
    before = dict(view.model.mappings)
    view.apply_mapping()
    view.refresh()
    assert view.model.mappings == before


def test_vehicle_display_is_bounded_under_buffer_drop(window_factory, synthetic_dbc_path):
    # 새 화면도 기존 유한 Buffer의 처리 결과만 읽는다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    select_mapping(window.vehicle_view)
    for index in range(2000):
        window.buffer.append(replace(make_demo_frame(0), timestamp=index))
    for _ in range(6):
        window.refresh_frames()
    assert window.vehicle_view.table.rowCount() == len(DISPLAY_ITEMS)
    assert cell(window.vehicle_view, 5) == "1999.000000"
    assert window.buffer.dropped == 1488 and window._processed == 512

@pytest.mark.parametrize("channel", [None, 0, "0"])
def test_channel_selector_preserves_type(window_factory, synthetic_dbc_path, channel):
    # None/정수 0/문자열 '0'을 실제 Qt 선택에서도 서로 구분한다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    show_frame(window, replace(make_demo_frame(0), channel=channel))
    select_mapping(window.vehicle_view, channel=channel)
    mapping = window.vehicle_view.model.mappings[ITEM]
    assert type(mapping.channel) is type(channel) and mapping.channel == channel
    assert mapping.channel_selected and cell(window.vehicle_view, STATE_COLUMN) == "Valid"
