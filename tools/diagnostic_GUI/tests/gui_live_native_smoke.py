"""Windows 실제 창의 Fake Live TEST ONLY smoke. 장치 접속/송신을 하지 않는다."""
import argparse
import csv
import json
from pathlib import Path
import sys
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from pc_diagnostic.gui.window import MainWindow
from pc_diagnostic.gui.vehicle_status import SignalMapping
from pc_diagnostic.gui.ecu_observation import MessageMapping
from pc_diagnostic.gui.logging_session import LoggingState
from pc_diagnostic.logger import RawCanLogger, read_jsonl
from fake_live import FakeLive, FAKE_CHANNEL
from gui_native_smoke import wait_until, NATIVE_WAIT_MS


def main():
    # 생성 산출물은 호출자가 지정한 새 시험 폴더에만 쓴다. 기존 파일은 덮어쓰지 않는다.
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    root = Path(args.output_dir)
    assert root.is_dir()
    app = QApplication([])
    assert app.platformName() == "windows"
    buses = []
    def factory(settings):
        # Native 검증은 Fake backend이며 실제 CANable 결과가 아니다.
        bus = FakeLive()
        buses.append(bus)
        return bus
    window = MainWindow(live_interface_factory=factory)
    results = []
    try:
        window.show()
        assert QTest.qWaitForWindowExposed(window, NATIVE_WAIT_MS)
        view = window.connection_view
        view.mode_combo.setCurrentText("Live")
        view.backend_combo.setCurrentIndex(view.backend_combo.findData("slcan"))
        view.channel_edit.setText("FAKE_PORT_TEST_ONLY")
        fixture = Path(__file__).parent / "fixtures/test_only.dbc"
        assert window.load_dbc(fixture)
        session = window.decode_session
        window.vehicle_view.model.bind("DBC Observation",
            SignalMapping("TestOnlySample", "Measurement", FAKE_CHANNEL, True, True), session)
        mapping = MessageMapping("TestOnlySample", FAKE_CHANNEL, 1617, False, True, True)
        window.ecu_view.model.bind("VCU", mapping, session)
        window.ecu_view.model.bind_fault(mapping, session)
        window.start_monitor()
        wait_until(lambda: window.table.rowCount() >= 4 and window.receiver_running())
        assert "Connected" in view.status_label.text()
        assert window.vehicle_view.table.item(5, 3).text() == "-10.0"
        assert window.ecu_view.cards["VCU"]["state"].text() == "State: Observed"
        assert window.ecu_view.statistics_table.rowCount() == 2
        assert window.ecu_view.fault_table.rowCount() == 3
        assert "TEST ONLY" in window.banner.text()
        accepted = []
        original = window.logging_session.accept
        def tracked(frame):
            # 동일 Raw 객체를 Logger 계약과 byte 비교할 수 있도록 순서만 기록한다.
            result = original(frame)
            if result:
                accepted.append(frame)
            return result
        window.logging_session.accept = tracked
        # Worker는 생성 때 sink를 보관하므로 다음 실행부터 이 tracker를 사용한다.
        window.stop_monitor()
        wait_until(lambda: window.worker is None)
        for fmt in ("jsonl", "csv"):
            accepted.clear()
            window.start_monitor()
            wait_until(lambda: window.receiver_running())
            logging = window.logging_view
            path = root / ("fake-live." + fmt)
            logging.set_output_path(path)
            logging.format_combo.setCurrentIndex(logging.format_combo.findData(fmt))
            logging.start_recording()
            wait_until(lambda: window.logging_session.snapshot().written >= 4)
            window.stop_monitor()
            wait_until(lambda: window.worker is None and not window.logging_session.snapshot().active)
            snapshot = window.logging_session.snapshot()
            assert snapshot.closed and snapshot.written == snapshot.received == len(accepted)
            reference = root / ("cli-reference." + fmt)
            with RawCanLogger(reference, format=fmt) as logger:
                for frame in accepted:
                    logger.write(frame)
            assert path.read_bytes() == reference.read_bytes()
            results.append({"format": fmt, "written": snapshot.written, "cli_bytes_equal": True})
        for tab, name in enumerate(("raw", "vehicle", "ecu", "logging")):
            window.tabs.setCurrentIndex(tab)
            app.processEvents()
            assert window.grab().save(str(root / (name + "-fake-live.png")))
        window.start_monitor()
        wait_until(lambda: window.receiver_running())
        window.logging_view.set_output_path(root / "active-close.jsonl")
        window.logging_view.format_combo.setCurrentIndex(0)
        window.logging_view.start_recording()
        wait_until(lambda: window.logging_session.snapshot().written > 1)
        receiver, writer = window.worker, window.logging_session._thread
        assert window.close() and not receiver.isRunning() and not writer.is_alive()
        assert all(bus.shutdown_calls == 1 and bus.send_calls == 0 for bus in buses)
        print(json.dumps({"platform": app.platformName(), "window_exposed": True,
            "source": "FAKE LIVE / TEST ONLY", "decode_cache_vehicle_ecu_fault": True,
            "statistics_std_ext": True, "captures": results, "active_close": True,
            "transports_released": len(buses), "application_tx_calls": 0,
            "human_manual": "NOT VERIFIED", "hardware": "NOT VERIFIED"}))
    finally:
        # assertion 실패에도 QThread/Writer가 활성 상태로 파괴되지 않도록 해제한다.
        window.stop_monitor()
        if window.worker is not None:
            assert window.worker.wait(NATIVE_WAIT_MS)
        window.logging_session.stop()
        assert window.logging_session.wait(NATIVE_WAIT_MS / 1000)
        app.processEvents()
        window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
