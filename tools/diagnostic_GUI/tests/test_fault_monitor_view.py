"""Fault Monitor Qt offscreen 시험. 실제 Fault/ECU/Hardware 결과가 아니다."""
from dataclasses import replace
import pytest
pytest.importorskip("PySide6", reason="install .[gui]")
from PySide6.QtCore import QThread, Qt
from pc_diagnostic.gui.demo import make_demo_frame
from pc_diagnostic.gui.fault_history import channel_key
from pc_diagnostic.gui.fault_monitor_view import entry_detail
from pc_diagnostic.logger import read_jsonl
from test_gui import qt_app, window_factory, wait_until
from test_live_gui import select_live, stop_and_wait
from test_graph_view import select_graph
from fake_live import FakeLive, FAKE_CHANNEL
from test_fault_history import REPOSITORY_DBC, fault_frame

MOCK_CHANNEL = "DEMO/TEST ONLY"


def select_fault_source(window, channel=MOCK_CHANNEL, message="TestOnlySample"):
    # 제품 UI에서 actual Message/Channel을 직접 선택하고 source 확인을 수행한다.
    view = window.fault_monitor_view
    view.observe_channel(channel)
    view.channel_combo.setCurrentIndex(next(i for i in range(1, view.channel_combo.count())
        if type(view.channel_combo.itemData(i)) is type(channel) and view.channel_combo.itemData(i)==channel))
    view.message_combo.setCurrentIndex(next(i for i in range(1, view.message_combo.count())
        if view.message_combo.itemData(i)[0]==message))
    view.confirm_box.setChecked(True)
    view.add_source()
    assert view.model.sources
    return view


def feed(window, *frames):
    # 기존 GUI buffer/Decode 경로로만 주입한다. Fault GUI의 별도 Decode는 허용하지 않는다.
    for frame in frames:
        window.buffer.append(frame)
    window.refresh_frames()


def test_no_dbc_no_data_and_no_automatic_fault_selection(window_factory, synthetic_dbc_path):
    # 미수신을 No Fault라고 표시하지 않는다.
    window = window_factory()
    view = window.fault_monitor_view
    assert window.tabs.tabText(4)=="Signal Graph" and window.tabs.tabText(5)=="Fault Monitor"
    assert "No DBC" in view.state_label.text() and not view.add_button.isEnabled()
    feed(window, make_demo_frame(0))
    assert view.table_model.rowCount()==0 and window.table.rowCount()==1
    assert window.load_dbc(synthetic_dbc_path)
    assert "No Data" in view.state_label.text() and not view.model.sources
    view.message_combo.setCurrentIndex(1)
    view.add_source()
    assert not view.model.sources
    select_fault_source(window)
    assert view.table_model.rowCount()==0 and "Status Unknown" in view.state_label.text()


def test_history_details_reuse_decode_once_and_keep_bad_raw(window_factory, synthetic_dbc_path, monkeypatch):
    # 정상/오류 Raw를 보존하고 Graph/Signal과 동일 per-frame Decode만 사용한다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    view = select_fault_source(window)
    calls=[]
    codec=window.decode_session.service.codec
    original=codec.decode
    def counted(frame):
        # 기존 Codec 호출 수만 관측한다.
        calls.append(frame)
        return original(frame)
    monkeypatch.setattr(codec, "decode", counted)
    good=make_demo_frame(0)
    bad=replace(good, data=b"\x01", dlc=1, timestamp=None)
    feed(window, good, bad, make_demo_frame(1))
    assert len(calls)==3 and view.table_model.rowCount()==2
    assert window.table.rowCount()==3
    view.table.selectRow(0)
    view.show_detail()
    assert "Measurement = -10.0" in view.details.toPlainText() and "test_unit" in view.details.toPlainText()
    view.table.selectRow(1)
    view.show_detail()
    details=view.details.toPlainText()
    assert "Decode Error" in details and "Payload: 01" in details and "Missing" in details
    assert not view.model.entries[-1].signals
    assert window.decode_session.service.cache.get_message("TestOnlySample", channel=MOCK_CHANNEL).signals["Measurement"]==-10.0
    before=len(calls)
    view.refresh(); view.refresh()
    assert len(calls)==before


def test_actual_existing_fault_dbc_code_and_channel_filters(window_factory):
    # 저장소 DBC를 명시적으로 로드한 TEST ONLY 관측이며 하드웨어 Fault 시험이 아니다.
    window=window_factory()
    window.load_dbc(REPOSITORY_DBC)
    view=select_fault_source(window, message="Fault_Status")
    select_fault_source(window, channel=0, message="Fault_Status")
    select_fault_source(window, channel="0", message="Fault_Status")
    session=window.decode_session
    feed(window, fault_frame(session, code=0, channel=MOCK_CHANNEL),
         fault_frame(session, code=1, channel=0), fault_frame(session, code=2, channel="0"))
    assert view.table_model.rowCount()==3
    view.code_filter.setCurrentIndex(view.code_filter.findData(0))
    assert view.table_model.rowCount()==1 and view.table_model.entries[0].signals["FaultCode"]==0
    view.code_filter.setCurrentIndex(0)
    index=next(i for i in range(1,view.channel_filter.count()) if view.channel_filter.itemData(i)==channel_key(0))
    view.channel_filter.setCurrentIndex(index)
    assert view.table_model.rowCount()==1 and type(view.table_model.entries[0].frame.channel) is int
    assert "Status Unknown" in entry_detail(view.table_model.entries[0])
    assert "DBC Choice: ACTIVE" in entry_detail(view.table_model.entries[0])
    assert len(view.model.entries)==3


def test_message_and_decode_error_filters_and_evicted_details(window_factory, synthetic_dbc_path):
    # 같은 ID의 STD/EXT Message를 필터로 구별하고 사라진 행의 상세를 남기지 않는다.
    window=window_factory()
    window.load_dbc(synthetic_dbc_path)
    view=select_fault_source(window)
    select_fault_source(window, message="TestOnlyExtended")
    good=make_demo_frame(0)
    feed(window, good, make_demo_frame(1), replace(good,data=b"",dlc=0))
    assert view.table_model.rowCount()==3
    index=next(i for i in range(1,view.message_filter.count()) if view.message_filter.itemData(i)[0]=="TestOnlyExtended")
    view.message_filter.setCurrentIndex(index)
    assert view.table_model.rowCount()==1 and view.table_model.entries[0].frame.is_extended_id
    view.table.selectRow(0); view.show_detail()
    assert view.details.toPlainText()
    view.error_filter.setChecked(True)
    assert view.table_model.rowCount()==0 and not view.details.toPlainText()
    view.message_filter.setCurrentIndex(0)
    assert view.table_model.rowCount()==1 and view.table_model.entries[0].decode_state=="Decode Error"
    assert len(view.model.entries)==3


def test_clear_history_leaves_logging_graph_cache_and_raw_unchanged(window_factory, synthetic_dbc_path, tmp_path):
    # Clear 중에도 Logger/Graph/Receiver가 계속하며 기존 파일은 변경되지 않는다.
    window=window_factory()
    window.load_dbc(synthetic_dbc_path)
    view=select_fault_source(window)
    graph=select_graph(window)
    window.start_monitor()
    wait_until(lambda: view.model.observed>=2 and graph.model.accepted>=2)
    path=tmp_path/"fault-clear.jsonl"
    window.logging_view.set_output_path(path)
    window.logging_view.start_recording()
    wait_until(lambda: window.logging_session.snapshot().written>=2)
    raw=window.table.rowCount()
    cache=window.decode_session.service.cache.snapshot()
    samples=tuple(graph.model.samples)
    count=window.logging_session.snapshot().written
    writer=window.logging_session._thread
    view.clear_history()
    assert not view.model.entries and window.worker.isRunning() and writer.is_alive()
    assert window.table.rowCount()==raw and window.decode_session.service.cache.snapshot()==cache
    assert tuple(graph.model.samples)==samples and window.logging_session.snapshot().written>=count
    wait_until(lambda: view.model.observed>=1 and window.logging_session.snapshot().written>count)
    stop_and_wait(window)
    snap=window.logging_session.snapshot()
    assert snap.closed and len(list(read_jsonl(path)))==snap.written
    assert not writer.is_alive()


def test_repeat_start_stop_has_new_receptions_and_run_identity(window_factory, synthetic_dbc_path):
    # 이전 표 행만으로 통과하지 않고 매회 신규 관측과 정확한 Start marker를 확인한다.
    window=window_factory()
    window.load_dbc(synthetic_dbc_path)
    view=select_fault_source(window)
    for run in range(1,4):
        before=view.model.observed
        window.start_monitor()
        worker=window.worker
        window.start_monitor()
        assert window.worker is worker
        wait_until(lambda: view.model.observed>before)
        stop_and_wait(window)
        wait_until(lambda: window.buffer.pending_count==0)
        assert view.model.entries[-1].receiver_run==run
    assert {e.receiver_run for e in view.model.entries}=={1,2,3}


def test_start_with_prior_pending_backlog_does_not_claim_exact_run(window_factory, synthetic_dbc_path):
    # 기존 Start API를 변경하지 않고 backlog attribution 불가를 명시적으로 드러낸다.
    window=window_factory()
    window.load_dbc(synthetic_dbc_path)
    view=select_fault_source(window)
    window.buffer.append(make_demo_frame(0))
    window.start_monitor()
    wait_until(lambda: view.model.observed>=2)
    stop_and_wait(window)
    assert all(e.receiver_run is None for e in view.model.entries)
    assert "RX Run Unknown" in view.count_label.text()


def test_source_and_dbc_reload_clear_mapping_history_filters_and_details(window_factory, synthetic_dbc_path):
    # Source 세션 교체 시 과거 decode, 필터 및 상세를 새 Source로 표시하지 않는다.
    window=window_factory()
    window.load_dbc(synthetic_dbc_path)
    view=select_fault_source(window)
    feed(window,make_demo_frame(0))
    view.table.selectRow(0);view.show_detail()
    assert view.details.toPlainText()
    old_session=window.decode_session.session_id
    select_live(window, lambda settings:FakeLive())
    assert window.decode_session.session_id>old_session and not view.model.entries and not view.model.sources
    assert not view.details.toPlainText() and view.channel_combo.count()==1
    assert "TEST ONLY" in view.source_label.text()
    select_fault_source(window, channel=FAKE_CHANNEL)
    window.start_monitor()
    wait_until(lambda:view.model.observed>=1)
    stop_and_wait(window)
    window.load_dbc(synthetic_dbc_path)
    assert not view.model.entries and not view.model.sources and view.code_filter.count()==1
    window.connection_view.mode_combo.setCurrentText("Mock")
    assert not view.model.entries and not view.model.sources


def test_transport_error_then_reconnect_tags_new_run(window_factory, synthetic_dbc_path):
    # 실제 연결 실패가 아닌 Fake backend 오류/재접속에서 과거값을 새 현재 상태로 합성하지 않는다.
    from pc_diagnostic.interfaces import CanInterfaceError
    window=window_factory()
    select_live(window, lambda settings:FakeLive())
    window.load_dbc(synthetic_dbc_path)
    view=select_fault_source(window, channel=FAKE_CHANNEL)
    class FailedFake(FakeLive):
        def recv(self, timeout=None):
            # 첫 정상 관측 후 TEST ONLY transport 오류를 발생시킨다.
            if self.index>=2:
                raise CanInterfaceError("TEST ONLY receive failure")
            return super().recv(timeout)
    window._live_interface_factory=lambda settings:FailedFake()
    window.start_monitor()
    wait_until(lambda:window.worker is None and window.status_label.text()=="Error")
    assert view.model.observed>=1 and view.model.entries[-1].receiver_run==1
    window._live_interface_factory=lambda settings:FakeLive()
    before=view.model.observed
    window.start_monitor()
    wait_until(lambda:view.model.observed>before)
    stop_and_wait(window)
    assert view.model.entries[-1].receiver_run==2 and all(e.fault_status=="Status Unknown" for e in view.model.entries)


def test_fault_view_ui_is_main_thread_and_close_stops_all_resources(window_factory, synthetic_dbc_path):
    # 새 화면은 추가 Thread/Timer를 만들지 않고 기존 종료 계약을 유지한다.
    window=window_factory()
    window.load_dbc(synthetic_dbc_path)
    view=select_fault_source(window)
    assert view.thread() is QThread.currentThread()
    window.start_monitor()
    wait_until(lambda:view.model.observed>0)
    worker=window.worker
    assert window.close() and not worker.isRunning()
    assert view._closed and not window.timer.isActive() and not window.graph_view.timer.isActive()
    before=view.model.observed
    view.record(window.decode_session.process(make_demo_frame(0)))
    assert view.model.observed==before


def test_remove_source_keeps_received_history_but_stops_new_collection(window_factory, synthetic_dbc_path):
    # 사용자 source 제거는 이력 삭제 또는 ECU Clear와 다르다.
    window=window_factory()
    window.load_dbc(synthetic_dbc_path)
    view=select_fault_source(window)
    feed(window,make_demo_frame(0))
    view.remove_source()
    assert len(view.model.entries)==1 and not view.model.sources
    feed(window,make_demo_frame(0))
    assert len(view.model.entries)==1


def test_selected_source_and_detail_are_stable_during_new_rx(window_factory, synthetic_dbc_path, monkeypatch):
    # 수신 중 사용자의 Remove 대상/상세 스크롤을 첫 항목으로 되돌리지 않는다.
    window=window_factory()
    window.load_dbc(synthetic_dbc_path)
    view=select_fault_source(window)
    select_fault_source(window, channel=0)
    view.sources_combo.setCurrentIndex(1)
    selected_source=view.sources_combo.currentData()
    feed(window, make_demo_frame(0))
    view.table.selectRow(0);view.show_detail()
    detail=view.details.toPlainText()
    updates=[]
    original=view.details.setPlainText
    def track(text):
        # 불필요한 immutable 상세 재작성을 검출한다.
        updates.append(text)
        original(text)
    monkeypatch.setattr(view.details, "setPlainText", track)
    feed(window, make_demo_frame(0))
    assert view.sources_combo.currentData()==selected_source
    assert view.details.toPlainText()==detail and not updates
    view.remove_source()
    assert len(view.model.sources)==1


def test_evicted_selected_detail_and_bounded_view(window_factory, synthetic_dbc_path):
    # 이력 상한을 작게 주입해 eviction 후 과거 상세가 새 행으로 오인되지 않는지 확인한다.
    from pc_diagnostic.gui.fault_history import FaultHistoryModel
    window=window_factory()
    window.load_dbc(synthetic_dbc_path)
    view=window.fault_monitor_view
    view.model=FaultHistoryModel(capacity=2)
    view.refresh()
    select_fault_source(window)
    feed(window, make_demo_frame(0))
    view.table.selectRow(0);view.show_detail()
    assert view.details.toPlainText()
    feed(window, make_demo_frame(0), make_demo_frame(0))
    assert view.table_model.rowCount()==2 and view.model.history_omitted==1
    assert not view.details.toPlainText() and [e.sequence for e in view.model.entries]==[2,3]


def test_unknown_channel_filter_is_explicit_not_all(window_factory, synthetic_dbc_path):
    # unknown(None) 채널 선택은 wildcard All과 구별한다.
    window=window_factory()
    window.load_dbc(synthetic_dbc_path)
    view=select_fault_source(window)
    select_fault_source(window, channel=None)
    feed(window, make_demo_frame(0), replace(make_demo_frame(0), channel=None))
    index=next(i for i in range(1,view.channel_filter.count()) if view.channel_filter.itemData(i)==channel_key(None))
    view.channel_filter.setCurrentIndex(index)
    assert view.table_model.rowCount()==1 and view.table_model.entries[0].frame.channel is None


def test_backend_channel_changes_isolate_fault_history(window_factory, synthetic_dbc_path):
    # 같은 Live mode라도 Backend/설정 Channel 변경은 기존 source generation 정책을 따른다.
    window=window_factory()
    select_live(window, lambda settings:FakeLive())
    window.load_dbc(synthetic_dbc_path)
    view=select_fault_source(window, channel=FAKE_CHANNEL)
    frame=replace(make_demo_frame(0), channel=FAKE_CHANNEL)
    feed(window, frame)
    assert view.model.entries
    window.connection_view.channel_edit.setText("OTHER_FAKE_TEST_ONLY")
    assert not view.model.entries and not view.model.sources
    select_fault_source(window, channel=FAKE_CHANNEL)
    feed(window, frame)
    assert view.model.entries
    window.connection_view.backend_combo.setCurrentIndex(window.connection_view.backend_combo.findData("virtual"))
    assert not view.model.entries and not view.model.sources


def test_mapping_error_survives_rx_refresh_until_success(window_factory, synthetic_dbc_path):
    # 주기적 RX refresh가 사용자 매핑 오류 안내를 숨기는 회귀를 검출한다.
    window=window_factory()
    window.load_dbc(synthetic_dbc_path)
    view=select_fault_source(window)
    view.confirm_box.setChecked(False)
    view.add_source()
    assert "Last mapping error" in view.state_label.text() and "Ambiguous" in view.state_label.text()
    feed(window, make_demo_frame(0))
    assert "Ambiguous" in view.state_label.text() and len(view.model.entries)==1
    view.confirm_box.setChecked(True)
    view.add_source()
    assert "Last mapping error" not in view.state_label.text()
