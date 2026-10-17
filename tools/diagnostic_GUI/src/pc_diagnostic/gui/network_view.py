"""Network/KPI 읽기 전용 Dashboard 패널. CAN 통신과 계산은 모델에 둔다."""
import json
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractItemView, QHeaderView, QLabel, QPlainTextEdit,
                              QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)
from .theme import role

COLUMNS = (
    ("channel", "Channel"), ("arbitration_id", "CAN ID"), ("format", "Format"),
    ("message_name", "Message"), ("frame_count", "RX Count"),
    ("mean_period_s", "Mean (s)"), ("min_period_s", "Min (s)"), ("max_period_s", "Max (s)"),
    ("expected_period_ms", "Expected (ms)"), ("mean_minus_expected_ms", "Mean - Expected (ms)"),
    ("last_timestamp", "Last timestamp (s)"), ("observed_duration_s", "Observed span (s)"),
    ("observed_frame_rate_hz", "Observed rate (Hz)"), ("timing_status", "Timing status"),
    ("comparison_status", "Comparison scope"),
)
TABLE_MIN_HEIGHT = 220
DETAILS_MAX_HEIGHT = 160


class NetworkView(QWidget):
    def __init__(self, owner, parent=None):
        # 기존 Dashboard/주기 갱신을 재사용하며 Worker/Timer를 만들지 않는다.
        super().__init__(parent)
        self.owner = owner
        self._version = None
        self.records = ()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.source_label = role(QLabel(), "badge")
        self.summary_label = QLabel("No Data")
        self.kpi_label = role(QLabel(
            "Jitter: Definition Pending · Bus Load: N/A · Controller state: Unsupported\n"
            "Observed RX ≠ complete bus capture / ECU health · Hardware NOT VERIFIED"), "warning")
        for label in (self.source_label, self.summary_label, self.kpi_label):
            label.setWordWrap(True)
            label.setMinimumWidth(0)
            layout.addWidget(label)
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setAccessibleName("CAN Network observed statistics")
        self.table.setHorizontalHeaderLabels([title for _, title in COLUMNS])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setMinimumHeight(TABLE_MIN_HEIGHT)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        for index in range(len(COLUMNS)):
            self.table.setColumnWidth(index, 150 if index < 13 else 260)
        layout.addWidget(self.table)
        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setMaximumHeight(DETAILS_MAX_HEIGHT)
        self.details.setAccessibleName("Network KPI definition and selected record details")
        layout.addWidget(self.details)
        self.table.itemSelectionChanged.connect(self.show_details)
        self.refresh()

    def refresh(self):
        # 동일 모델 세대의 표는 다시 만들지 않는다. MainWindow의 기존 Qt timer만 사용한다.
        model, session = self.owner.network_model, self.owner.decode_session
        self.source_label.setText(model.source + " · " + model.source_kind + " · Hardware NOT VERIFIED")
        self.summary_label.setText(
            f"Processed RX: {model.processed_rx} · Tracked CAN IDs: {model.observed_id_count} · "
            f"Identities: {len(model.entries)}/{model.capacity}\n"
            f"Buffer dropped: {model.buffer_dropped} · Capacity excluded: {model.capacity_excluded} · "
            f"Error frames provided: {model.error_frames}\n"
            "Observation span: per identity / receiver-run segments; no mixed-channel clock total")
        version = model.generation, session.session_id
        if version == self._version:
            return
        self._version = version
        self.records = model.snapshot_records(session.loader)
        selected = self.table.currentRow()
        self.table.setRowCount(len(self.records))
        for row, record in enumerate(self.records):
            for column, (key, _) in enumerate(COLUMNS):
                value = record.get(key)
                if key == "format":
                    value = ("ERROR" if record["is_error_frame"] else "EXT" if record["is_extended_id"] else "STD")
                    if record["is_remote_frame"]:
                        value += " RTR"
                elif key == "arbitration_id":
                    value = f"0x{value:X}"
                elif key == "channel":
                    value = f"{value!r} ({record['channel_type']})"
                elif isinstance(value, float):
                    value = f"{value:.9g}"
                text = "N/A" if value is None else str(value)
                item = QTableWidgetItem(text)
                item.setToolTip(text)
                self.table.setItem(row, column, item)
        if 0 <= selected < len(self.records):
            self.table.selectRow(selected)
        self.show_details()

    def show_details(self):
        # 전체 정밀도/출처는 상세에서 유지한다. 임의 threshold PASS/FAIL은 없다.
        row = self.table.currentRow()
        record = dict(self.records[row]) if 0 <= row < len(self.records) else None
        text = ("No Data" if not self.records else "Select a CAN identity for exact values / provenance.")
        text += ("\nPeriod = positive consecutive Raw timestamp deltas within receiver runs. "
                 "Mean/min/max and rate are descriptive observations. Timestamp accuracy NOT VERIFIED. "
                 "Drop/anomaly => timing N/A. No sender-task Jitter/packet loss/latency/Health inference.")
        if record is not None:
            text += "\n" + json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False)
        self.details.setPlainText(text)
