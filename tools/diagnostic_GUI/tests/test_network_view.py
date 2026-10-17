"""Network Dashboard Qt 시험. Mock/Fake Live 전용, Hardware KPI 결과 아님."""
from dataclasses import replace
import json
from threading import Event
import pytest
pytest.importorskip("PySide6", reason="install .[gui]")
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QFileDialog
from pc_diagnostic.gui.demo import make_demo_frame
from pc_diagnostic.gui.observation_export import ObservationExport, SnapshotFileWriter
from test_gui import qt_app, window_factory, wait_until
from test_fault_monitor_view import feed
from test_graph_view import select_graph
from test_live_gui import select_live
from fake_live import FakeLive, FAKE_CHANNEL


def panel(window):
    # 기존9개 Navigation을 유지하고 Dashboard 안에서 명시적으로 패널을 연다.
    window.navigation.setCurrentRow(0)
    window.dashboard_view.network_section.set_expanded(True)
    window.dashboard_view.refresh()
    return window.dashboard_view.network_view


@pytest.mark.parametrize("size",[(800,600),(1024,768),(1280,920)])
def test_network_no_data_navigation_and_export_access(window_factory, qt_app, size):
    # 작은 화면에서도 새 버튼이 scroll viewport 안으로 들어와야 한다.
    window=window_factory();window.resize(*size)
    view=panel(window);QTest.qWait(10)
    assert window.navigation.count()==9 and window.tabs.currentWidget() is window.dashboard_view
    assert view.table.rowCount()==0 and "No Data" in view.details.toPlainText()
    assert "Processed RX: 0" in view.summary_label.text() and "Hardware NOT VERIFIED" in view.source_label.text()
    assert "Definition Pending" in view.kpi_label.text() and "Bus Load: N/A" in view.kpi_label.text()
    button=window.export_controls.widgets["network"][2]
    assert not button.isEnabled()
    window.page_scroll.ensureWidgetVisible(button);qt_app.processEvents()
    rect=button.rect();rect.moveTopLeft(button.mapTo(window.page_scroll.viewport(),rect.topLeft()))
    assert window.page_scroll.viewport().rect().contains(rect)
    window.navigation.setCurrentRow(2)
    assert window.tabs.currentWidget() is window.monitor_page


def test_pause_decode_graph_and_network_independent(window_factory, synthetic_dbc_path):
    # 같은 처리 경계에서 Frame마다 Network를 한 번만 세고 Raw Pause와 격리한다.
    window=window_factory();window.load_dbc(synthetic_dbc_path)
    graph=select_graph(window);view=panel(window)
    frame=make_demo_frame(0)
    feed(window,replace(frame,timestamp=10))
    window.set_raw_paused(True)
    feed(window,replace(frame,timestamp=10.01),replace(frame,timestamp=10.02))
    view.refresh()
    row=view.records[0]
    assert window.table.rowCount()==1 and window.network_model.processed_rx==3
    assert graph.model.accepted==3 and row["frame_count"]==3
    assert row["mean_period_s"]==pytest.approx(.01)
    assert window.decode_session.service.cache.get_message("TestOnlySample",channel=frame.channel).timestamp==10.02
    window.set_raw_paused(False)
    assert window.table.rowCount()==3 and window.network_model.processed_rx==3


def test_queue_drop_counts_partial_without_inventing_bus_loss(window_factory):
    # GUI buffer512에서 실제 제외를 유발하고 Network는 drain한 부분집합만 센다.
    window=window_factory()
    for i in range(520):
        window.buffer.append(replace(make_demo_frame(0),timestamp=float(i)))
    while window.buffer.pending_count:
        window.refresh_frames()
    row=window.network_model.snapshot_records(window.decode_session.loader)[0]
    assert window.buffer.total_received==520 and window.network_model.processed_rx==512
    assert row["frame_count"]==512 and row["buffer_dropped"]==8
    assert row["mean_period_s"] is row["observed_frame_rate_hz"] is None
    assert window.table.rowCount()==500 and len(window.raw_history.records)==500
    assert "packet_loss_percent" not in row


def test_dbc_reload_clear_source_and_saved_snapshot(window_factory,synthetic_dbc_path):
    # 기존 ECU 통계와 같은 초기화 경계이며 이미 고정한 Export는 영향을 받지 않는다.
    window=window_factory();window.load_dbc(synthetic_dbc_path)
    feed(window,make_demo_frame(0))
    old=window.export_controls.capture("network")
    assert old.records[0]["message_name"]=="TestOnlySample"
    window.load_dbc(synthetic_dbc_path)
    assert not window.network_model.entries and window.table.rowCount()==1
    feed(window,make_demo_frame(0));window.clear_monitor()
    assert not window.network_model.entries
    window.connection_view.mode_combo.setCurrentText("Live")
    assert not window.network_model.entries and "Live" in window.network_model.source
    assert not window.driver_control_view.live_tx_button.isEnabled()
    assert "Mock" in old.records[0]["source"]


@pytest.mark.parametrize("format",["jsonl","csv"])
def test_network_gui_export_no_dbc_and_activity(window_factory,tmp_path,format):
    # Raw 통계는 DBC 없이도 가능하며 Expected는 null/No DBC다.
    window=window_factory();view=panel(window)
    feed(window,replace(make_demo_frame(0),timestamp=1),replace(make_demo_frame(0),timestamp=2))
    path=tmp_path/("network."+format)
    controls=window.export_controls
    assert controls.export_to("network",path,format=format)
    wait_until(lambda:not controls.exporter.writer.snapshot().active)
    controls.refresh()
    assert path.exists() and "Export completed: network, 1 rows" in window.error_area.toPlainText()
    view.table.selectRow(0);view.show_details()
    assert '"hardware_verification": "NOT VERIFIED"' in view.details.toPlainText()
    if format=="jsonl":
        row=json.loads(path.read_text(encoding="utf-8"))
        assert row["expected_period_ms"] is None and row["comparison_status"]=="No DBC"


def test_real_mock_stop_start_counts_logging_and_close(window_factory,tmp_path):
    # 기존 Mock Worker와 Raw Logger를 실제로 실행하되 물리 CAN은 없다.
    window=window_factory();panel(window);window.set_raw_paused(True)
    window.start_monitor();wait_until(lambda:window.network_model.processed_rx>=3)
    path=tmp_path/"raw.jsonl";window.logging_view.set_output_path(path)
    window.logging_view.start_recording()
    wait_until(lambda:window.logging_session.snapshot().written>=2)
    window.stop_monitor();wait_until(lambda:window.worker is None and not window.buffer.pending_count)
    count=window.network_model.processed_rx
    window.start_monitor();wait_until(lambda:window.network_model.processed_rx>count)
    assert window.network_model.receiver_runs==2 and window.table.rowCount()==0
    worker=window.worker
    assert window.close() and not worker.isRunning()
    assert not window.timer.isActive() and not window.age_timer.isActive()


def test_fake_live_source_never_hardware_verified(window_factory):
    # 실제 Live factory 대신 기존 Fake transport를 주입하고 TX0/정상해제를 확인한다.
    buses=[]
    def factory(settings):
        # Frame은 기존 fixture이고 실제 Bus를 생성하지 않는다.
        bus=FakeLive();buses.append(bus);return bus
    window=window_factory()
    select_live(window,factory);panel(window)
    window.start_monitor();wait_until(lambda:window.network_model.processed_rx>=4)
    window.stop_monitor();wait_until(lambda:window.worker is None and not window.buffer.pending_count)
    rows=window.network_model.snapshot_records(window.decode_session.loader)
    assert rows and all("TEST ONLY" in r["source"] and r["source_kind"]=="Injected Live / TEST ONLY" for r in rows)
    assert all(r["hardware_verification"]=="NOT VERIFIED" for r in rows)
    assert all(r["channel"]==FAKE_CHANNEL for r in rows)
    assert any(r["timestamp_duplicate"] or r["timestamp_reversed"] for r in rows)
    assert all(b.shutdown_calls==1 and b.send_calls==0 for b in buses)
    assert not window.driver_control_view.live_tx_button.isEnabled()


def test_export_file_dialog_snapshots_before_source_switch(window_factory,tmp_path,monkeypatch):
    # 사용자 파일 선택 nested loop 동안 Source가 달라져도 고정한 관측 Source를 보존한다.
    window=window_factory();feed(window,make_demo_frame(0))
    path=tmp_path/"selected.jsonl"
    def choose(*args,**kwargs):
        # Save dialog를 직접 모의하며 실제 경로는 시험자가 명시한다.
        window.connection_view.mode_combo.setCurrentText("Live")
        return str(path),""
    monkeypatch.setattr(QFileDialog,"getSaveFileName",choose)
    window.export_controls.choose("network")
    wait_until(lambda:not window.export_controls.exporter.writer.snapshot().active)
    assert "Mock" in json.loads(path.read_text(encoding="utf-8"))["source"]
    assert not window.network_model.entries


def test_network_error_first_close_and_retry(window_factory,tmp_path):
    # 공통 Export lifecycle을 Network snapshot에서도 유지하는지 확인한다.
    window=window_factory();feed(window,make_demo_frame(0))
    class Broken(SnapshotFileWriter):
        def close(self):
            # 실제 handle 해제 후 close 실패만 모의한다.
            super().close()
            raise OSError("TEST ONLY network close")
    window.export_controls.exporter=ObservationExport(writer_factory=Broken)
    window.export_controls.export_to("network",tmp_path/"error")
    wait_until(lambda:not window.export_controls.exporter.writer.snapshot().active)
    assert not window.close() and window.isVisible()
    assert "Export ended with error" in window.error_area.toPlainText()
    assert window.close()


def test_statistics_outlive_raw500_without_replay_or_drop(window_factory):
    # Raw 표시500행과 무관하게 같은 키의 구간 집계는 유지하며 유한 데이터만 보관한다.
    window=window_factory()
    for batch in range(6):
        feed(window,*[replace(make_demo_frame(0),timestamp=(batch*100+i)*.001) for i in range(100)])
    row=window.network_model.snapshot_records(window.decode_session.loader)[0]
    assert window.table.rowCount()==len(window.raw_history.records)==500
    assert row["frame_count"]==600 and row["interval_count"]==599 and row["buffer_dropped"]==0
    assert row["mean_period_s"]==pytest.approx(.001)
    assert len(window.network_model.entries)==1
