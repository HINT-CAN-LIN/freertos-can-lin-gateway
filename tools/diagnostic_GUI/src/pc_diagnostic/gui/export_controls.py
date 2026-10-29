"""명시적 파일 선택과 Export 상태 표시. 수신/Decode/Logger를 중지하지 않는다."""
from PySide6.QtWidgets import QComboBox, QFileDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from .observation_export import ObservationExport, ExportSnapshot, decoded_snapshot, fault_snapshot
from .logging_session import LOG_CLOSE_SECONDS
from .theme import role
from .ui_components import ElidedLabel


class ExportControls:
    def __init__(self, owner, *, exporter=None):
        # 기존 UI timer로 상태를 읽는다. 자체 Timer/Worker를 추가하지 않는다.
        self.owner = owner
        self.exporter = exporter or ObservationExport()
        self.selecting = False
        self.notice = None
        self.close_notice = None
        self.widgets = {}
        for kind, page in (("decoded", owner.monitor_page), ("fault", owner.fault_monitor_view),
                           ("network", owner.dashboard_view.network_view)):
            widget = QWidget(page)
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(3)
            row = QHBoxLayout()
            combo = QComboBox()
            combo.addItem("JSONL", "jsonl")
            combo.addItem("CSV", "csv")
            combo.setMaximumWidth(100)
            combo.setAccessibleName(kind + " export format")
            button = QPushButton({"decoded": "Export Decoded...", "fault": "Export Fault History...",
                                  "network": "Export Network KPI..."}[kind])
            button.setAccessibleName(kind + " export")
            state = ElidedLabel()
            row.addWidget(combo)
            row.addWidget(button)
            row.addWidget(state, 1)
            layout.addLayout(row)
            scope = role(QLabel(), "muted")
            scope.setWordWrap(True)
            layout.addWidget(scope)
            page.layout().insertWidget(1, widget)
            self.widgets[kind] = (widget, combo, button, state, scope)
            button.clicked.connect(lambda checked=False, value=kind: self.choose(value))
        self.refresh()

    def capture(self, kind):
        # Capture는 main thread에서 불변 tuple만 고정한다. Cache backfill/별도 Decode는 없다.
        if kind == "decoded":
            return decoded_snapshot(self.owner.raw_history, self.owner.decode_session)
        if kind == "fault":
            return fault_snapshot(self.owner.fault_monitor_view.model)
        if kind == "network":
            records = self.owner.network_model.snapshot_records(self.owner.decode_session.loader)
            if not records:
                raise ValueError("No Data: no retained Network identities.")
            return ExportSnapshot("network", records)
        raise ValueError("unsupported export kind")

    def export_to(self, kind, path, *, format="jsonl"):
        # Native/자동화에서도 명시적인 경로를 요구하며 실제 UI와 같은 snapshot 경로를 사용한다.
        if self.owner._closing or self.selecting or self.exporter.writer.snapshot().active:
            return False
        try:
            snapshot = self.capture(kind)
            started = self.exporter.start(snapshot, path, format=format)
        except Exception as exc:
            self.owner.error_area.appendPlainText(f"Export Error ({type(exc).__name__}): {exc}")
            return False
        self.refresh()
        return started

    def choose(self, kind):
        # 모달 dialog 전에 snapshot을 고정해 nested event loop 중 새 수신/Source와 섞지 않는다.
        if self.owner._closing or self.selecting or self.exporter.writer.snapshot().active:
            return
        try:
            snapshot = self.capture(kind)
        except ValueError as exc:
            self.owner.error_area.appendPlainText(f"Export: {exc}")
            return
        self.selecting = True
        self.refresh()
        try:
            format = self.widgets[kind][1].currentData()
            path, _ = QFileDialog.getSaveFileName(self.owner, "Export observation snapshot — new file only", "",
                                                  "CSV (*.csv)" if format == "csv" else "JSONL (*.jsonl)",
                                                  options=QFileDialog.Option.DontConfirmOverwrite)
            if path and not self.owner._closing:
                self.exporter.start(snapshot, path, format=format)
        except Exception as exc:
            self.owner.error_area.appendPlainText(f"Export Error ({type(exc).__name__}): {exc}")
        finally:
            self.selecting = False
            self.refresh()

    def refresh(self):
        # 수신 상태와 Export 상태를 분리한다. Export 실패에 owner.show_error를 호출하지 않는다.
        state = self.exporter.writer.snapshot()
        for kind, (_, combo, button, label, scope) in self.widgets.items():
            try:
                snapshot = self.capture(kind)
            except ValueError as exc:
                count, rows, detail = 0, 0, str(exc)
            else:
                count, rows = len(snapshot.records), snapshot.row_count
                detail = {"decoded": "current DBC session RX", "fault": "all retained Fault observations",
                          "network": "processed RX identity aggregates / current statistics interval"}[kind]
            button.setEnabled(bool(count) and not self.selecting and not state.active and not self.owner._closing)
            combo.setEnabled(not self.selecting and not state.active and not self.owner._closing)
            extra = (" | Event store: Not Implemented; no reconstructed events" if kind == "fault" else
                     " | Hardware NOT VERIFIED; Jitter Definition Pending" if kind == "network" else
                     " | all retained frames; display filters ignored")
            scope.setText(f"{count} records / {rows} rows · {detail}" + extra)
            summary = f"Export: {state.state.value}"
            if state.error:
                summary += " · Error / partial file possible"
            label.set_full_text(summary)
        key = state.generation, state.state, state.error
        if state.generation and not state.active and self.notice != key:
            self.notice = key
            if state.error:
                self.owner.error_area.appendPlainText("Export Error: " + state.error + " · Partial file possible; existing files protected.")
            elif state.closed and state.written == 1:
                self.owner.error_area.appendPlainText(
                    f"Export completed: {self.exporter.snapshot.kind}, {self.exporter.snapshot.row_count} rows · {state.path}")

    def prepare_close(self):
        # 진행 중 I/O를 강제 종료하지 않는다. 첫 Error Close는 창을 유지해 사용자에게 보인다.
        if self.selecting:
            self.owner.error_area.appendPlainText("Export file selection is open; close the dialog before exiting.")
            return False
        self.exporter.writer.stop()
        if not self.exporter.wait(LOG_CLOSE_SECONDS):
            self.owner.error_area.appendPlainText("Export stop timed out; close again after the writer finishes. Partial file possible.")
            return False
        state = self.exporter.writer.snapshot()
        key = state.generation, state.error
        if state.error and self.close_notice != key:
            self.close_notice = key
            self.refresh()
            self.owner.error_area.appendPlainText("Export ended with error; review the partial file and close again to exit.")
            return False
        return True
