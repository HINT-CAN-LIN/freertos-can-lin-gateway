"""ECU/통계/Fault 읽기 전용 화면. 수신 및 Decode는 기존 계층에 위임한다."""
from PySide6.QtCore import Slot
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QGridLayout,
                              QGroupBox, QHeaderView, QLabel, QPushButton, QScrollArea,
                              QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget)
from ..dbc_loader import DbcLookupError
from .connection import MOCK_CHANNEL, MOCK_SOURCE_LABEL
from .ecu_observation import ECU_NAMES, LIN_ECUS, EcuObservationModel, MessageMapping
from .message_statistics import observation_age
from .vehicle_view import MAX_CHANNEL_CHOICES, channel_text

MAX_FAULT_SIGNAL_ROWS = 64
FAULT_TARGET = "Fault Observation"
STAT_HEADERS = ("Channel", "CAN ID", "Format", "DLC (latest)", "Processed RX Count",
                "First Seen", "Last Seen", "Age (s)", "DBC Message")
FAULT_HEADERS = ("Source Message", "Signal", "Last decoded RX value", "DBC Choice",
                 "Unit", "Value Timestamp", "Frame Timestamp", "Observation State")


def time_text(value, *, age=False):
    # 미수신/시각 미제공을 0으로 합성하지 않는다.
    return "unknown" if value is None else f"{value:.3f}" if age else f"{value:.6f}"


def source_text(mapping):
    # CAN 식별자와 channel 타입을 보존하여 출처를 구분한다.
    if mapping is None:
        return "Not Configured"
    kind = "EXT" if mapping.is_extended_id else "STD"
    signal = f".{mapping.signal_name}" if mapping.signal_name else ""
    can_id = "unknown" if mapping.arbitration_id is None else f"0x{mapping.arbitration_id:X}"
    return f"{mapping.message_name or '?'}{signal} [{can_id} {kind}] / {channel_text(mapping.channel)}"


def make_table(headers):
    # 모든 테이블은 읽기 전용이고 표시 행은 모델의 상한을 따른다.
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setAlternatingRowColors(True)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    table.horizontalHeader().setStretchLastSection(True)
    return table


def set_cells(table, row, values):
    # 긴 출처/오류는 tooltip에서도 확인할 수 있다.
    for column, value in enumerate(values):
        item = QTableWidgetItem(str(value))
        item.setToolTip(str(value))
        table.setItem(row, column, item)


class EcuObservationView(QWidget):
    def __init__(self, session, clock, parent=None):
        # Qt UI와 통계 모델은 GUI 메인 스레드만 소유한다.
        super().__init__(parent)
        self.session = session
        self.clock = clock
        self.model = EcuObservationModel()
        self._closed = False
        self._source_text = MOCK_SOURCE_LABEL
        self._source_is_mock = True
        self._received = self._buffer_dropped = self._pending = self._processed = 0
        layout = QVBoxLayout(self)
        self.source_label = QLabel()
        self.source_label.setWordWrap(True)
        layout.addWidget(self.source_label)
        policy = QLabel("Observed는 CAN RX 관측 사실입니다. "
                        "Healthy/Online 또는 개별 LIN ECU 정상 판정이 아닙니다. Age에 판정 기준 없음.")
        policy.setWordWrap(True)
        layout.addWidget(policy)
        controls = QGridLayout()
        self.target_combo = QComboBox()
        self.target_combo.addItems((*ECU_NAMES, FAULT_TARGET))
        self.channel_combo = QComboBox()
        self.message_combo = QComboBox()
        self.signal_combo = QComboBox()
        self.confirm_box = QCheckBox("출처/표시 목적 확인 (팀 Interface 승인이 아님)")
        self.apply_button = QPushButton("Apply mapping")
        self.remove_button = QPushButton("Remove mapping")
        for column, (label, widget) in enumerate((
                ("ECU / Fault target", self.target_combo), ("Channel", self.channel_combo),
                ("DBC Message / ID / Format", self.message_combo), ("LIN individual Signal", self.signal_combo))):
            controls.addWidget(QLabel(label), 0, column)
            controls.addWidget(widget, 1, column)
        controls.addWidget(self.confirm_box, 2, 0, 1, 2)
        controls.addWidget(self.apply_button, 2, 2)
        controls.addWidget(self.remove_button, 2, 3)
        layout.addLayout(controls)
        self.definition_label = QLabel()
        self.definition_label.setWordWrap(True)
        layout.addWidget(self.definition_label)
        self.coverage_label = QLabel()
        self.coverage_label.setWordWrap(True)
        layout.addWidget(self.coverage_label)
        self.tabs = QTabWidget()
        dashboard = QWidget()
        grid = QGridLayout(dashboard)
        self.cards = {}
        for index, ecu in enumerate(ECU_NAMES):
            box = QGroupBox(ecu)
            card_layout = QVBoxLayout(box)
            route = "Gateway 경유 CAN (LIN 직접 수신 아님)" if ecu in LIN_ECUS else "CAN 직접 관측"
            route_label = QLabel(route)
            route_label.setWordWrap(True)
            card_layout.addWidget(route_label)
            labels = {}
            for field in ("source", "state", "time", "count", "details"):
                label = QLabel()
                label.setWordWrap(True)
                labels[field] = label
                card_layout.addWidget(label)
            self.cards[ecu] = labels
            grid.addWidget(box, index // 2, index % 2)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(dashboard)
        self.tabs.addTab(scroll, "ECU Dashboard")
        self.statistics_table = make_table(STAT_HEADERS)
        self.tabs.addTab(self.statistics_table, "CAN Message Statistics")
        fault = QWidget()
        fault_layout = QVBoxLayout(fault)
        self.fault_label = QLabel()
        self.fault_label.setWordWrap(True)
        fault_layout.addWidget(self.fault_label)
        fault_note = QLabel("명시적으로 선택한 DBC Message의 읽기 전용 관측. "
                            "Fault 전파/Recovery 완료/실제 ECU 고장 검증이 아닙니다. DBC Choice는 파일 metadata 그대로.")
        fault_note.setWordWrap(True)
        fault_layout.addWidget(fault_note)
        self.fault_table = make_table(FAULT_HEADERS)
        fault_layout.addWidget(self.fault_table)
        self.tabs.addTab(fault, "Fault Observation")
        layout.addWidget(self.tabs, 1)
        self.message_combo.currentIndexChanged.connect(self.update_signals)
        self.channel_combo.currentIndexChanged.connect(self.source_changed)
        self.signal_combo.currentIndexChanged.connect(self.source_changed)
        self.target_combo.currentIndexChanged.connect(self.edit_mapping)
        self.apply_button.clicked.connect(self.apply_mapping)
        self.remove_button.clicked.connect(self.remove_mapping)
        self.refresh()

    def set_input_source(self, text, *, is_mock):
        # Fault/ECU/통계는 같은 Source 세션을 사용하며 실제 노드 정상 판정은 하지 않는다.
        self._source_text, self._source_is_mock = text, is_mock
        self.refresh()

    def definitions(self):
        # 공통 DBC Loader metadata만 조회하며 별도의 parse를 하지 않는다.
        return self.session.loader.get_messages() if self.session.loader.is_loaded else ()

    def reset_selectors(self):
        # 새 DBC 세션은 과거 연결/확인 상태를 승계하지 않는다.
        self.message_combo.clear()
        self.message_combo.addItem("Select message")
        for message in self.definitions():
            kind = "EXT" if message.is_extended_frame else "STD"
            self.message_combo.addItem(f"{message.name} [0x{message.frame_id:X} {kind}]", message.name)
        self.channel_combo.clear()
        self.channel_combo.addItem("Select channel")
        if self._source_is_mock:
            self.channel_combo.addItem(channel_text(MOCK_CHANNEL), MOCK_CHANNEL)
        self.confirm_box.setChecked(False)
        self.update_signals()

    def observe_channel(self, channel):
        # 관측한 Channel 목록도 기존 표시 상한을 따르며 0/'0'/None을 분리한다.
        if self._closed:
            return
        for index in range(1, self.channel_combo.count()):
            existing = self.channel_combo.itemData(index)
            if type(existing) is type(channel) and existing == channel:
                return
        if self.channel_combo.count() - 1 < MAX_CHANNEL_CHOICES:
            self.channel_combo.addItem(channel_text(channel), channel)

    @Slot()
    def update_signals(self, *_):
        # LIN은 개별 Signal을 반드시 선택해야 하며 첫 후보를 자동 선택하지 않는다.
        self.signal_combo.clear()
        self.signal_combo.addItem("No individual signal", None)
        name = self.message_combo.currentData()
        if name and self.session.loader.is_loaded:
            message = self.session.loader.get_message_by_name(name)
            for signal in message.signals:
                self.signal_combo.addItem(signal.name, signal.name)
            self.definition_label.setText(
                f"DBC senders: {', '.join(message.senders) or 'not defined'} (metadata only; ECU identity/Health 증거 아님). "
                f"{message.comment or ''}")
        else:
            self.definition_label.setText("No automatic Message/ECU mapping. LIN requires an individual Signal.")
        self.signal_combo.setEnabled(self.target_combo.currentText() != FAULT_TARGET)
        self.confirm_box.setChecked(False)

    @Slot()
    def source_changed(self, *_):
        # Source 변경은 이전 확인 체크를 무효화한다.
        self.confirm_box.setChecked(False)

    @Slot()
    def edit_mapping(self, *_):
        # ECU별 기존 사용자 선택만 복원하며 다른 카드의 출처를 자동 복사하지 않는다.
        target = self.target_combo.currentText()
        mapping = self.model.fault_mapping if target == FAULT_TARGET else self.model.mappings.get(target)
        self.message_combo.setCurrentIndex(0 if mapping is None else max(0, self.message_combo.findData(mapping.message_name)))
        self.channel_combo.setCurrentIndex(0)
        self.update_signals()
        if mapping is not None:
            for index in range(1, self.channel_combo.count()):
                value = self.channel_combo.itemData(index)
                if type(value) is type(mapping.channel) and value == mapping.channel and mapping.channel_selected:
                    self.channel_combo.setCurrentIndex(index)
                    break
            self.signal_combo.setCurrentIndex(max(0, self.signal_combo.findData(mapping.signal_name)))
            self.confirm_box.setChecked(mapping.source_confirmed)

    @Slot()
    def apply_mapping(self):
        # ID와 format은 선택된 실제 DBC 정의에서만 가져온다.
        if self._closed or not self.session.loader.is_loaded:
            return
        name = self.message_combo.currentData()
        message = None if name is None else self.session.loader.get_message_by_name(name)
        target = self.target_combo.currentText()
        mapping = MessageMapping(name, self.channel_combo.currentData(),
                                 None if message is None else message.frame_id,
                                 None if message is None else message.is_extended_frame,
                                 self.channel_combo.currentIndex() > 0, self.confirm_box.isChecked(),
                                 None if target == FAULT_TARGET else self.signal_combo.currentData())
        if target == FAULT_TARGET:
            self.model.bind_fault(mapping, self.session)
        else:
            self.model.bind(target, mapping, self.session)
        self.refresh()

    @Slot()
    def remove_mapping(self):
        # 표시 연결만 제거하며 기존 Cache/통계/다른 ECU를 변경하지 않는다.
        if self._closed:
            return
        target = self.target_combo.currentText()
        if target == FAULT_TARGET:
            self.model.fault_mapping = None
        else:
            self.model.mappings.pop(target, None)
        self.edit_mapping()
        self.refresh()

    def record(self, observation):
        # MainWindow의 제한된 Decode 처리 batch에서만 새 통계 입력을 받는다.
        if not self._closed:
            self.model.record(observation, self.session)
            self.observe_channel(observation.frame.channel)

    def update_coverage(self, *, received, buffer_dropped, pending, processed):
        # Raw Buffer 누락과 통계 상한 제외는 서로 다른 항목으로 표시한다.
        self._received, self._buffer_dropped = received, buffer_dropped
        self._pending, self._processed = pending, processed

    def clear_observations(self):
        # 기존 Clear의 Cache 보존 계약을 유지하고 이 화면의 관측 구간만 초기화한다.
        self.model.statistics.clear()
        self.update_coverage(received=0, buffer_dropped=0, pending=0, processed=0)
        self.refresh()

    @Slot()
    def refresh(self):
        # 모든 UI 갱신은 기존 GUI timer/main thread에서 실행한다.
        if self._closed:
            return
        changed = self.model.sync_session(self.session)
        if changed:
            self.reset_selectors()
        loaded = self.session.loader.is_loaded
        enabled = loaded and not self._closed
        self.apply_button.setEnabled(enabled)
        self.remove_button.setEnabled(enabled)
        dbc = "No DBC" if not loaded else self.session.loader.status.path.name
        self.source_label.setText(f"Source: {self._source_text} | DBC: {dbc} | Production approval NOT VERIFIED")
        stats = self.model.statistics
        self.coverage_label.setText(
            f"통계 구간: Clear/DBC Reload 이후 처리된 RX만 / Processed RX: {stats.processed_rx} | Ignored TX: {stats.ignored_tx} | "
            f"Statistics entries: {len(stats.entries)}/{stats.capacity} | Capacity excluded frames: {stats.capacity_excluded}\n"
            f"Buffer received: {self._received} | Buffer dropped: {self._buffer_dropped} | Pending: {self._pending} | "
            f"Raw/Decode processed: {self._processed}. 통계 Count는 총수신량이 아니며 누락 후 실제 무수신을 증명하지 않습니다.")
        now = self.clock()
        for ecu, labels in self.cards.items():
            mapping = self.model.mappings.get(ecu)
            result = self.model.observe(ecu, self.session, now=now)
            labels["source"].setText("Source: " + source_text(mapping))
            labels["state"].setText("State: " + result.state)
            labels["time"].setText(f"Last RX: {time_text(result.timestamp)} / Age(s): {time_text(result.age, age=True)}")
            labels["count"].setText(f"Processed Message RX: {result.count}")
            signal = "" if result.signal_value is None else f" Signal value: {result.signal_value}."
            labels["details"].setText(result.detail + signal)
        self.refresh_statistics(now)
        self.refresh_fault(now)

    def refresh_statistics(self, now):
        # 유한 항목에 실제 Raw DLC/시각을 표시하고 DBC 없을 때도 RX 통계를 유지한다.
        stats = self.model.statistics.snapshot()
        self.statistics_table.setRowCount(len(stats))
        for row, stat in enumerate(stats):
            key = stat.key
            name = "Unknown / Undefined"
            if key.is_error_frame:
                name = "Error mask; no DBC lookup"
            elif self.session.loader.is_loaded:
                try:
                    name = self.session.loader.get_message_by_id(key.arbitration_id, is_extended_id=key.is_extended_id).name
                except DbcLookupError:
                    pass
            kind = "EXT" if key.is_extended_id else "STD"
            if key.is_error_frame:
                kind += " ERROR"
            if key.is_remote_frame:
                kind += " RTR"
            set_cells(self.statistics_table, row, (
                channel_text(key.channel), f"0x{key.arbitration_id:X}", kind, stat.dlc, stat.count,
                time_text(stat.first_seen), time_text(stat.last_seen),
                time_text(observation_age(stat.last_seen, now), age=True), name))

    def refresh_fault(self, now):
        # 최신 수신 시각과 마지막 정상 decoded 값의 시각을 분리하여 오래된 값의 오인을 막는다.
        result, message, good = self.model.fault_observation(self.session, now=now)
        self.fault_table.setRowCount(0)
        mapping = self.model.fault_mapping
        self.fault_label.setText(
            f"Input: {self._source_text}\n{source_text(mapping)} | {result.state} | Processed RX: {result.count} | "
            f"Last Frame RX: {time_text(result.timestamp)} | Age(s): {time_text(result.age, age=True)}\n{result.detail}")
        if good is None or message is None:
            return
        values = good.decoded.signals
        definitions = {signal.name: signal for signal in message.signals}
        items = tuple(values.items())[:MAX_FAULT_SIGNAL_ROWS]
        self.fault_table.setRowCount(len(items))
        for row, (name, value) in enumerate(items):
            signal = definitions[name]
            choice = (signal.choices or {}).get(value)
            set_cells(self.fault_table, row, (message.name, name, value, "" if choice is None else str(choice),
                                           signal.unit or "", time_text(good.frame.timestamp),
                                           time_text(result.timestamp), result.state))
        if len(values) > MAX_FAULT_SIGNAL_ROWS:
            self.fault_label.setText(self.fault_label.text() + f"\nSignal display limited to {MAX_FAULT_SIGNAL_ROWS}; omitted {len(values) - MAX_FAULT_SIGNAL_ROWS}.")

    def close_view(self):
        # MainWindow가 Worker를 종료한 후 모든 추가 UI 동작을 차단한다.
        self._closed = True
        self.apply_button.setEnabled(False)
        self.remove_button.setEnabled(False)
