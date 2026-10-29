"""기존 화면 snapshot의 읽기 전용 요약. ECU Health/Fault/KPI를 판정하지 않는다."""
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QLayout, QSizePolicy, QVBoxLayout, QWidget
from .theme import role
from .network_view import NetworkView
from .ui_components import Disclosure
from PySide6.QtWidgets import QWidgetItem

DASHBOARD_COLUMNS = 2
DASHBOARD_COMPACT_WIDTH = 700
CARD_TITLES = (
    ("connection", "CAN CONNECTION"),
    ("frames", "RECEIVED / DISPLAY"),
    ("ecu", "ECU OBSERVATION"),
    ("fault", "FAULT OBSERVATION"),
    ("logging", "RAW RECORDING"),
    ("vehicle", "VEHICLE STATUS"),
)


class DashboardView(QWidget):
    def __init__(self, owner, parent=None):
        # 새 Worker/Timer 없이 MainWindow의 기존 UI 갱신을 사용한다.
        super().__init__(parent)
        self.owner = owner
        self.cards = {}
        self._boxes = []
        self._columns = None
        layout = QVBoxLayout(self)
        # 넓은 배치의 최소 너비를 ScrollArea에 고정하지 않는다.
        layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.source_label = role(QLabel(), "badge")
        self.source_label.setWordWrap(True)
        layout.addWidget(self.source_label)
        note = role(QLabel("수신 관측 요약 · Observed ≠ Healthy · Fault 상태 Unknown · Hardware NOT VERIFIED"), "muted")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.summary_grid = QGridLayout()
        self.grid = QGridLayout()
        self.summary_grid.setSpacing(6)
        self.grid.setSpacing(6)
        self.details = []
        for key, title in CARD_TITLES:
            box = role(QFrame(), "card")
            card = QVBoxLayout(box)
            card.setContentsMargins(10, 7, 10, 7)
            card.setSpacing(3)
            from PySide6.QtCore import Qt
            card.setAlignment(Qt.AlignmentFlag.AlignTop)
            card.addWidget(role(QLabel(title), "muted"))
            value = role(QLabel("No Data"), "metric")
            value.setWordWrap(True)
            detail = role(QLabel(), "muted")
            detail.setWordWrap(True)
            card.addWidget(value)
            if key in ("logging", "vehicle"):
                card.addWidget(detail)
            else:
                self.details.append(Disclosure(box, card, "Details", [QWidgetItem(detail)]))
            self.cards[key] = (value, detail)
            self._boxes.append(box)
        layout.addLayout(self.summary_grid)
        layout.addLayout(self.grid)
        self.network_view = NetworkView(owner, self)
        self.network_section = Disclosure(self, layout, "Network / KPI — observed RX",
                                         [QWidgetItem(self.network_view)])
        self.scope_label = role(QLabel(
            "Network / KPI: observed RX panel above · 실제 Fault Injection: Not Implemented\n"
            "Driver Input: VCU UART is available when connected · CAN TX remains blocked"), "warning")
        self.scope_label.setWordWrap(True)
        layout.addWidget(self.scope_label)
        layout.addStretch()
        self._arrange(DASHBOARD_COLUMNS)

    def _arrange(self, columns):
        # 작은 화면에서는 카드만 재배치하며 데이터/상태는 변경하지 않는다.
        if columns == self._columns:
            return
        self._columns = columns
        for box in self._boxes:
            self.grid.removeWidget(box)
            self.summary_grid.removeWidget(box)
        # 상단 관측 요약은 작은 화면에서도 2×2, 상세 카드는 기존 1/2열 정책을 따른다.
        summary_columns = 4 if columns == DASHBOARD_COLUMNS else 2
        for index, box in enumerate(self._boxes[:4]):
            self.summary_grid.addWidget(box, index // summary_columns, index % summary_columns)
        for index, box in enumerate(self._boxes[4:]):
            self.grid.addWidget(box, index // columns, index % columns)
        for column in range(DASHBOARD_COLUMNS):
            self.grid.setColumnStretch(column, 1 if column < columns else 0)
        for column in range(4):
            self.summary_grid.setColumnStretch(column, 1 if column < summary_columns else 0)

    def resizeEvent(self, event):
        # Qt 필수 override. 카드 너비만 반응형으로 바꾸고 추가 타이머는 만들지 않는다.
        # 넓은 카드의 minimumSize가 축소를 막아도 실제 viewport 폭으로 판단한다.
        available_width = self.parentWidget().width() if self.parentWidget() is not None else event.size().width()
        self._arrange(1 if available_width < DASHBOARD_COMPACT_WIDTH else DASHBOARD_COLUMNS)
        super().resizeEvent(event)

    def refresh(self):
        # 기존 표시/immutable snapshot만 읽는다. CAN/DBC 해석이나 ECU 추론은 하지 않는다.
        owner = self.owner
        self.network_view.refresh()
        self.source_label.setText(owner.selected_source_text())
        self.cards["connection"][0].setText(owner.status_label.text())
        self.cards["connection"][1].setText("선택 Source와 연결 성공은 별개 · " + owner.connection_view.status_label.text())
        self.cards["frames"][0].setText(owner.counter_label.text())
        self.cards["frames"][1].setText(owner.processed_label.text() + "\n" + owner.drop_label.text())
        observed = [ecu for ecu, labels in owner.ecu_view.cards.items()
                    if labels["state"].text() == "State: Observed"]
        self.cards["ecu"][0].setText(f"Observed: {len(observed)}" if observed else "No Data")
        self.cards["ecu"][1].setText(", ".join(observed) if observed else "명시 매핑 후 수신 관측 · Healthy/Online 판정 없음")
        fault = owner.fault_monitor_view.model
        self.cards["fault"][0].setText(f"Observed: {fault.observed}" if fault.observed else "No Data")
        self.cards["fault"][1].setText(
            f"Status Unknown · Retained: {len(fault.entries)} · Omitted: {fault.history_omitted}\n"
            "관측 건수는 Active Fault 수가 아닙니다.")
        log = owner.logging_session.snapshot()
        self.cards["logging"][0].setText(log.state.value)
        self.cards["logging"][1].setText(
            f"Logged: {log.written} · Queue dropped: {log.queue_dropped} · Unconfirmed: {log.unconfirmed}"
            + (f"\n{log.error}" if log.error else ""))
        table = owner.vehicle_view.table
        values = []
        for row in range(table.rowCount()):
            name, value, unit, state = (table.item(row, c) for c in (0, 3, 4, 7))
            if all(cell is not None for cell in (name, value, unit, state)):
                values.append(f"{name.text()}: {value.text()} {unit.text()} · {state.text()}")
        self.cards["vehicle"][0].setText("No Data" if not owner.decode_session.loader.is_loaded else "Explicit DBC mapping")
        self.cards["vehicle"][1].setText("\n".join(values) or "No DBC · 사용자 Signal 매핑 필요")
