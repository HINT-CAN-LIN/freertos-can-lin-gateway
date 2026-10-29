"""Windows Graph Native Smoke. Mock/Fake Live TEST ONLY; 실제 장치 연결 없음."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys
from time import time
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from pc_diagnostic import DbcCodec, DbcLoader
from pc_diagnostic.gui.window import MainWindow
from pc_diagnostic.logger import read_jsonl
from fake_live import FakeLive, FAKE_CHANNEL
from gui_native_smoke import wait_until, NATIVE_WAIT_MS

TEST_VALUES = (-10, -5, 0, 5, 10)


def choose_graph(window, channel):
    # user 선택을 TEST ONLY Channel/Message/Signal로 명시적으로 수행한다.
    graph = window.graph_view
    graph.observe_channel(channel)
    graph.channel_combo.setCurrentIndex(next(i for i in range(1, graph.channel_combo.count())
        if graph.channel_combo.itemData(i) == channel))
    graph.message_combo.setCurrentIndex(next(i for i in range(1, graph.message_combo.count())
        if graph.message_combo.itemData(i)[0] == "TestOnlySample"))
    graph.signal_combo.setCurrentIndex(graph.signal_combo.findData("Measurement"))
    graph.apply_signal()
    return graph


def main():
    # 산출물은 새 전용 폴더만 사용한다. 파일 overwrite/실기 KPI를 생성하지 않는다.
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    root = Path(args.output_dir)
    assert root.is_dir()
    app = QApplication([])
    assert app.platformName() == "windows"
    fixture = Path(__file__).parent / "fixtures/test_only.dbc"
    codec = DbcCodec(DbcLoader().load(fixture))
    transports = []
    class ChangingFake(FakeLive):
        def recv(self, timeout=None):
            # 기존 TEST ONLY Signal만 encoder로 생성한다. 제품 Worker에서 DEMO를 생성하지 않는다.
            self.recv_calls += 1
            self.closed.wait(0.02)
            if self.closed.is_set():
                return None
            value = TEST_VALUES[self.index % len(TEST_VALUES)]
            frame = codec.encode("TestOnlySample", {"Measurement":value,"Mode":1,"Counter":self.index % 256})
            self.index += 1
            return replace(frame, channel=FAKE_CHANNEL, timestamp=time(), is_rx=True)
    def factory(settings):
        # 실제 Backend 대신 TEST ONLY 주입임을 Source banner에서 확인한다.
        bus = ChangingFake()
        transports.append(bus)
        return bus
    window = MainWindow(live_interface_factory=factory)
    try:
        window.show()
        assert QTest.qWaitForWindowExposed(window, NATIVE_WAIT_MS)
        assert window.load_dbc(fixture)
        graph = choose_graph(window, "DEMO/TEST ONLY")
        window.tabs.setCurrentWidget(graph)
        window.start_monitor()
        wait_until(lambda: len(graph.canvas.samples) >= 3)
        assert graph.model.latest_value == -10.0 and graph.model.unit == "test_unit"
        graph.toggle_pause()
        frozen = graph.canvas.samples
        before = graph.model.accepted
        wait_until(lambda: graph.model.accepted > before)
        assert graph.canvas.samples == frozen
        graph.toggle_pause()
        assert len(graph.canvas.samples) > len(frozen)
        window.stop_monitor()
        wait_until(lambda: window.worker is None)
        assert window.grab().save(str(root / "mock-graph.png"))
        window.connection_view.mode_combo.setCurrentText("Live")
        window.connection_view.backend_combo.setCurrentIndex(window.connection_view.backend_combo.findData("slcan"))
        window.connection_view.channel_edit.setText("FAKE_GRAPH_TEST_ONLY")
        assert graph.model.selection is None and not graph.canvas.samples
        graph = choose_graph(window, FAKE_CHANNEL)
        for cycle in range(2):
            previous = graph.model.accepted
            window.start_monitor()
            wait_until(lambda: graph.model.accepted > previous)
            window.stop_monitor()
            wait_until(lambda: window.worker is None)
        window.start_monitor()
        wait_until(lambda: len(graph.canvas.samples) >= 8 and window.receiver_running())
        assert len({sample.value for sample in graph.model.samples}) >= 3
        path = root / "graph-live.jsonl"
        window.logging_view.set_output_path(path)
        window.logging_view.start_recording()
        wait_until(lambda: window.logging_session.snapshot().written >= 3)
        graph.toggle_pause()
        frozen = graph.canvas.samples
        previous_samples, previous_written = graph.model.accepted, window.logging_session.snapshot().written
        wait_until(lambda: graph.model.accepted > previous_samples and window.logging_session.snapshot().written > previous_written)
        assert graph.canvas.samples == frozen
        graph.toggle_pause()
        assert window.grab().save(str(root / "fake-live-graph.png"))
        raw_count = window.table.rowCount()
        cached = window.decode_session.service.cache.snapshot()
        stats = window.ecu_view.model.statistics.processed_rx
        graph.clear_graph()
        assert not graph.canvas.samples and not graph.model.samples
        assert window.table.rowCount() == raw_count and window.decode_session.service.cache.snapshot() == cached
        assert window.ecu_view.model.statistics.processed_rx == stats
        wait_until(lambda: len(graph.canvas.samples) >= 2)
        receiver, writer = window.worker, window.logging_session._thread
        assert window.close() and not receiver.isRunning() and not writer.is_alive()
        assert not graph.timer.isActive() and all(bus.shutdown_calls == 1 and bus.send_calls == 0 for bus in transports)
        snap = window.logging_session.snapshot()
        assert snap.closed and len(list(read_jsonl(path))) == snap.written
        print(json.dumps({"platform":app.platformName(),"window_exposed":True,
            "mock_graph":True,"fake_live_variable_graph":True,"unit":"test_unit",
            "pause_keeps_collection_and_logging":True,"clear_graph_only":True,
            "source_transition_clears_graph":True,"repeated_live":True,
            "logging_written":snap.written,"active_close":True,"graph_timer_stopped":True,
            "transports_released":len(transports),"application_tx_calls":0,
            "human_manual":"NOT VERIFIED","hardware":"NOT VERIFIED"}))
    finally:
        # 실패한 assertion도 활성 Worker/Writer를 남겨 두지 않는다.
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
