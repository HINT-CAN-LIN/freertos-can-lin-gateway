"""Non-modal, bounded log for the PC↔VCU UART connection."""
from datetime import datetime

from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout


MAX_UART_LOG_LINES = 3000


class UartConnectionLogDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VCU UART Connection Log")
        self.resize(760, 420)
        layout = QVBoxLayout(self)
        self.status_label = QLabel("Connection events, transmitted packets, and VCU ACKs")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.document().setMaximumBlockCount(MAX_UART_LOG_LINES)
        self.log_text.setPlaceholderText("UART connection log will appear here.")
        layout.addWidget(self.log_text, 1)
        buttons = QHBoxLayout()
        self.clear_button = QPushButton("Clear Log")
        self.close_button = QPushButton("Close")
        buttons.addWidget(self.clear_button)
        buttons.addStretch(1)
        buttons.addWidget(self.close_button)
        layout.addLayout(buttons)
        self.clear_button.clicked.connect(self.log_text.clear)
        self.close_button.clicked.connect(self.hide)

    def append_event(self, message):
        timestamp = datetime.now().astimezone().strftime("%H:%M:%S.%f")[:-3]
        self.log_text.appendPlainText(f"[{timestamp}] {message}")
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    def show_log(self):
        self.show()
        self.raise_()
        self.activateWindow()
