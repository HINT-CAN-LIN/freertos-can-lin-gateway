"""Qt 연결 편집기. 장치 열기/수신은 수행하지 않는다."""
from PySide6.QtCore import Signal, QSignalBlocker
from PySide6.QtWidgets import QComboBox, QGridLayout, QLabel, QLineEdit, QWidget
from .connection import ConnectionSettings, MOCK_MODE, LIVE_MODE, LIVE_BACKENDS, CLUSTER_TEST_BITRATE


class ConnectionView(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        # 기본 Mock, 실제 backend/channel은 미선택이며 COM port를 고정하지 않는다.
        super().__init__(parent)
        self._locked = False
        self.mode_combo = QComboBox()
        self.mode_combo.addItems((MOCK_MODE, LIVE_MODE))
        self.backend_combo = QComboBox()
        self.backend_combo.addItem("Select backend", "")
        for backend in LIVE_BACKENDS:
            self.backend_combo.addItem(backend, backend)
        self.channel_edit = QLineEdit()
        self.channel_edit.setPlaceholderText("SLCAN: 실제 port / gs_usb: device index")
        self.bitrate_edit = QLineEdit(str(CLUSTER_TEST_BITRATE))
        self.status_label = QLabel("Connection: Disconnected")
        self.error_label = QLabel("Last connection error: none")
        self.error_label.setWordWrap(True)
        self.policy_label = QLabel(
            "Source 설정 변경은 Stop + Receiver/Writer 종료 후만 가능. 이전 관측/Cache/매핑 초기화. "
            "Live GUI는 application CAN TX 없음; hardware listen-only/ACK 무송신 보장은 아님."
        )
        self.policy_label.setWordWrap(True)
        layout = QGridLayout(self)
        for column, (label, widget) in enumerate((
                ("Mode", self.mode_combo), ("Backend", self.backend_combo),
                ("Channel", self.channel_edit), ("Bitrate (bit/s)", self.bitrate_edit))):
            layout.addWidget(QLabel(label), 0, column)
            layout.addWidget(widget, 1, column)
        layout.addWidget(self.status_label, 2, 0, 1, 2)
        layout.addWidget(self.error_label, 2, 2, 1, 2)
        layout.addWidget(self.policy_label, 3, 0, 1, 4)
        self._accepted = self.raw_values()
        self.mode_combo.currentTextChanged.connect(self.settings_changed)
        self.backend_combo.currentIndexChanged.connect(self.settings_changed)
        self.channel_edit.textChanged.connect(self.settings_changed)
        self.bitrate_edit.textChanged.connect(self.settings_changed)
        self.set_locked(False)

    def raw_values(self):
        # 미완성 입력도 보존하여 잠금 중 programmatic 변경을 복구한다.
        return (self.mode_combo.currentText(), self.backend_combo.currentIndex(),
                self.channel_edit.text(), self.bitrate_edit.text())

    def settings_changed(self, *_):
        # disabled widget에 대한 직접 변경도 활성 수신 설정에 반영하지 않는다.
        if self._locked:
            widgets = (self.mode_combo, self.backend_combo, self.channel_edit, self.bitrate_edit)
            blockers = [QSignalBlocker(widget) for widget in widgets]
            mode, backend_index, channel, bitrate = self._accepted
            self.mode_combo.setCurrentText(mode)
            self.backend_combo.setCurrentIndex(backend_index)
            self.channel_edit.setText(channel)
            self.bitrate_edit.setText(bitrate)
            del blockers
            return
        self._accepted = self.raw_values()
        self.set_locked(False)
        self.changed.emit()

    def set_locked(self, locked):
        # 연결 중/수신 중/해제 중에는 Source 선택 전체를 잠근다.
        self._locked = locked
        self.mode_combo.setEnabled(not locked)
        live = self.mode_combo.currentText() == LIVE_MODE
        for widget in (self.backend_combo, self.channel_edit, self.bitrate_edit):
            widget.setEnabled(live and not locked)

    def settings(self):
        # 설정 오류는 Start에서 표시한다. gs_usb 숫자 채널은 문자열과 구분한다.
        mode = self.mode_combo.currentText()
        if mode == MOCK_MODE:
            return ConnectionSettings()
        backend = self.backend_combo.currentData()
        channel = self.channel_edit.text().strip()
        if backend == "gs_usb":
            try:
                channel = int(channel)
            except ValueError:
                raise ValueError("gs_usb channel must be a nonnegative device index.") from None
        try:
            bitrate = int(self.bitrate_edit.text().strip())
        except ValueError:
            raise ValueError("Bitrate must be a positive integer in bit/s.") from None
        return ConnectionSettings(mode, backend, channel, bitrate).validate()

    def source_text(self):
        # 편집 중에도 Live를 Mock이라고 표시하지 않는다. Connected 여부와 별개이다.
        if self.mode_combo.currentText() == MOCK_MODE:
            return ConnectionSettings().source_text()
        return (f"Live / {self.backend_combo.currentData() or 'not selected'} / "
                f"channel={self.channel_edit.text()!r} / bitrate={self.bitrate_edit.text()}")

    def set_state(self, state):
        # 실제 Worker lifecycle 이벤트에 의해 MainWindow에서만 갱신한다.
        self.status_label.setText("Connection: " + state)

    def show_error(self, message):
        # 마지막 연결 오류는 재시도 중에도 보존하여 원인을 확인할 수 있게 한다.
        self.error_label.setText("Last connection error: " + message)
