"""승인 전 UART 상태를 표시하는 UI 전용 패널. 실제 연결 동작은 제공하지 않는다."""
from PySide6.QtWidgets import QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout
from .theme import role

UART_STATUS = (
    ("interface", "Interface: UART"),
    ("target", "Target: VCU"),
    ("connection", "Connection: NOT CONFIGURED"),
    ("protocol", "Protocol: PENDING APPROVAL"),
    ("tx", "UART TX: DISABLED"),
    ("rx", "UART RX: NOT VERIFIED"),
)


class UartConnectionView(QGroupBox):
    def __init__(self, parent=None):
        # 이 화면은 CAN ConnectionView와 별도이며 DriverTransport를 만들거나 호출하지 않는다.
        super().__init__("PC ↔ VCU Driver Input · UART", parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(3)
        self.status_labels = {}
        for index, (key, text) in enumerate(UART_STATUS):
            value = role(QLabel(text), "warning" if key not in ("interface", "target") else "badge")
            value.setWordWrap(True)
            value.setAccessibleName(text)
            grid.addWidget(value, index // 2, index % 2)
            self.status_labels[key] = value
        layout.addLayout(grid)
        actions = QHBoxLayout()
        self.connect_button = QPushButton("Connect")
        self.disconnect_button = QPushButton("Disconnect")
        self.connect_button.setAccessibleName("UART Connect unavailable")
        self.disconnect_button.setAccessibleName("UART Disconnect unavailable")
        self.connect_button.setEnabled(False)
        self.disconnect_button.setEnabled(False)
        reason = "Disabled: UART protocol and physical connection are not configured or approved."
        self.connect_button.setToolTip(reason)
        self.disconnect_button.setToolTip(reason)
        actions.addWidget(self.connect_button)
        actions.addWidget(self.disconnect_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        self.action_reason_label = QLabel(reason)
        self.action_reason_label.setWordWrap(True)
        layout.addWidget(self.action_reason_label)
        self.response_label = QLabel(
            "VCU Response: NOT IMPLEMENTED / NOT VERIFIED · no automatic ACK or re-command")
        self.response_label.setWordWrap(True)
        self.can_scope_label = QLabel(
            "CAN RX remains in the independent CAN Monitor; CAN RX is not a UART response.")
        self.can_scope_label.setWordWrap(True)
        layout.addWidget(self.response_label)
        layout.addWidget(self.can_scope_label)
        self.connect_button.clicked.connect(self.request_connect)
        self.disconnect_button.clicked.connect(self.request_disconnect)

    def request_connect(self):
        # 비활성 버튼을 코드에서 직접 호출해도 연결 상태나 장치에 접근하지 않는다.
        return False

    def request_disconnect(self):
        # 세션이 없으므로 GUI가 Transport를 생성하거나 해제하지 않는다.
        return False