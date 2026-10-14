"""Windows Fault Monitor Native Smoke. Mock/Fake TEST ONLY, 실제 장치 접속·송신 없음."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys
from time import time
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from pc_diagnostic.gui.window import MainWindow
from pc_diagnostic.logger import read_jsonl
from fake_live import FakeLive, FAKE_CHANNEL
from gui_native_smoke import wait_until, NATIVE_WAIT_MS
from test_fault_history import REPOSITORY_DBC, fault_frame
from test_fault_monitor_view import select_fault_source
from test_graph_view import select_graph


def main():
    # 기존 파일을 덮어쓰지 않도록 호출자가 만든 새 증적 폴더만 사용한다.
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    root = Path(args.output_dir)
    assert root.is_dir()
    app = QApplication([])
    assert app.platformName() == "windows"
    transports = []
    frames = ()
    def factory(settings):
        # 기존 DBC 정의의 encoded 시험 프레임만 Fake로 주입한다. 실제 ECU 응답이 아니다.
        bus = FakeLive(frames=frames)
        transports.append(bus)
        return bus
    window = MainWindow(live_interface_factory=factory)
    try:
        window.show()
        assert QTest.qWaitForWindowExposed(window, NATIVE_WAIT_MS)
        fixture = Path(__file__).parent/"fixtures/test_only.dbc"
        assert window.load_dbc(fixture)
        view = select_fault_source(window)
        graph = select_graph(window)
        window.tabs.setCurrentWidget(view)
        window.start_monitor()
        wait_until(lambda: view.model.observed >= 2 and graph.model.accepted >= 2)
        window.logging_view.set_output_path(root/"mock.jsonl")
        window.logging_view.start_recording()
        wait_until(lambda: window.logging_session.snapshot().written >= 2)
        written = window.logging_session.snapshot().written
        raw = window.table.rowCount()
        cached = window.decode_session.service.cache.snapshot()
        graph_count = graph.model.accepted
        view.clear_history()
        assert not view.model.entries and window.table.rowCount() == raw
        assert window.decode_session.service.cache.snapshot() == cached and graph.model.accepted == graph_count
        wait_until(lambda: view.model.observed >= 1 and window.logging_session.snapshot().written > written)
        window.stop_monitor()
        wait_until(lambda: window.worker is None and not window.logging_session.snapshot().active and window.buffer.pending_count == 0)
        view.table.selectRow(0)
        view.show_detail()
        assert "Measurement = -10.0" in view.details.toPlainText() and "Status Unknown" in view.details.toPlainText()
        assert window.grab().save(str(root/"fault-mock.png"))
        # Writer 종료 flag와 Qt UI unlock은 별개다. 실제 사용 가능한 controls를 기다린다.
        wait_until(lambda: window.can_change_source() and window.connection_view.mode_combo.isEnabled())
        window.connection_view.mode_combo.setCurrentText("Live")
        window.connection_view.backend_combo.setCurrentIndex(window.connection_view.backend_combo.findData("slcan"))
        window.connection_view.channel_edit.setText("FAKE_FAULT_TEST_ONLY")
        assert not view.model.entries and not view.model.sources
        assert window.load_dbc(REPOSITORY_DBC)  # native contract test explicit load; no production default.
        session = window.decode_session
        stamp = time()
        first = fault_frame(session, code=1, node=1, recovery=0, system=3, timestamp=stamp, channel=FAKE_CHANNEL)
        frames = (first,
                  fault_frame(session, code=2, node=5, recovery=0, system=2, timestamp=None, channel=FAKE_CHANNEL),
                  fault_frame(session, code=1, node=1, recovery=1, system=0, timestamp=stamp-3, channel=FAKE_CHANNEL),
                  replace(first, data=first.data[:1], dlc=1))
        view = select_fault_source(window, channel=FAKE_CHANNEL, message="Fault_Status")
        graph = select_graph(window, channel=FAKE_CHANNEL, message="Fault_Status", signal="FaultCode")
        for cycle in range(2):
            before = view.model.observed
            window.start_monitor()
            wait_until(lambda: view.model.observed > before+3 and graph.model.accepted >= 2)
            window.stop_monitor()
            wait_until(lambda: window.worker is None and window.buffer.pending_count == 0)
            assert view.model.entries[-1].receiver_run == cycle+1
        assert {entry.receiver_run for entry in view.model.entries} == {1,2}
        assert any(entry.decode_state == "Decode Error" for entry in view.model.entries)
        assert view.model.missing_timestamps and view.model.reversed_timestamps
        assert all(entry.fault_status == "Status Unknown" for entry in view.model.entries)
        view.code_filter.setCurrentIndex(view.code_filter.findData(1))
        assert view.table_model.rowCount() > 0 and all(entry.signals["FaultCode"] == 1 for entry in view.table_model.entries)
        view.code_filter.setCurrentIndex(0)
        view.error_filter.setChecked(True)
        assert view.table_model.rowCount() > 0 and all(entry.decode_state == "Decode Error" for entry in view.table_model.entries)
        view.table.selectRow(0)
        view.show_detail()
        assert "Decode Error" in view.details.toPlainText() and "DLC: 1" in view.details.toPlainText()
        assert window.grab().save(str(root/"fault-error-filter.png"))
        view.error_filter.setChecked(False)
        view.table.selectRow(0)
        view.show_detail()
        assert "FaultCode = 1" in view.details.toPlainText()
        assert window.grab().save(str(root/"fault-existing-dbc-fake.png"))
        window.start_monitor()
        wait_until(lambda: window.receiver_running())
        path = root/"fake-fault.jsonl"
        window.logging_view.set_output_path(path)
        window.logging_view.start_recording()
        wait_until(lambda: window.logging_session.snapshot().written >= 3)
        received = view.model.observed
        graph_before = graph.model.accepted
        wait_until(lambda: view.model.observed > received and graph.model.accepted > graph_before)
        receiver, writer = window.worker, window.logging_session._thread
        assert window.close() and not receiver.isRunning() and not writer.is_alive()
        assert view._closed and not window.graph_view.timer.isActive() and not window.timer.isActive()
        assert all(bus.shutdown_calls == 1 and bus.send_calls == 0 for bus in transports)
        snap = window.logging_session.snapshot()
        assert snap.closed and len(list(read_jsonl(path))) == snap.written
        print(json.dumps({"platform":app.platformName(),"window_exposed":True,
                          "mock_existing_fixture":True,"existing_repository_dbc_fake_only":True,
                          "code_channel_message_filters_auto_tests":True,"error_filter_details":True,
                          "timestamp_missing_reversed_preserved":True,"status":"Status Unknown",
                          "clear_keeps_logging_graph_cache_raw":True,"source_reload_isolation":True,"source_change_waits_ui_unlocked":True,
                          "repeated_receiver_runs":2,"graph_and_logging_concurrent":True,
                          "written":snap.written,"active_close":True,"fake_transports_released":len(transports),
                          "application_tx_calls":0,"hardware":"NOT VERIFIED","human_manual":"NOT VERIFIED"}))
    finally:
        # 실패해도 활성 Receiver/Writer가 native process에 남지 않도록 정리한다.
        window.stop_monitor()
        if window.worker is not None:
            assert window.worker.wait(NATIVE_WAIT_MS)
        window.logging_session.stop()
        assert window.logging_session.wait(NATIVE_WAIT_MS/1000)
        app.processEvents()
        window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
