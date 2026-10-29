"""명시적 DBC Signal 선택과 timer 기반 그래프. 수신·Decode·Logging은 재사용한다."""
from PySide6.QtCore import QTimer, Slot
from PySide6.QtWidgets import QComboBox, QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from .connection import MOCK_CHANNEL, MOCK_SOURCE_LABEL
from .graph_canvas import GraphCanvas
from .signal_graph import GraphSelection, SignalGraphModel
from .vehicle_view import MAX_CHANNEL_CHOICES, channel_text

GRAPH_REFRESH_MS = 200  # GUI 렌더링 설정이며 CAN 전송 주기/Fault Timeout이 아니다.


class SignalGraphView(QWidget):
    def __init__(self, session, parent=None):
        # 모든 Widget/Model은 GUI 메인 스레드가 소유한다.
        super().__init__(parent)
        self.session = session
        self.source = MOCK_SOURCE_LABEL
        self.is_mock = True
        self.model = SignalGraphModel()
        self.paused = False
        self._closed = False
        self.source_label = QLabel()
        self.source_label.setWordWrap(True)
        self.policy_label = QLabel("단일 Signal · 명시적 DBC 선택 · Healthy 판정 아님. "
                                  "Pause는 곡선 표시만 정지: 수신/Decode/Logging/유한 수집은 계속. Clear Graph는 그래프만 초기화.")
        self.policy_label.setWordWrap(True)
        self.channel_combo = QComboBox()
        self.message_combo = QComboBox()
        self.signal_combo = QComboBox()
        self.unit_label = QLabel("Unit: not defined")
        self.apply_button = QPushButton("Apply signal")
        self.pause_button = QPushButton("Pause graph")
        self.clear_button = QPushButton("Clear Graph")
        self.value_label = QLabel()
        self.state_label = QLabel()
        self.count_label = QLabel()
        self.state_label.setWordWrap(True)
        self.count_label.setWordWrap(True)
        self.canvas = GraphCanvas(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.source_label)
        layout.addWidget(self.policy_label)
        controls = QGridLayout()
        for column, (name, widget) in enumerate((
                ("CAN Channel", self.channel_combo), ("Message Name / CAN ID / STD·EXT", self.message_combo),
                ("Exact Signal", self.signal_combo), ("DBC Unit (read only)", self.unit_label))):
            controls.addWidget(QLabel(name), 0, column)
            controls.addWidget(widget, 1, column)
        controls.addWidget(self.apply_button, 2, 0)
        controls.addWidget(self.pause_button, 2, 1)
        controls.addWidget(self.clear_button, 2, 2)
        layout.addLayout(controls)
        for label in (self.value_label, self.state_label, self.count_label):
            layout.addWidget(label)
        layout.addWidget(self.canvas, 1)
        self.message_combo.currentIndexChanged.connect(self.update_signals)
        self.signal_combo.currentIndexChanged.connect(self.describe_unit)
        self.apply_button.clicked.connect(self.apply_signal)
        self.pause_button.clicked.connect(self.toggle_pause)
        self.clear_button.clicked.connect(self.clear_graph)
        self.timer = QTimer(self)
        self.timer.setInterval(GRAPH_REFRESH_MS)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def sync_session(self):
        # Reload/Source 전환은 paused curve와 선택 채널까지 원자적으로 초기화한다.
        changed = self.model.sync_session(self.session, self.source)
        if changed:
            self.paused = False
            self.pause_button.setText("Pause graph")
            self.canvas.set_samples(())
            self.channel_combo.clear()
            self.channel_combo.addItem("Select channel")
            if self.is_mock:
                self.channel_combo.addItem(channel_text(MOCK_CHANNEL), MOCK_CHANNEL)
            self.message_combo.clear()
            self.message_combo.addItem("Select message")
            if self.session.loader.is_loaded:
                for message in self.session.loader.get_messages():
                    fmt = "EXT" if message.is_extended_frame else "STD"
                    self.message_combo.addItem(f"{message.name} [0x{message.frame_id:X} {fmt}]",
                                               (message.name, message.frame_id, message.is_extended_frame))
            self.update_signals()
        return changed

    def set_input_source(self, text, *, is_mock):
        # Live/Fake Live/Mock provenance를 Sample과 화면에 함께 기록한다.
        self.source, self.is_mock = text, is_mock
        self.refresh()

    def observe_channel(self, channel):
        # None은 unknown channel 선택이며 wildcard가 아니다. 목록은 유한하다.
        for index in range(1, self.channel_combo.count()):
            existing = self.channel_combo.itemData(index)
            if type(existing) is type(channel) and existing == channel:
                return
        if self.channel_combo.count()-1 < MAX_CHANNEL_CHOICES:
            self.channel_combo.addItem(channel_text(channel), channel)

    def selected_definition(self):
        # Combo item의 정확한 이름/ID/STD·EXT를 사용하며 같은 Signal 이름을 자동 연결하지 않는다.
        key = self.message_combo.currentData()
        if key is None or not self.session.loader.is_loaded:
            return None
        matches = [m for m in self.session.loader.get_messages()
                   if (m.name, m.frame_id, m.is_extended_frame) == tuple(key)]
        return matches[0] if len(matches) == 1 else None

    @Slot()
    def update_signals(self, *_):
        # Message 선택 후에도 Signal은 placeholder에서 시작한다.
        self.signal_combo.clear()
        self.signal_combo.addItem("Select signal", None)
        message = self.selected_definition()
        if message is not None:
            for signal in message.signals:
                self.signal_combo.addItem(signal.name, signal.name)
        self.describe_unit()

    @Slot()
    def describe_unit(self, *_):
        # Unit은 DBC metadata 그대로 사용하고 비어 있으면 임의 단위를 만들지 않는다.
        message = self.selected_definition()
        name = self.signal_combo.currentData()
        signals = [] if message is None else [s for s in message.signals if s.name == name]
        self.unit_label.setText("Unit: " + (signals[0].unit or "not defined") if len(signals) == 1 else "Unit: not defined")

    @Slot()
    def apply_signal(self):
        # Apply 전에는 편집 선택을 현재 plotted selection으로 암묵 적용하지 않는다.
        if self._closed:
            return
        message = self.selected_definition()
        name = self.signal_combo.currentData()
        selected = None
        if message is not None and name:
            selected = GraphSelection(self.channel_combo.currentData(), message.name, message.frame_id,
                                      message.is_extended_frame, name, self.channel_combo.currentIndex()>0)
        self.model.bind(selected, self.session, self.source)
        self.canvas.set_samples(())
        self.refresh()

    def record(self, observation):
        # MainWindow의 이미 Decode된 FrameObservation만 받고 다시 decode하지 않는다.
        if not self._closed:
            self.sync_session()
            self.observe_channel(observation.frame.channel)
            self.model.record(observation, self.session, self.source)

    def note_buffer_drop(self, dropped):
        # Raw Buffer 제외와 graph history/time/value 제외를 별도 계수로 표시한다.
        if not self._closed:
            self.sync_session()
            self.model.note_buffer_drop(dropped)

    @Slot()
    def toggle_pause(self):
        # 표시 snapshot만 유지한다. 수신/모델 수집/Logger는 중단하지 않는다.
        if not self._closed:
            self.paused = not self.paused
            self.pause_button.setText("Resume graph" if self.paused else "Pause graph")
            self.refresh()

    @Slot()
    def clear_graph(self):
        # Pause 중에도 현재 곡선과 Graph 이력만 비운다.
        if not self._closed:
            self.model.clear()
            signal, state, detail = self.model.definition(self.session)
            if state:
                self.model.state, self.model.detail = state, detail
            else:
                self.model.unit = signal.unit
            self.canvas.set_samples(())
            self.refresh()

    @Slot()
    def refresh(self):
        # 렌더링 주기는 CAN 수신 빈도와 분리하며 Snapshot 크기도 sample 상한을 따른다.
        if self._closed:
            return
        self.sync_session()
        model = self.model
        self.source_label.setText(f"Signal Graph | Source={self.source} | DBC session={self.session.session_id} | Hardware NOT VERIFIED")
        chosen = model.selection
        selection = "not selected" if chosen is None else (
            f"{channel_text(chosen.channel)} / {chosen.message_name} [0x{chosen.arbitration_id:X} "
            f"{'EXT' if chosen.is_extended_id else 'STD'}].{chosen.signal_name}")
        stamp = "unknown" if model.latest_timestamp is None else str(model.latest_timestamp)
        self.value_label.setText(f"Selected: {selection}\nLatest numeric observation: {model.latest_value if model.latest_value is not None else 'No Data'} "
                                 f"| Unit: {model.unit or 'not defined'} | Last Update (raw timestamp): {stamp}")
        self.value_label.setWordWrap(True)
        self.state_label.setText(f"State: {model.state} | {'Curve PAUSED; collection continues' if self.paused else 'Curve updating'} | {model.detail}")
        self.count_label.setText(f"Samples retained: {len(model.samples)}/{model.capacity} | Accepted since Clear: {model.accepted} | "
                                 f"Graph history omitted: {model.history_omitted} | Timestamp excluded: {model.timestamp_excluded} | "
                                 f"Value excluded: {model.value_excluded} | Decode errors: {model.decode_errors}\n"
                                 f"GUI Buffer dropped: {model.buffer_dropped} (not measured CAN loss); graph samples are processed RX only.")
        self.apply_button.setEnabled(self.session.loader.is_loaded)
        if not self.paused:
            self.canvas.set_samples(model.samples)

    def close_view(self):
        # MainWindow가 Receiver/Writer 종료 후 Graph timer와 편집도 정리한다.
        self._closed = True
        self.timer.stop()
        for widget in (self.apply_button, self.pause_button, self.clear_button):
            widget.setEnabled(False)
