"""명시적 Fault 표시 출처의 유한 이력/필터/상세. Qt 메인 스레드 전용."""
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Slot
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QGridLayout,
                              QLabel, QPlainTextEdit, QPushButton, QSplitter, QTableView,
                              QVBoxLayout, QWidget)
from .connection import MOCK_CHANNEL, MOCK_SOURCE_LABEL
from .ecu_observation import MessageMapping
from .fault_history import FaultHistoryModel, channel_key, mapping_key
from .vehicle_view import MAX_CHANNEL_CHOICES, channel_text

HISTORY_HEADERS = ("Order", "RX Run", "Timestamp", "Source", "Channel", "CAN ID / Format",
                   "Message", "FaultCode (raw)", "Decode", "Fault State")
DETAIL_LINES = 256  # 표시 자원 제한. 원본 Frame/Signal은 model의 immutable entry에 보존한다.


def entry_cells(entry):
    # 실제 Raw 식별자와 수신 Timestamp를 그대로 표시하며 선택 의미를 추정하지 않는다.
    frame = entry.frame
    fmt = "EXT" if frame.is_extended_id else "STD"
    if frame.is_remote_frame:
        fmt += " RTR"
    return (entry.sequence, "Unknown" if entry.receiver_run is None else entry.receiver_run,
            "unknown" if frame.timestamp is None else str(frame.timestamp), entry.source,
            channel_text(frame.channel), f"0x{frame.arbitration_id:X} {fmt}", entry.message_name,
            entry.signals.get("FaultCode", "Not Defined / No decoded value"),
            entry.decode_state, entry.fault_status)


def entry_detail(entry):
    # Frame/Decode/상태 해석을 세 수준으로 분리한다. Payload bit 재해석은 하지 않는다.
    frame = entry.frame
    lines = [f"Observation order: {entry.sequence} | Source: {entry.source}",
             f"DBC/Source session: {entry.session_id} | RX run: {entry.receiver_run or 'Unknown (no Start marker or prior backlog)'}",
             "1. Received Raw Frame",
             f"Channel: {channel_text(frame.channel)} | CAN ID: 0x{frame.arbitration_id:X} | {'EXT' if frame.is_extended_id else 'STD'}",
             f"Timestamp: {frame.timestamp} | {entry.timestamp_note}",
             f"DLC: {frame.dlc} | Payload: {frame.data.hex(' ').upper()} | RX: {frame.is_rx} | RTR: {frame.is_remote_frame}",
             f"2. Per-frame Decode: {entry.decode_state} | Message: {entry.message_name}",
             f"Error: {entry.error or 'none'}"]
    for name, value in entry.signals.items():
        lines.append(f"{name} = {value} | Unit: {entry.units.get(name) or 'not defined'} | DBC Choice: {entry.choices.get(name, 'not defined')}")
    lines.extend(("3. Interpreted Fault State: Status Unknown",
                  "DBC Choice is metadata, not approved lifecycle/current ECU state. No fault-free/clear/replay inference."))
    return "\n".join(lines)


class FaultTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        # Qt 필수 override 이름은 snake_case 규칙의 예외이다.
        super().__init__(parent)
        self.entries = ()

    def rowCount(self, parent=QModelIndex()):
        # 유한 filtered snapshot의 크기만 Qt에 제공한다.
        return 0 if parent.isValid() else len(self.entries)

    def columnCount(self, parent=QModelIndex()):
        # 열 의미는 CAN Interface 정의와 별도의 표시 계약이다.
        return 0 if parent.isValid() else len(HISTORY_HEADERS)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        # Qt main thread에서 실제 entry의 표시값만 조회한다.
        if not index.isValid() or not 0 <= index.row() < len(self.entries):
            return None
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole):
            return str(entry_cells(self.entries[index.row()])[index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        # Qt 표준 모델 계약으로 고정 표시 헤더를 제공한다.
        if role == Qt.ItemDataRole.DisplayRole:
            return HISTORY_HEADERS[section] if orientation == Qt.Orientation.Horizontal else str(section + 1)
        return None

    def replace_entries(self, entries):
        # Qt에 batch 단위 snapshot을 제공하여 프레임별 queued UI 이벤트를 만들지 않는다.
        self.beginResetModel()
        self.entries = entries
        self.endResetModel()


class FaultMonitorView(QWidget):
    def __init__(self, session, *, capacity=None, parent=None):
        # 별도 Worker/Timer 없이 MainWindow의 기존 GUI refresh를 재사용한다.
        super().__init__(parent)
        self.session = session
        self.source, self.is_mock = MOCK_SOURCE_LABEL, True
        self.model = FaultHistoryModel() if capacity is None else FaultHistoryModel(capacity)
        self._closed = self._filter_updating = False
        self._rendered_revision = None
        self._mapping_error = None
        self.source_label = QLabel()
        self.source_label.setWordWrap(True)
        self.state_label = QLabel()
        self.state_label.setWordWrap(True)
        self.count_label = QLabel()
        self.count_label.setWordWrap(True)
        note = QLabel("Fault 관련 출처를 명시적으로 선택합니다. 관측 이력 ≠ 실제 Active Fault 목록. "
                      "Status Unknown: ACTIVE/CLEARED/Severity/Replay 계약 승인 미확인. Clear History는 ECU 해제가 아닙니다.")
        note.setWordWrap(True)
        layout = QVBoxLayout(self)
        for label in (self.source_label, note):
            layout.addWidget(label)
        controls = QGridLayout()
        self.channel_combo, self.message_combo, self.sources_combo = QComboBox(), QComboBox(), QComboBox()
        self.confirm_box = QCheckBox("Fault 표시 출처 확인 (팀 Interface 승인 아님 / TEST ONLY 가능)")
        self.add_button, self.remove_button = QPushButton("Add observation source"), QPushButton("Remove source")
        self.clear_button = QPushButton("Clear History")
        for column, (name, widget) in enumerate((("Source Channel", self.channel_combo),
                                                ("Exact DBC Message / ID / Format", self.message_combo),
                                                ("Configured sources", self.sources_combo))):
            controls.addWidget(QLabel(name), 0, column)
            controls.addWidget(widget, 1, column)
        controls.addWidget(self.confirm_box, 2, 0)
        controls.addWidget(self.add_button, 2, 1)
        controls.addWidget(self.remove_button, 2, 2)
        controls.addWidget(self.clear_button, 2, 3)
        layout.addLayout(controls)
        filters = QGridLayout()
        self.code_filter, self.channel_filter, self.message_filter = QComboBox(), QComboBox(), QComboBox()
        self.error_filter = QCheckBox("Decode Error only")
        for column, (name, widget) in enumerate((("FaultCode (exact numeric value)", self.code_filter),
                                                ("Channel filter", self.channel_filter),
                                                ("Message / ID / Format filter", self.message_filter))):
            filters.addWidget(QLabel(name), 0, column)
            filters.addWidget(widget, 1, column)
            widget.currentIndexChanged.connect(self.filters_changed)
        filters.addWidget(self.error_filter, 1, 3)
        layout.addLayout(filters)
        for label in (self.state_label, self.count_label):
            layout.addWidget(label)
        self.table_model = FaultTableModel(self)
        self.table = QTableView()
        self.table.setModel(self.table_model)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setMaximumBlockCount(DETAIL_LINES)
        split = QSplitter(Qt.Orientation.Vertical)
        split.addWidget(self.table)
        split.addWidget(self.details)
        split.setStretchFactor(0, 2)
        split.setStretchFactor(1, 1)
        layout.addWidget(split, 1)
        self.table.selectionModel().selectionChanged.connect(self.show_detail)
        self.add_button.clicked.connect(self.add_source)
        self.remove_button.clicked.connect(self.remove_source)
        self.clear_button.clicked.connect(self.clear_history)
        self.error_filter.toggled.connect(self.filters_changed)
        self.channel_combo.currentIndexChanged.connect(self.unconfirm)
        self.message_combo.currentIndexChanged.connect(self.unconfirm)
        self.refresh()

    @Slot()
    def unconfirm(self, *_):
        # 출처 선택이 바뀌면 이전 사용자 확인을 승계하지 않는다.
        self.confirm_box.setChecked(False)

    def sync_session(self):
        # Source/DBC 변경은 이력·필터·매핑·상세를 함께 초기화한다.
        changed = self.model.sync_session(self.session, self.source)
        if changed:
            self._mapping_error = None
            self.channel_combo.clear()
            self.channel_combo.addItem("Select channel")
            if self.is_mock:
                self.observe_channel(MOCK_CHANNEL)
            self.message_combo.clear()
            self.message_combo.addItem("Select message")
            if self.session.loader.is_loaded:
                for message in self.session.loader.get_messages():
                    self.message_combo.addItem(f"{message.name} [0x{message.frame_id:X} {'EXT' if message.is_extended_frame else 'STD'}]",
                                               (message.name, message.frame_id, message.is_extended_frame))
            self.confirm_box.setChecked(False)
            self._filter_updating = True
            for widget in (self.code_filter, self.channel_filter, self.message_filter):
                widget.clear()
                widget.addItem("All", None)
            self.error_filter.setChecked(False)
            self._filter_updating = False
            self.details.clear()
        return changed

    def set_input_source(self, text, *, is_mock):
        # Fake Live는 MainWindow에서 주입 출처 표기를 포함하여 전달한다.
        self.source, self.is_mock = text, is_mock
        self.refresh()

    def observe_channel(self, channel):
        # Channel 후보도 기존 GUI 상한을 따르며 타입별로 구별한다.
        for index in range(1, self.channel_combo.count()):
            if channel_key(self.channel_combo.itemData(index)) == channel_key(channel):
                return
        if self.channel_combo.count() - 1 < MAX_CHANNEL_CHOICES:
            self.channel_combo.addItem(channel_text(channel), channel)

    @Slot()
    def add_source(self):
        # 첫 후보/이름 유사성/임의 CAN ID를 사용하지 않는다.
        if self._closed:
            return
        self.sync_session()
        key = self.message_combo.currentData()
        if key is None:
            self._mapping_error = "Select an exact DBC message."
            self.refresh()
            return
        mapping = MessageMapping(key[0], self.channel_combo.currentData(), key[1], key[2],
                                 self.channel_combo.currentIndex() > 0, self.confirm_box.isChecked())
        try:
            self.model.add_source(mapping, self.session, self.source)
        except ValueError as exc:
            self._mapping_error = str(exc)
            self.refresh()
            return
        self._mapping_error = None
        self.refresh()

    @Slot()
    def remove_source(self):
        # 과거 관측은 유지하며 앞으로 수집할 매핑만 제거한다.
        if not self._closed:
            self.model.remove_source(self.sources_combo.currentData())
            self.refresh()

    def begin_receiver(self, *, pending_prior=False):
        # 재접속/Start는 새 관측 run이다. 이전 이력은 run 열로 구분하며 재전송을 가정하지 않는다.
        if not self._closed:
            self.sync_session()
            self.model.begin_receiver(pending_prior=pending_prior)
            self.refresh()

    def record(self, observation):
        # 입력은 이미 처리된 FrameObservation이며 UI 변경은 refresh batch에 모은다.
        if not self._closed:
            self.sync_session()
            self.observe_channel(observation.frame.channel)
            self.model.record(observation, self.session, self.source)

    def note_buffer_drop(self, dropped):
        # 공유 수신 버퍼 제외량은 별도로 표시하고 History completeness를 주장하지 않는다.
        if not self._closed:
            self.sync_session()
            self.model.note_buffer_drop(dropped)

    @Slot()
    def filters_changed(self, *_):
        # 필터 변경은 수신/Logger/model 이력을 수정하지 않는다.
        if not self._filter_updating:
            self._rendered_revision = None
            self.refresh()

    def refill_filter(self, widget, candidates):
        # 현재 선택은 이력이 evict되어도 유지하고 후보 목록은 retained history로 제한한다.
        selected = widget.currentData()
        if selected is not None and selected not in [key for label, key in candidates]:
            candidates.append((widget.currentText(), selected))
        widget.blockSignals(True)
        widget.clear()
        widget.addItem("All", None)
        for label, key in candidates:
            widget.addItem(label, key)
        for index in range(widget.count()):
            if widget.itemData(index) == selected:
                widget.setCurrentIndex(index)
                break
        widget.blockSignals(False)

    @Slot()
    def refresh(self):
        # 기존 Qt 메인 스레드 refresh에서 revision 변경 시에만 유한 표 snapshot을 바꾼다.
        if self._closed:
            return
        self.sync_session()
        model = self.model
        self.source_label.setText(f"Fault Monitor | Source: {self.source} | DBC/Source session: {model.session_id} | Hardware NOT VERIFIED")
        self.add_button.setEnabled(self.session.loader.is_loaded)
        state = "No DBC" if not self.session.loader.is_loaded else (
            "No Data" if not model.entries else model.entries[-1].decode_state)
        mapping_error = "" if self._mapping_error is None else f"Last mapping error: {self._mapping_error} | "
        # 정기 refresh가 사용자 매핑 오류 원인을 즉시 지우지 않도록 보존한다.
        self.state_label.setText(f"{mapping_error}{state} | Status Unknown | Fault not observed is NOT No Fault. "
                                 "History is processed RX only; no missing event replay/current state reconstruction.")
        if self._rendered_revision == model.revision:
            return
        selected = self.selected_entry()
        selected_order = None if selected is None else selected.sequence
        source_selection = self.sources_combo.currentData()
        self.sources_combo.clear()
        for key, mapping in model.sources.items():
            self.sources_combo.addItem(f"{channel_text(mapping.channel)} / {mapping.message_name} "
                                       f"[0x{mapping.arbitration_id:X} {'EXT' if mapping.is_extended_id else 'STD'}]", key)
        for index in range(self.sources_combo.count()):
            if self.sources_combo.itemData(index) == source_selection:
                self.sources_combo.setCurrentIndex(index)
                break
        codes, channels, messages = {}, {}, {}
        for entry in model.entries:
            code = entry.signals.get("FaultCode")
            if code is not None:
                codes[code] = str(code)
            channels[channel_key(entry.frame.channel)] = channel_text(entry.frame.channel)
            key = (entry.message_name, entry.frame.arbitration_id, entry.frame.is_extended_id)
            messages[key] = f"{key[0]} [0x{key[1]:X} {'EXT' if key[2] else 'STD'}]"
        self.refill_filter(self.code_filter, [(label, key) for key, label in codes.items()])
        self.refill_filter(self.channel_filter, [(label, key) for key, label in channels.items()])
        self.refill_filter(self.message_filter, [(label, key) for key, label in messages.items()])
        entries = model.filtered(fault_code=self.code_filter.currentData(), channel=self.channel_filter.currentData(),
                                 message=self.message_filter.currentData(), errors_only=self.error_filter.isChecked())
        selection_model = self.table.selectionModel()
        selection_model.blockSignals(True)
        self.table_model.replace_entries(entries)
        for row, entry in enumerate(entries):
            if entry.sequence == selected_order:
                self.table.selectRow(row)
                break
        selection_model.blockSignals(False)
        self.show_detail()
        self.count_label.setText(f"History retained: {len(model.entries)}/{model.capacity} | Filtered: {len(entries)} | "
                                 f"Observed since Clear: {model.observed} | Oldest history omitted: {model.history_omitted}\n"
                                 f"GUI Buffer dropped: {model.buffer_dropped} (not measured CAN loss) | "
                                 f"Missing timestamp: {model.missing_timestamps} | Reversed: {model.reversed_timestamps} | "
                                 f"Latest observed raw Timestamp: {model.entries[-1].frame.timestamp if model.entries else 'No Data'} | "
                                 f"Receiver Start markers: {model.receiver_generation}. Prior backlog → RX Run Unknown.")
        self._rendered_revision = model.revision

    def selected_entry(self):
        # Row index를 보관하지 않고 현재 filtered snapshot의 immutable 항목을 조회한다.
        index = self.table.currentIndex()
        return self.table_model.entries[index.row()] if index.isValid() and index.row() < len(self.table_model.entries) else None

    @Slot()
    def show_detail(self, *_):
        # 선택 항목이 filter/eviction으로 사라지면 과거 상세를 현재 관측처럼 남기지 않는다.
        entry = self.selected_entry()
        text = "" if entry is None else entry_detail(entry)
        # 선택 항목이 그대로이면 내용/스크롤을 다시 초기화하지 않는다.
        if self.details.toPlainText() != text:
            self.details.setPlainText(text)

    @Slot()
    def clear_history(self):
        # 파일/Cache/Raw/Graph/Transport에는 접근하지 않는 PC 로컬 동작이다.
        if not self._closed:
            self.model.clear()
            self.refresh()

    def close_view(self):
        # 별도 Thread/Timer가 없으며 종료 이후 새 UI 작업만 차단한다.
        self._closed = True
        for widget in (self.add_button, self.remove_button, self.clear_button):
            widget.setEnabled(False)
