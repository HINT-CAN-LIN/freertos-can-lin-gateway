"""Qt Logging 설정/상태 화면. 파일 I/O는 LoggingSession writer만 수행한다."""
from PySide6.QtCore import QTimer, Slot
from PySide6.QtWidgets import (QComboBox, QFileDialog, QGridLayout, QLabel, QLineEdit,
                              QPlainTextEdit, QPushButton, QVBoxLayout, QWidget)
from .logging_session import LoggingState
from .connection import MOCK_SOURCE_LABEL

LOG_STATUS_REFRESH_MS = 100
LOG_ERROR_LINES = 10


class LoggingView(QWidget):
    def __init__(self, session, receiver_running, parent=None):
        # Dialog/Widget/상태 timer는 메인 스레드에서 생성한다.
        super().__init__(parent)
        self.session = session
        self.receiver_running = receiver_running
        self._closed = False
        self._selecting_path = False
        self._selection_error = ""
        layout = QVBoxLayout(self)
        self._source_text = MOCK_SOURCE_LABEL
        self._recorded_source = None
        self.source_label = QLabel()
        banner = self.source_label
        banner.setWordWrap(True)
        layout.addWidget(banner)
        policy = QLabel("CAN Receiver Start/Stop와 Logging Start/Stop는 별개입니다. "
                        "Receiver 실행 중에만 Start Logging 가능. Receiver Stop은 Logging admission을 닫고 잔여 Queue를 기록합니다. "
                        "기존 파일 덮어쓰기/Append 없음; 새 파일을 직접 선택하세요.")
        policy.setWordWrap(True)
        layout.addWidget(policy)
        controls = QGridLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItem("JSONL", "jsonl")
        self.format_combo.addItem("CSV", "csv")
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setPlaceholderText("출력 파일을 직접 선택하세요")
        self.choose_button = QPushButton("Select output file...")
        self.start_button = QPushButton("Start Logging")
        self.stop_button = QPushButton("Stop Logging")
        controls.addWidget(QLabel("Format"), 0, 0)
        controls.addWidget(self.format_combo, 0, 1)
        controls.addWidget(self.choose_button, 1, 0)
        controls.addWidget(self.path_edit, 1, 1)
        controls.addWidget(self.start_button, 2, 0)
        controls.addWidget(self.stop_button, 2, 1)
        layout.addLayout(controls)
        self.state_label = QLabel()
        self.file_label = QLabel()
        self.count_label = QLabel()
        self.warning_label = QLabel()
        for label in (self.state_label, self.file_label, self.count_label, self.warning_label):
            label.setWordWrap(True)
            layout.addWidget(label)
        layout.addWidget(QLabel("Last logging error"))
        self.error_area = QPlainTextEdit()
        self.error_area.setReadOnly(True)
        self.error_area.document().setMaximumBlockCount(LOG_ERROR_LINES)
        self.error_area.setMaximumHeight(100)
        layout.addWidget(self.error_area)
        self.scope_label = QLabel("Receiver received / GUI processed / Buffer dropped는 상단 표시이며 Clear 이후 구간입니다. "
                                 "아래 Logging 계수는 해당 Logging Start 이후 구간입니다. "
                                 "Clear/DBC Reload는 파일 기록을 초기화하지 않습니다. 표시 Drop과 파일 Queue Drop은 독립입니다.")
        self.scope_label.setWordWrap(True)
        layout.addWidget(self.scope_label)
        layout.addStretch()
        self.choose_button.clicked.connect(self.choose_file)
        self.start_button.clicked.connect(self.start_recording)
        self.stop_button.clicked.connect(self.stop_recording)
        self.timer = QTimer(self)
        self.timer.setInterval(LOG_STATUS_REFRESH_MS)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def set_input_source(self, text):
        # 완료된 파일은 기록 시작 시의 출처를 유지한다. Source 변경으로 과거 파일을 재분류하지 않는다.
        self._source_text = text
        self.refresh()

    def set_output_path(self, path):
        # 사용자가 선택한 새 경로만 반영하며 기록 중 경로 변경을 거부한다.
        if self._closed or self.session.snapshot().active:
            return False
        self.path_edit.setText(str(path))
        self._selection_error = ""
        self.refresh()
        return True

    @Slot()
    def choose_file(self):
        # 파일 Dialog는 Receiver/writer에서 호출하지 않는다. 취소는 기존 선택을 유지한다.
        if self._closed or self._selecting_path or self.session.snapshot().active:
            return
        self._selecting_path = True
        self.refresh()
        try:
            fmt = self.format_combo.currentData()
            filter_text = "CSV files (*.csv);;All files (*)" if fmt == "csv" else "JSONL files (*.jsonl);;All files (*)"
            path, _ = QFileDialog.getSaveFileName(
                self, "Select NEW output file — overwrite/append disabled", "", filter_text,
                options=QFileDialog.Option.DontConfirmOverwrite,
            )
            if path and not self._closed:
                self.set_output_path(path)
        finally:
            self._selecting_path = False
            self.refresh()

    @Slot()
    def start_recording(self):
        # GUI는 현재 Receiver 실행 확인과 Session 요청만 수행한다.
        if self._closed or self._selecting_path or self.session.snapshot().active:
            return
        if not self.receiver_running():
            self._selection_error = "Start CAN Receiver first. Logging is never enabled automatically."
            self.refresh()
            return
        self._selection_error = ""
        self._recorded_source = self._source_text
        self.session.start(self.path_edit.text(), format=self.format_combo.currentData())
        self.refresh()

    @Slot()
    def stop_recording(self):
        # 즉시 수신 admission을 닫고 종료 완료 표시는 timer가 snapshot으로 읽는다.
        if not self._closed:
            self.session.stop()
            self.refresh()

    @Slot()
    def refresh(self):
        # Qt 이벤트 큐에 프레임별 signal을 누적하지 않고 유한 snapshot을 polling한다.
        if self._closed:
            return
        snap = self.session.snapshot()
        self.source_label.setText(f"Current input: {self._source_text} | File source: {self._recorded_source or 'not started'} "
                                  "| Hardware/KPI NOT VERIFIED")
        opening = " | opening file; written count is not yet confirmed" if snap.active and not snap.opened and snap.state is LoggingState.RECORDING else ""
        self.state_label.setText("Logging: " + snap.state.value + opening)
        self.file_label.setText(f"Session file: {snap.path or 'not selected'} | Format: {snap.format.upper()} | "
                               f"opened={snap.opened} / close confirmed={snap.closed}")
        self.count_label.setText(
            f"Receiver frames during this Logging session: {snap.received}\n"
            f"Logged (write + flush completed): {snap.written} | Queue dropped: {snap.queue_dropped} | "
            f"Failed/unconfirmed: {snap.unconfirmed} | Pending: {snap.pending} | In flight: {snap.in_flight}")
        incomplete = snap.queue_dropped > 0 or snap.unconfirmed > 0
        self.warning_label.setText(
            "INCOMPLETE / 확인 불가 — Queue 제외 또는 실패 기록이 있습니다. 파일은 부분 기록일 수 있습니다."
            if incomplete or snap.state is LoggingState.ERROR else
            "No measured queue exclusions. 무손실/전원 차단 내구성 보장은 아닙니다.")
        error = self._selection_error or snap.error or ""
        if self.error_area.toPlainText() != error:
            self.error_area.setPlainText(error)
        editable = not snap.active and not self._selecting_path and not self._closed
        self.choose_button.setEnabled(editable)
        self.format_combo.setEnabled(editable)
        self.start_button.setEnabled(editable and self.receiver_running() and bool(self.path_edit.text().strip()))
        self.stop_button.setEnabled(snap.state is LoggingState.RECORDING and not self._closed)

    def close_view(self):
        # MainWindow가 CAN/기록 worker 정리를 완료한 뒤 timer와 편집을 차단한다.
        self._closed = True
        self.timer.stop()
        for widget in (self.choose_button, self.format_combo, self.start_button, self.stop_button):
            widget.setEnabled(False)
