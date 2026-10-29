"""Windows Network/KPI Native Smoke. Mock/Fake TEST ONLY, 실제 성능/HIL 검증 아님."""
import argparse
from dataclasses import replace
import csv
import json
from pathlib import Path
import can
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from pc_diagnostic import DbcCodec, DbcLoader
from pc_diagnostic.gui.demo import make_demo_frame
from pc_diagnostic.gui.window import MainWindow
from fake_live import FakeLive, FAKE_CHANNEL
from gui_native_smoke import wait_until, NATIVE_WAIT_MS
from test_fault_monitor_view import feed
from test_fault_history import REPOSITORY_DBC

SIZES=((800,600),(1024,768),(1280,920))


def main():
    # 실제 Windows 창을 사용하지만 장치 생성/송신은 금지하고 파일은 지정 폴더만 사용한다.
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",required=True)
    args=parser.parse_args()
    output=Path(args.output_dir)
    assert output.is_dir()
    app=QApplication([]);assert app.platformName()=="windows"
    calls=[];buses=[];captures=[]
    def forbidden(*args,**kwargs):
        # 실기 연결이 발생하면 이 자동 시험을 즉시 실패시킨다.
        calls.append(True)
        raise AssertionError("No physical CAN in Network smoke")
    can.Bus=forbidden
    class TimedFake(FakeLive):
        def recv(self,timeout=None):
            # 기존 합성 Frame의 Timestamp만 결정적으로 생성한다. 실제 도착시간이 아니다.
            frame=super().recv(timeout)
            return None if frame is None else replace(frame,timestamp=100+self.index*.01)
    def factory(settings):
        # Factory 주입 표식으로 Fake Live와 실제 backend를 구분한다.
        bus=TimedFake();buses.append(bus);return bus
    window=MainWindow(live_interface_factory=factory)
    view=window.dashboard_view.network_view
    def settle():
        # 고정 긴 sleep 없이 실제 Qt layout/event를 처리한다.
        for _ in range(5):app.processEvents()
    def show_panel():
        # 기존 Dashboard Navigation 아래 패널을 열며 기존9페이지 순서는 유지한다.
        window.navigation.setCurrentRow(0)
        window.dashboard_view.network_section.set_expanded(True)
        window.dashboard_view.refresh()
        settle()
    def expose(widget):
        # 작은 화면에서 사용자가 스크롤하여 주요 조작을 완전히 볼 수 있어야 한다.
        window.page_scroll.ensureWidgetVisible(widget);settle()
        rect=widget.rect();rect.moveTopLeft(widget.mapTo(window.page_scroll.viewport(),rect.topLeft()))
        assert window.page_scroll.viewport().rect().contains(rect)
    def capture(name):
        # 실제 native QWidget 화면이며 데이터를 합성 시안으로 그리지 않는다.
        settle();assert window.grab().save(str(output/name));captures.append(name)
    try:
        window.show();assert QTest.qWaitForWindowExposed(window,NATIVE_WAIT_MS)
        show_panel()
        assert view.table.rowCount()==0 and "No Data" in view.details.toPlainText()
        fixture=Path(__file__).parent/"fixtures/test_only.dbc"
        window.load_dbc(fixture);window.set_raw_paused(True);window.start_monitor()
        wait_until(lambda:window.network_model.processed_rx>=4)
        window.logging_view.set_output_path(output/"network-raw.jsonl")
        window.logging_view.start_recording()
        wait_until(lambda:window.logging_session.snapshot().written>=2)
        assert window.table.rowCount()==0 and window.decode_session.service.cache.snapshot()
        window.stop_monitor();wait_until(lambda:window.worker is None and not window.buffer.pending_count)
        show_panel()
        assert len(view.records)==2 and all(r["mean_period_s"] is not None for r in view.records)
        assert all(r["expected_period_ms"] is None for r in view.records)
        for width,height in SIZES:
            window.resize(width,height);settle()
            assert (window.width(),window.height())==(width,height)
            expose(window.export_controls.widgets["network"][2])
            capture(f"network-mock-{width}x{height}.png")
            expose(view.table)
            capture(f"network-table-{width}x{height}.png")
        exports=[]
        for format in ("csv","jsonl"):
            path=output/("network."+format)
            assert window.export_controls.export_to("network",path,format=format)
            wait_until(lambda:not window.export_controls.exporter.writer.snapshot().active)
            state=window.export_controls.exporter.writer.snapshot()
            assert state.closed and not state.error
            if format=="jsonl":rows=[json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            else:
                with path.open(encoding="utf-8",newline="") as stream:rows=list(csv.DictReader(stream))
            assert len(rows)==2 and all("Mock" in r["source"] and r["hardware_verification"]=="NOT VERIFIED" for r in rows)
            exports.append({"format":format,"rows":len(rows)})
        window.set_raw_paused(False)
        assert window.table.rowCount()==len(window.raw_history.records)
        # DBC 주기 비교는 실제 Repository metadata에서 읽고 Frame은 Encoder로 시험 생성한다.
        assert window.load_dbc(REPOSITORY_DBC)
        loader=window.decode_session.loader
        codec=DbcCodec(loader)
        for name in ("VCU_Command","Fault_Status"):
            message=loader.get_message_by_name(name)
            frame=replace(codec.encode(name,{s.name:0 for s in message.signals}),is_rx=True,channel="DEMO/TEST ONLY")
            feed(window,*[replace(frame,timestamp=1+i*.01) for i in range(3)])
        show_panel()
        by_name={r["message_name"]:r for r in view.records}
        assert by_name["VCU_Command"]["expected_period_ms"]==10
        assert by_name["Fault_Status"]["expected_period_ms"] is None
        assert by_name["VCU_Command"]["jitter_status"]=="Definition Pending"
        window.resize(1280,920);expose(window.export_controls.widgets["network"][2])
        capture("network-explicit-dbc-period-event.png")
        view.table.horizontalScrollBar().setValue(view.table.horizontalScrollBar().maximum())
        view.table.selectRow(0);view.show_details()
        expose(view.table);capture("network-expected-status-columns.png")
        view.table.horizontalScrollBar().setValue(0)
        # GUI Drop은 실제 Bus packet loss와 별개이며 timing을 N/A로 바꾼다.
        window.clear_monitor()
        for i in range(520):window.buffer.append(replace(make_demo_frame(0),timestamp=float(i)))
        while window.buffer.pending_count:window.refresh_frames()
        row=window.network_model.snapshot_records(loader)[0]
        assert row["frame_count"]==512 and row["buffer_dropped"]==8 and row["mean_period_s"] is None
        window.clear_monitor()
        window.connection_view.mode_combo.setCurrentText("Live")
        window.connection_view.backend_combo.setCurrentIndex(window.connection_view.backend_combo.findData("slcan"))
        window.connection_view.channel_edit.setText("FAKE_NETWORK_TEST_ONLY")
        window.load_dbc(fixture)
        assert not window.driver_control_view.live_tx_button.isEnabled()
        for _ in range(2):
            before=window.network_model.processed_rx
            window.start_monitor();wait_until(lambda:window.network_model.processed_rx>before+3)
            window.stop_monitor();wait_until(lambda:window.worker is None and not window.buffer.pending_count)
        show_panel()
        assert all("Injected" in r["source"] and r["source_kind"]=="Injected Live / TEST ONLY" for r in view.records)
        assert window.network_model.receiver_runs==2
        expose(window.export_controls.widgets["network"][2]);capture("network-fake-live-test-only.png")
        window.start_monitor();wait_until(window.receiver_running)
        worker=window.worker
        assert window.close() and not worker.isRunning()
        assert not window.timer.isActive() and not window.age_timer.isActive()
        assert all(b.shutdown_calls==1 and b.send_calls==0 for b in buses) and not calls
        print(json.dumps({"platform":app.platformName(),"mock_pause_rx_decode_logging":True,
            "period_event_explicit_dbc":True,"jitter":"Definition Pending","bus_load":"N/A",
            "queue_drop_timing_na":True,"fake_live_test_only":True,"exports":exports,
            "receiver_runs":3,"active_close":True,"navigation_pages":window.navigation.count(),
            "screenshots":captures,"CAN_backend_calls":0,"hardware":"NOT VERIFIED","manual":"NOT VERIFIED"}))
    finally:
        # 실패해도 기존 Receiver/Writer 종료 계약을 지켜 미해제 thread를 남기지 않는다.
        window.stop_monitor()
        if window.worker is not None:assert window.worker.wait(NATIVE_WAIT_MS)
        window.logging_session.stop();assert window.logging_session.wait(NATIVE_WAIT_MS/1000)
        window.export_controls.exporter.writer.stop();assert window.export_controls.exporter.wait(NATIVE_WAIT_MS/1000)
        app.processEvents();window.close()
    return 0


if __name__=="__main__":
    raise SystemExit(main())
