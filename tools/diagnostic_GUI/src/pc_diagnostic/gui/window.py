"""Raw CAN 표시만 담당하는 Qt 메인 윈도우."""
from PySide6.QtCore import QTimer, Qt, Slot
from PySide6.QtWidgets import (QAbstractItemView, QHBoxLayout, QHeaderView, QLabel,
                              QMainWindow, QPlainTextEdit, QPushButton, QTableWidget,
                              QTableWidgetItem, QVBoxLayout, QWidget)
from ..interfaces import MockCanInterface
from .buffer import FrameBuffer
from .receiver import CLOSE_WAIT_MS, ReceiveWorker

# 아래 값은 GUI 표시 자원 제한이며 통신 규격 수치가 아니다.
DISPLAY_REFRESH_MS = 50
MAX_TABLE_ROWS = 500
MAX_ERROR_LINES = 50
WINDOW_WIDTH = 980
WINDOW_HEIGHT = 600


def frame_cells(frame):
    # ID의 숫자를 보존하면서 실제 STD/EXT/ERROR/RTR 속성을 함께 표시한다.
    width = 8 if frame.is_extended_id or frame.is_error_frame else 3
    kind = "ERROR" if frame.is_error_frame else ("EXT" if frame.is_extended_id else "STD")
    if frame.is_remote_frame:
        kind += " RTR"
    timestamp = "unknown" if frame.timestamp is None else f"{frame.timestamp:.6f}"
    channel = "unknown" if frame.channel is None else str(frame.channel)
    return (timestamp, channel, f"0x{frame.arbitration_id:0{width}X} ({kind})",
            str(frame.dlc), frame.data.hex(" ").upper())


class MainWindow(QMainWindow):
    def __init__(self, interface_factory=MockCanInterface):
        # Qt widget와 표시 타이머는 메인 스레드에서만 생성한다.
        super().__init__()
        self._interface_factory = interface_factory
        self.buffer = FrameBuffer()
        self.worker = None
        self._failed = False
        self.setWindowTitle("PC Diagnostic Tool")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.addWidget(QLabel("Mock · DEMO / TEST ONLY — 실제 ECU 데이터가 아닙니다. Hardware NOT VERIFIED"))
        controls = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.clear_button = QPushButton("Clear")
        self.stop_button.setEnabled(False)
        for button in (self.start_button, self.stop_button, self.clear_button):
            controls.addWidget(button)
        self.status_label = QLabel("Disconnected")
        self.counter_label = QLabel("Received: 0")
        self.drop_label = QLabel("표시 버퍼 제외: 0")
        for label in (self.status_label, self.counter_label, self.drop_label):
            controls.addWidget(label)
        layout.addLayout(controls)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Channel", "CAN ID", "DLC", "DATA"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        layout.addWidget(QLabel("오류 메시지"))
        self.error_area = QPlainTextEdit()
        self.error_area.setReadOnly(True)
        self.error_area.document().setMaximumBlockCount(MAX_ERROR_LINES)
        self.error_area.setMaximumHeight(100)
        layout.addWidget(self.error_area)
        self.timer = QTimer(self)
        self.timer.setInterval(DISPLAY_REFRESH_MS)
        self.timer.timeout.connect(self.refresh_frames)
        self.start_button.clicked.connect(self.start_monitor)
        self.stop_button.clicked.connect(self.stop_monitor)
        self.clear_button.clicked.connect(self.clear_monitor)

    @Slot()
    def start_monitor(self):
        # 종료 signal 처리 전까지 worker 참조를 유지해 중복 실행을 차단한다.
        if self.worker is not None:
            return
        self._failed = False
        self.error_area.clear()
        self.worker = ReceiveWorker(self.buffer, self._interface_factory, self)
        self.worker.failed.connect(self.show_error)
        self.worker.finished.connect(self.worker_finished)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("Running")
        self.timer.start()
        self.worker.start()

    @Slot()
    def stop_monitor(self):
        # 비동기 정지: UI 응답을 유지하면서 worker의 취소 이벤트만 설정한다.
        if self.worker is not None:
            self.stop_button.setEnabled(False)
            self.worker.request_stop()

    @Slot(str)
    def show_error(self, message):
        # Error는 worker 종료 후에도 유지하여 실패 원인을 확인할 수 있게 한다.
        self._failed = True
        self.status_label.setText("Error")
        self.error_area.appendPlainText(message)

    @Slot()
    def worker_finished(self):
        # 수신 잔여 데이터는 제한된 batch로 처리하고 종료된 thread를 해제한다.
        self.refresh_frames()
        self.stop_button.setEnabled(False)
        self.start_button.setEnabled(True)
        if not self._failed:
            self.status_label.setText("Stopped")
        completed = self.worker
        if completed is not None and not completed.wait(CLOSE_WAIT_MS):
            # finished 이후에도 native thread 정리를 확인하지 못하면 참조를 유지한다.
            self.start_button.setEnabled(False)
            self.show_error("Worker cleanup timed out; close again after it finishes.")
            return
        self.worker = None
        if completed is not None:
            completed.deleteLater()
        # 정지 후 남은 버퍼도 timer로 비우되 새 수신은 발생하지 않는다.

    @Slot()
    def refresh_frames(self):
        # 한 번에 제한된 행만 추가하고 화면/대기 버퍼 모두 유한하게 유지한다.
        frames, total, dropped = self.buffer.drain()
        for frame in frames:
            if self.table.rowCount() >= MAX_TABLE_ROWS:
                self.table.removeRow(0)
            row = self.table.rowCount()
            self.table.insertRow(row)
            for column, value in enumerate(frame_cells(frame)):
                self.table.setItem(row, column, QTableWidgetItem(value))
        self.counter_label.setText(f"Received: {total}")
        self.drop_label.setText(f"표시 버퍼 제외: {dropped}")
        if self.worker is None and not frames:
            self.timer.stop()

    @Slot()
    def clear_monitor(self):
        # 통신 상태를 바꾸지 않고 화면과 표시 계수만 초기화한다.
        self.buffer.clear()
        self.table.setRowCount(0)
        self.counter_label.setText("Received: 0")
        self.drop_label.setText("표시 버퍼 제외: 0")

    def closeEvent(self, event):
        # Qt 필수 override 명칭은 snake_case 규칙의 예외이다.
        # 제한 시간 안에 종료되지 않으면 창을 유지하여 실행 중 QThread 파괴를 방지한다.
        if self.worker is not None:
            self.worker.request_stop()
            if not self.worker.wait(CLOSE_WAIT_MS):
                self.show_error("Worker stop timed out; close again after it finishes.")
                event.ignore()
                return
        self.timer.stop()
        event.accept()
