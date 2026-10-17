"""Windows Raw Pause/Export smoke. Mock 주입 전용이며 실기/사용자 수동 시험이 아니다."""
import argparse
import csv
import json
from pathlib import Path
import can
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from pc_diagnostic.gui.window import MainWindow
from gui_native_smoke import wait_until, NATIVE_WAIT_MS
from test_fault_monitor_view import select_fault_source, feed
from test_fault_history import REPOSITORY_DBC, fault_frame
from test_graph_view import select_graph

SIZES = ((800, 600), (1024, 768), (1280, 920))


def main():
    # 새 외부 증적 폴더에만 파일을 만들며 실제 CAN Bus 생성은 즉시 실패시킨다.
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    output = Path(args.output_dir)
    assert output.is_dir()
    app = QApplication([])
    assert app.platformName() == "windows"
    bus_calls = []
    def forbidden(*args, **kwargs):
        # 물리 CAN 연결은 이번 자동 검증 범위 밖이다.
        bus_calls.append(True)
        raise AssertionError("Hardware is outside Mock export smoke")
    can.Bus = forbidden
    window = MainWindow(live_interface_factory=forbidden)
    captures = []
    exports = []
    def settle():
        # Qt layout 완료 후 실제 geometry를 확인한다.
        for _ in range(5):
            app.processEvents()
    def expose(widget):
        # 작은 창에서도 새 조작을 스크롤하여 완전히 노출할 수 있어야 한다.
        window.page_scroll.ensureWidgetVisible(widget)
        settle()
        rect = widget.rect()
        rect.moveTopLeft(widget.mapTo(window.page_scroll.viewport(), rect.topLeft()))
        assert window.page_scroll.viewport().rect().contains(rect), (widget.accessibleName(), rect)
    def capture(name):
        # Windows native QWidget 캡처이며 합성 이미지가 아니다.
        settle()
        assert window.grab().save(str(output / name))
        captures.append(name)
    try:
        window.show()
        assert QTest.qWaitForWindowExposed(window, NATIVE_WAIT_MS)
        fixture = Path(__file__).parent / "fixtures/test_only.dbc"
        assert window.load_dbc(fixture)
        fault = select_fault_source(window)
        graph = select_graph(window)
        window.tabs.setCurrentWidget(window.monitor_page)
        window.start_monitor()
        wait_until(lambda: window._processed >= 3)
        window.set_raw_paused(True)
        frozen = tuple(tuple(window.table.item(r, c).text() for c in range(5))
                       for r in range(window.table.rowCount()))
        before = window._processed
        graph_before = graph.model.accepted
        raw_path = output / "paused-raw.jsonl"
        window.logging_view.set_output_path(raw_path)
        window.logging_view.start_recording()
        wait_until(lambda: window._processed >= before + 4
                   and window.logging_session.snapshot().written >= 3)
        assert frozen == tuple(tuple(window.table.item(r, c).text() for c in range(5))
                               for r in range(window.table.rowCount()))
        assert graph.model.accepted > graph_before and fault.model.entries
        assert window.decode_session.service.cache.snapshot()
        window.stop_monitor()
        wait_until(lambda: window.worker is None and not window.logging_session.snapshot().active)
        assert window.raw_paused
        for width, height in SIZES:
            window.resize(width, height)
            settle()
            assert (window.width(), window.height()) == (width, height)
            window.tabs.setCurrentWidget(window.monitor_page)
            expose(window.pause_button)
            expose(window.export_controls.widgets["decoded"][2])
            capture(f"paused-monitor-{width}x{height}.png")
            window.tabs.setCurrentWidget(fault)
            expose(window.export_controls.widgets["fault"][2])
            capture(f"fault-export-{width}x{height}.png")
        window.tabs.setCurrentWidget(window.monitor_page)
        QTest.mouseClick(window.pause_button, Qt.MouseButton.LeftButton)
        assert not window.raw_paused
        assert window.table.rowCount() == len(window.raw_history.records)
        assert all(window.table.item(r, 0).data(Qt.ItemDataRole.UserRole) is record.observation
                   for r, record in enumerate(window.raw_history.snapshot()))
        for kind in ("decoded", "fault"):
            for format in ("csv", "jsonl"):
                path = output / (kind + "." + format)
                snapshot = window.export_controls.capture(kind)
                assert window.export_controls.export_to(kind, path, format=format)
                wait_until(lambda: not window.export_controls.exporter.writer.snapshot().active)
                state = window.export_controls.exporter.writer.snapshot()
                assert state.closed and not state.error
                window.export_controls.refresh()
                if format == "jsonl":
                    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
                else:
                    with path.open(encoding="utf-8", newline="") as stream:
                        rows = list(csv.DictReader(stream))
                assert len(rows) == snapshot.row_count
                assert all(row["source"] == window._source_text for row in rows)
                assert "Mock" in window._source_text and "ONLY" in window._source_text
                exports.append({"kind": kind, "format": format, "rows": len(rows)})
        assert "Export completed" in window.error_area.toPlainText()
        # Repository DBC는 명시적 읽기 전용 로드하고 기존 Encoder 시험 helper만 사용한다.
        assert window.load_dbc(REPOSITORY_DBC)
        select_fault_source(window, message="Fault_Status")
        feed(window, fault_frame(window.decode_session, code=0, node=1, channel="DEMO/TEST ONLY"))
        path = output / "fault-contract.jsonl"
        assert window.export_controls.export_to("fault", path)
        wait_until(lambda: not window.export_controls.exporter.writer.snapshot().active)
        row = json.loads(path.read_text(encoding="utf-8"))
        assert row["signals"]["ECUOffline"] == 1 and row["dbc_choices"]["ECUOffline"] == "VCU"
        assert row["signals"]["FaultCode"] == 0 and row["fault_status"] == "Status Unknown"
        window.set_raw_paused(True)
        window.clear_monitor()
        assert window.raw_paused and not window.raw_history.records
        window.connection_view.mode_combo.setCurrentText("Live")
        assert not window.raw_paused and not window.driver_control_view.live_tx_button.isEnabled()
        assert "Live" in window._source_text and not bus_calls
        capture("live-not-connected-tx-blocked.png")
        window.connection_view.mode_combo.setCurrentText("Mock")
        assert window.load_dbc(fixture)
        for _ in range(2):
            before = window._processed
            window.start_monitor()
            wait_until(lambda: window._processed > before)
            window.stop_monitor()
            wait_until(lambda: window.worker is None)
        window.start_monitor()
        wait_until(window.receiver_running)
        worker = window.worker
        assert window.close() and not worker.isRunning()
        assert not window.timer.isActive() and not window.age_timer.isActive() and not graph.timer.isActive()
        assert not window.export_controls.exporter.writer.snapshot().active
        print(json.dumps({"platform":app.platformName(),"pause_rx_decode_cache_graph_logging":True,
            "resume_exact_snapshot":True,"clear_source_repeated_start_stop_close":True,
            "exports":exports,"fault_node_enum_status_unknown":True,"screenshots":captures,
            "live_tx_blocked":True,"hardware_bus_calls":len(bus_calls),
            "manual":"NOT VERIFIED","hardware":"NOT VERIFIED"}))
    finally:
        # 실패 시에도 기존 종료 계약으로 Receiver와 파일 Writer를 해제한다.
        window.stop_monitor()
        if window.worker is not None:
            assert window.worker.wait(NATIVE_WAIT_MS)
        window.logging_session.stop()
        assert window.logging_session.wait(NATIVE_WAIT_MS / 1000)
        window.export_controls.exporter.writer.stop()
        assert window.export_controls.exporter.wait(NATIVE_WAIT_MS / 1000)
        app.processEvents()
        window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
