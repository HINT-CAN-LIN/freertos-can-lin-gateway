"""Qt 메인 스레드의 Vehicle Status 화면. 값/시각은 VehicleStatusModel에서 조회한다."""
from PySide6.QtCore import Slot
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QGridLayout,
                              QHeaderView, QLabel, QPushButton, QTableWidget,
                              QTableWidgetItem, QVBoxLayout, QWidget)
from .connection import MOCK_CHANNEL, MOCK_SOURCE_LABEL
from .vehicle_status import DISPLAY_ITEMS, SignalMapping, VehicleStatusModel

# 표시 자원 제한이며 CAN Channel 수/통신 규격을 정의하지 않는다.
MAX_CHANNEL_CHOICES = 128
VEHICLE_HEADERS = ["Display item", "Source Message.Signal", "Channel", "Value", "Unit",
                   "Last Update", "Age (s)", "State", "Details"]


def channel_text(channel):
    # None/int/string 식별을 표시하여 숫자 0과 문자열 '0'을 혼합하지 않는다.
    return f"{channel!r} ({type(channel).__name__})"


class VehicleStatusView(QWidget):
    def __init__(self, session, clock, parent=None):
        # 화면은 동일 DecodeSession을 참조하며 수신/Decode를 직접 수행하지 않는다.
        super().__init__(parent)
        self.session = session
        self.clock = clock
        self.model = VehicleStatusModel()
        self._closed = False
        self._session_id = None
        self._channel_count = 0
        self._demo_channel = MOCK_CHANNEL
        self._source_text = MOCK_SOURCE_LABEL
        self._source_is_mock = True
        layout = QVBoxLayout(self)
        self.source_label = QLabel()
        self.source_label.setWordWrap(True)
        layout.addWidget(self.source_label)
        policy = QLabel("자동 매핑 없음. Production 의미/물리값 검증은 별도입니다. "
                        "Valid는 마지막 Decode 성공 RX 값 존재만 의미합니다. Age로 Health/Fault를 판정하지 않습니다.")
        policy.setWordWrap(True)
        layout.addWidget(policy)
        controls = QGridLayout()
        self.item_combo = QComboBox()
        self.item_combo.addItems(DISPLAY_ITEMS)
        self.channel_combo = QComboBox()
        self.message_combo = QComboBox()
        self.signal_combo = QComboBox()
        self.signal_combo.setEditable(True)
        self.confirm_box = QCheckBox("선택 출처/표시 의미 확인 (Interface 승인이 아님)")
        self.apply_button = QPushButton("Apply mapping")
        self.remove_button = QPushButton("Remove mapping")
        for col, (label, widget) in enumerate((
                ("Display item", self.item_combo), ("Channel", self.channel_combo),
                ("DBC Message", self.message_combo), ("Exact Signal", self.signal_combo))):
            controls.addWidget(QLabel(label), 0, col)
            controls.addWidget(widget, 1, col)
        controls.addWidget(self.confirm_box, 2, 0, 1, 2)
        controls.addWidget(self.apply_button, 2, 2)
        controls.addWidget(self.remove_button, 2, 3)
        layout.addLayout(controls)
        self.definition_label = QLabel("DBC source not selected.")
        self.definition_label.setWordWrap(True)
        layout.addWidget(self.definition_label)
        self.table = QTableWidget(len(DISPLAY_ITEMS), len(VEHICLE_HEADERS))
        self.table.setHorizontalHeaderLabels(VEHICLE_HEADERS)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)
        self.message_combo.currentIndexChanged.connect(self.update_signals)
        self.signal_combo.currentTextChanged.connect(self.source_changed)
        self.channel_combo.currentIndexChanged.connect(self.source_changed)
        self.item_combo.currentIndexChanged.connect(self.edit_mapping)
        self.confirm_box.toggled.connect(self.describe_definition)
        self.apply_button.clicked.connect(self.apply_mapping)
        self.remove_button.clicked.connect(self.remove_mapping)
        self.refresh()

    def set_input_source(self, text, *, is_mock):
        # Source 전환 시 MainWindow가 Cache/매핑을 초기화하고 이 화면의 출처도 함께 바꾼다.
        self._source_text, self._source_is_mock = text, is_mock
        self.refresh()

    def reset_selectors(self):
        # 새 DBC 세션에서는 과거 파일의 Signal/사용자 연결을 남기지 않는다.
        self.channel_combo.clear()
        self.channel_combo.addItem("Select channel")
        self._channel_count = 0
        if self._source_is_mock:
            self.channel_combo.addItem(channel_text(self._demo_channel), self._demo_channel)
            self._channel_count = 1
        self.message_combo.clear()
        self.message_combo.addItem("Select message", None)
        for message in self.model.definitions(self.session):
            kind = "EXT" if message.is_extended_frame else "STD"
            self.message_combo.addItem(f"{message.name} [0x{message.frame_id:X} {kind}]", message.name)
        self.confirm_box.setChecked(False)
        self.update_signals()
        enabled = self.session.loader.is_loaded
        self.apply_button.setEnabled(enabled and not self._closed)
        self.remove_button.setEnabled(enabled and not self._closed)

    def observe_channel(self, channel):
        # Raw 수신에서 확인한 타입까지 보존한다. Source 목록은 유한하게 유지한다.
        if self._closed:
            return
        for index in range(1, self.channel_combo.count()):
            existing = self.channel_combo.itemData(index)
            if type(existing) is type(channel) and existing == channel:
                return
        if self._channel_count < MAX_CHANNEL_CHOICES:
            self.channel_combo.addItem(channel_text(channel), channel)
            self._channel_count += 1

    @Slot()
    def update_signals(self, *_):
        # Message 미선택 시 exact 이름 목록만 보여주며 첫 후보를 자동 선택하지 않는다.
        self.signal_combo.clear()
        self.signal_combo.addItem("")
        message_name = self.message_combo.currentData()
        definitions = self.model.definitions(self.session)
        names = sorted({signal.name for message in definitions
                        if message_name is None or message.name == message_name
                        for signal in message.signals})
        self.signal_combo.addItems(names)
        self.confirm_box.setChecked(False)
        self.describe_definition()

    @Slot()
    def source_changed(self, *_):
        # 출처를 바꾸면 이전 확인을 승계하지 않고 다시 확인하도록 한다.
        self.confirm_box.setChecked(False)
        self.describe_definition()

    @Slot()
    def describe_definition(self, *_):
        # 실제 DBC의 Unit/comment를 제시하며 Signal 의미를 별도로 추정하지 않는다.
        message_name = self.message_combo.currentData()
        signal_name = self.signal_combo.currentText()
        if not self.session.loader.is_loaded or not message_name:
            self.definition_label.setText("Choose exact Message and Signal; duplicate names require explicit Message.")
            return
        message = self.session.loader.get_message_by_name(message_name)
        signals = [signal for signal in message.signals if signal.name == signal_name]
        if len(signals) != 1:
            self.definition_label.setText("Not Defined / Ambiguous: choose an exact Signal in the selected Message.")
            return
        signal = signals[0]
        comment = signal.comment or "No DBC semantic comment; verify meaning before mapping."
        self.definition_label.setText(f"DBC source: {message_name}.{signal.name} | Unit={signal.unit or ''} | {comment}")

    @Slot()
    def edit_mapping(self, *_):
        # 이미 사용자 확인된 설정만 편집기에 복원한다. 다른 항목으로 암묵 복사하지 않는다.
        mapping = self.model.mappings.get(self.item_combo.currentText())
        self.message_combo.setCurrentIndex(0)
        self.channel_combo.setCurrentIndex(0)
        self.signal_combo.setCurrentText("")
        self.confirm_box.setChecked(False)
        if mapping is None:
            return
        self.message_combo.setCurrentIndex(self.message_combo.findData(mapping.message_name))
        self.signal_combo.setCurrentText(mapping.signal_name or "")
        self.observe_channel(mapping.channel)
        if mapping.channel_selected:
            for index in range(1, self.channel_combo.count()):
                value = self.channel_combo.itemData(index)
                if type(value) is type(mapping.channel) and value == mapping.channel:
                    self.channel_combo.setCurrentIndex(index)
                    break
        self.confirm_box.setChecked(mapping.meaning_confirmed)

    @Slot()
    def apply_mapping(self):
        # 부분 선택은 Ambiguous/Not Defined로 기록되며 가짜 신호값을 만들지 않는다.
        if self._closed or not self.session.loader.is_loaded:
            return
        mapping = SignalMapping(
            self.message_combo.currentData(), self.signal_combo.currentText() or None,
            self.channel_combo.currentData(), self.channel_combo.currentIndex() > 0,
            self.confirm_box.isChecked(),
        )
        self.model.bind(self.item_combo.currentText(), mapping, self.session)
        self.refresh()

    @Slot()
    def remove_mapping(self):
        # 표시 설정 제거만 수행한다. 다른 항목과 수신 Cache는 보존한다.
        if not self._closed:
            self.model.unbind(self.item_combo.currentText())
            self.refresh()

    @Slot()
    def refresh(self):
        # 고정 개수의 항목을 기존 Cache로만 갱신하며 Worker/Qt signal 큐를 늘리지 않는다.
        if self._closed:
            return
        changed = self.model.sync_session(self.session)
        if changed or self._session_id != self.session.session_id:
            self._session_id = self.session.session_id
            self.reset_selectors()
        status = self.session.loader.status
        name = "not selected" if status.path is None else status.path.name
        self.source_label.setText(f"Vehicle Status | DBC={name} | DBC session={self.session.session_id} | "
                                 f"Source={self._source_text} | user display mapping; Production approval not verified")
        now = self.clock()
        for row, item in enumerate(DISPLAY_ITEMS):
            observation = self.model.observe(item, self.session, now=now)
            mapping = self.model.mappings.get(item)
            source = "" if mapping is None else f"{mapping.message_name or '?'} . {mapping.signal_name or '?'}"
            channel = "" if mapping is None or not mapping.channel_selected else channel_text(mapping.channel)
            value = "No Data" if observation.value is None else str(observation.value)
            stamp = "unknown" if observation.timestamp is None else f"{observation.timestamp:.6f}"
            age = "unknown" if observation.age is None else f"{observation.age:.3f}"
            cells = (item, source, channel, value, observation.unit or "", stamp, age,
                     observation.state.value, observation.detail)
            for column, text in enumerate(cells):
                cell = QTableWidgetItem(text)
                # 긴 오류/출처가 셀에서 생략돼도 전체 원인을 hover로 확인할 수 있다.
                cell.setToolTip(text)
                self.table.setItem(row, column, cell)

    def close_view(self):
        # 종료 후 매핑/타이머 요청이 들어와도 UI와 Cache를 갱신하지 않는다.
        self._closed = True
        self.apply_button.setEnabled(False)
        self.remove_button.setEnabled(False)
