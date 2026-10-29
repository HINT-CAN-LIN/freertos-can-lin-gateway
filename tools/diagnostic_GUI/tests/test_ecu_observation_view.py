"""Mock / TEST ONLY Qt UI 경계 검증. 실제 ECU Health/Hardware 테스트가 아니다."""
from dataclasses import replace
import pytest
pytest.importorskip("PySide6", reason="install .[gui]")
from PySide6.QtCore import QThread, Qt
from PySide6.QtTest import QTest
from pc_diagnostic.frame import RawCanFrame
from pc_diagnostic.gui.demo import make_demo_frame
from pc_diagnostic.gui.ecu_observation import ECU_NAMES, LIN_ECUS
from pc_diagnostic.gui.observation_view import FAULT_TARGET
from pc_diagnostic.gui.message_statistics import MessageStatisticsStore
from pc_diagnostic.interfaces import MockCanInterface
from test_gui import qt_app, window_factory, wait_until
from test_vehicle_view import select_mapping as select_vehicle, cell as vehicle_cell


def select_source(view, target="VCU", message="TestOnlySample", channel="DEMO/TEST ONLY", signal=None, confirmed=True):
    # 실제 Qt 선택/확인/Apply 경계를 사용하며 Production 기본값을 넣지 않는다.
    view.target_combo.setCurrentText(target)
    view.observe_channel(channel)
    view.message_combo.setCurrentIndex(view.message_combo.findData(message) if message else 0)
    for index in range(1, view.channel_combo.count()):
        value = view.channel_combo.itemData(index)
        if type(value) is type(channel) and value == channel:
            view.channel_combo.setCurrentIndex(index)
            break
    view.signal_combo.setCurrentIndex(max(0, view.signal_combo.findData(signal)))
    view.confirm_box.setChecked(confirmed)
    QTest.mouseClick(view.apply_button, Qt.MouseButton.LeftButton)


def show_frame(window, frame):
    # 새 통계도 기존 Buffer→DecodeSession 결과로만 갱신한다.
    window.buffer.append(frame)
    window.refresh_frames()


def state(view, ecu="VCU"):
    # 카드 상태를 표시값 그대로 검사한다.
    return view.cards[ecu]["state"].text()


def test_seven_cards_no_mapping_and_routes(window_factory):
    # ECU 이름만 제공하며 LIN 직접 관측 또는 Health default를 표시하지 않는다.
    window = window_factory()
    view = window.ecu_view
    assert window.tabs.tabText(2) == "ECU Health Observation" and len(view.cards) == 7
    for ecu in ECU_NAMES:
        assert state(view, ecu) == "State: Not Configured"
    assert "Healthy/Online" in view.findChildren(type(view.source_label))[1].text()
    assert not view.model.mappings and not view.apply_button.isEnabled()
    routes = [label.text() for label in view.findChildren(type(view.source_label))]
    assert routes.count("CAN 직접 관측") == 4
    assert routes.count("Gateway 경유 CAN (LIN 직접 수신 아님)") == 3


def test_raw_statistics_no_dbc_unknown_and_flags(window_factory, synthetic_dbc_path):
    # DBC 미로드에서도 통계는 Raw 속성만 사용하고 알 수 없는 이름을 합성하지 않는다.
    window = window_factory()
    view = window.ecu_view
    frame = replace(make_demo_frame(0), timestamp=10, channel=0)
    show_frame(window, frame)
    show_frame(window, replace(frame, timestamp=20, data=bytes(3), dlc=3))
    table = view.statistics_table
    assert table.rowCount() == 1 and table.item(0, 4).text() == "2"
    assert table.item(0, 3).text() == "3" and table.item(0, 8).text() == "Unknown / Undefined"
    assert table.item(0, 5).text() == "10.000000" and table.item(0, 6).text() == "20.000000"
    assert window.load_dbc(synthetic_dbc_path)
    assert table.rowCount() == 0
    show_frame(window, RawCanFrame(0x7FE, b"\xA5", timestamp=42))
    show_frame(window, replace(frame, is_error_frame=True))
    show_frame(window, replace(frame, data=b"", dlc=4, is_remote_frame=True))
    assert table.rowCount() == 3
    assert table.item(0, 8).text() == "Unknown / Undefined"
    assert table.item(1, 8).text() == "Error mask; no DBC lookup"
    assert "RTR" in table.item(2, 2).text()


@pytest.mark.parametrize("channel", [None, 0, "0"])
def test_explicit_selection_typed_channel_id_and_format(window_factory, synthetic_dbc_path, channel):
    # 선택한 typed channel의 STD만 해당 카드의 관측 근거이다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    view = window.ecu_view
    select_source(view, channel=channel)
    assert state(view) == "State: No Data"
    show_frame(window, replace(make_demo_frame(0), timestamp=10, channel=channel))
    show_frame(window, replace(make_demo_frame(1), timestamp=20, channel=channel))
    show_frame(window, replace(make_demo_frame(0), timestamp=30, channel="another"))
    mapping = view.model.mappings["VCU"]
    assert type(mapping.channel) is type(channel)
    assert mapping.arbitration_id == make_demo_frame(0).arbitration_id and mapping.is_extended_id is False
    assert state(view) == "State: Observed"
    assert "10.000000" in view.cards["VCU"]["time"].text()
    assert view.cards["VCU"]["count"].text() == "Processed Message RX: 1"
    assert view.statistics_table.rowCount() == 3
    assert "TestOnlyNode" in view.definition_label.text()


def test_confirmation_reset_and_duplicate_mapping(window_factory, synthetic_dbc_path):
    # 확인은 Source 변경 시 재요구되고 중복 ECU 연결은 모두 모호 상태이다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    view = window.ecu_view
    select_source(view)
    view.message_combo.setCurrentIndex(view.message_combo.findData("TestOnlyExtended"))
    assert not view.confirm_box.isChecked()
    QTest.mouseClick(view.apply_button, Qt.MouseButton.LeftButton)
    assert state(view) == "State: Ambiguous"
    select_source(view)
    select_source(view, target="Motor")
    assert state(view) == state(view, "Motor") == "State: Ambiguous"
    QTest.mouseClick(view.remove_button, Qt.MouseButton.LeftButton)
    assert state(view, "Motor") == "State: Not Configured"
    assert state(view) == "State: No Data"


@pytest.mark.parametrize("ecu", ["Door", "Light", "Window"])
def test_lin_individual_signal_is_required(window_factory, synthetic_dbc_path, ecu):
    # TEST ONLY Signal의 선택은 화면 검증이며 실제 LIN/개별 ECU의 정상 검증이 아니다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    view = window.ecu_view
    show_frame(window, make_demo_frame(0))
    select_source(view, target=ecu)
    assert state(view, ecu) == "State: Not Available"
    select_source(view, target=ecu, signal="Measurement")
    assert state(view, ecu) == "State: Observed"
    assert "Signal value: -10.0" in view.cards[ecu]["details"].text()
    assert all(state(view, other) == "State: Not Configured" for other in LIN_ECUS - {ecu})


def test_fault_selection_values_enum_error_and_recovery(window_factory, synthetic_dbc_path):
    # 선택한 TEST ONLY Message의 값/Choice만 읽는다. 새 Fault 의미는 생성하지 않는다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    view = window.ecu_view
    assert "Not Configured" in view.fault_label.text()
    select_source(view, target=FAULT_TARGET)
    assert "No Data" in view.fault_label.text() and view.fault_table.rowCount() == 0
    assert not view.signal_combo.isEnabled()
    good = replace(make_demo_frame(0), timestamp=10)
    show_frame(window, good)
    assert "Observed" in view.fault_label.text() and view.fault_table.rowCount() == 3
    rows = {view.fault_table.item(row, 1).text(): row for row in range(3)}
    assert view.fault_table.item(rows["Measurement"], 2).text() == "-10.0"
    assert view.fault_table.item(rows["Measurement"], 4).text() == "test_unit"
    assert view.fault_table.item(rows["Mode"], 3).text() == "ONE"
    show_frame(window, replace(good, timestamp=20, data=bytes(3), dlc=3))
    assert "Decode Error" in view.fault_label.text()
    assert view.fault_table.item(rows["Measurement"], 5).text() == "10.000000"
    assert view.fault_table.item(rows["Measurement"], 6).text() == "20.000000"
    assert window.table.item(1, 4).text() == "00 00 00"
    show_frame(window, replace(good, timestamp=30))
    assert "Observed" in view.fault_label.text()
    assert view.fault_table.item(rows["Measurement"], 5).text() == "30.000000"


def test_clear_reload_and_vehicle_cache_contract(window_factory, synthetic_dbc_path, tmp_path):
    # 기존 Vehicle Cache 보존과 새 관측 구간 초기화를 동시에 검증한다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    view = window.ecu_view
    select_source(view)
    select_source(view, target=FAULT_TARGET)
    select_vehicle(window.vehicle_view)
    show_frame(window, replace(make_demo_frame(0), timestamp=10))
    window.table.selectRow(0)
    assert window.signal_table.rowCount() == 3 and vehicle_cell(window.vehicle_view, 7) == "Valid"
    window.clear_monitor()
    assert view.statistics_table.rowCount() == 0 and state(view) == "State: No Data"
    assert "No Data" in view.fault_label.text() and view.fault_table.rowCount() == 0
    assert view.model.mappings and view.model.fault_mapping
    assert vehicle_cell(window.vehicle_view, 7) == "Valid"
    show_frame(window, make_demo_frame(0))
    assert state(view) == "State: Observed"
    assert window.load_dbc(synthetic_dbc_path)
    assert state(view) == "State: Not Configured" and not view.model.mappings
    assert not view.model.fault_mapping and not view.model.statistics.entries
    assert not view.confirm_box.isChecked() and view.message_combo.currentData() is None
    assert not window.load_dbc(tmp_path / "missing.dbc")
    assert state(view) == "State: Not Configured" and "No DBC" in view.source_label.text()


def test_buffer_and_statistics_exclusions_are_separate(window_factory, synthetic_dbc_path):
    # Buffer Drop 후 처리된 통계는 전체 수신량으로 표시하지 않는다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    view = window.ecu_view
    view.model.statistics = MessageStatisticsStore(2)
    for index in range(1000):
        window.buffer.append(replace(make_demo_frame(0), channel=str(index), timestamp=index))
    for _ in range(6):
        window.refresh_frames()
    assert window.buffer.dropped == 488
    assert window._processed == 512 and view.model.statistics.processed_rx == 512
    assert view.model.statistics.capacity_excluded == 510 and view.statistics_table.rowCount() == 2
    assert view.channel_combo.count() <= 129
    assert "Buffer dropped: 488" in view.coverage_label.text()
    assert "Capacity excluded frames: 510" in view.coverage_label.text()
    assert "총수신량이 아니며" in view.coverage_label.text()


def test_repeated_start_stop_age_and_main_thread_close(window_factory, synthetic_dbc_path, qt_app, monkeypatch):
    # 실행마다 신규 RX/새 Mock/정상 해제와 main-thread UI 호출을 검증한다.
    transports = []
    class Tracked(MockCanInterface):
        def shutdown(self):
            # 각 transport의 해제 횟수는 독립 테스트 증거이다.
            self.released += 1
            super().shutdown()
    def factory():
        # 이전 실행의 transport를 재사용하지 않는다.
        transport = Tracked()
        transport.released = 0
        transports.append(transport)
        return transport
    window = window_factory(factory)
    window.load_dbc(synthetic_dbc_path)
    view = window.ecu_view
    select_source(view)
    refresh = view.refresh
    def checked_refresh():
        # Worker가 UI를 직접 수정하면 즉시 실패한다.
        assert QThread.currentThread() == qt_app.thread()
        refresh()
    monkeypatch.setattr(view, "refresh", checked_refresh)
    for index in range(3):
        before = view.model.statistics.processed_rx
        window.start_monitor()
        worker = window.worker
        window.start_monitor()
        assert window.worker is worker
        wait_until(lambda: view.model.statistics.processed_rx > before)
        window.stop_monitor()
        wait_until(lambda: window.worker is None)
        assert transports[index].released == 1 and not transports[index].sent_frames
    before_time = view.cards["VCU"]["time"].text()
    wait_until(lambda: view.cards["VCU"]["time"].text() != before_time)
    window.start_monitor()
    wait_until(lambda: len(transports) == 4 and window.buffer.total_received > 3)
    worker = window.worker
    assert window.close() and not worker.isRunning()
    assert all(t.released == 1 for t in transports) and not view.apply_button.isEnabled()
    before = view.model.statistics.processed_rx
    view.record(window.decode_session.process(make_demo_frame(0)))
    view.refresh()
    assert view.model.statistics.processed_rx == before
