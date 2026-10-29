"""유한 Raw 표의 표시 필터. 수신/Decode/Cache/Logger는 변경하지 않는다."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit, QWidget


class MonitorFilter(QWidget):
    def __init__(self, table, parent=None):
        # 필터는 이미 표시된 행만 숨기며 Frame 객체/원본 행/계수는 보존한다.
        super().__init__(parent)
        self.table = table
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search timestamp, channel, CAN ID or DATA")
        self.search.setClearButtonEnabled(True)
        self.search.setAccessibleName("Search displayed CAN frames")
        self.format_combo = QComboBox()
        self.format_combo.addItems(("All formats", "STD", "EXT"))
        self.format_combo.setAccessibleName("Displayed CAN frame format")
        self.errors_only = QCheckBox("Decode errors only")
        layout.addWidget(QLabel("Filter"))
        layout.addWidget(self.search, 1)
        layout.addWidget(self.format_combo)
        layout.addWidget(self.errors_only)
        self.search.textChanged.connect(self.apply_filter)
        self.format_combo.currentIndexChanged.connect(self.apply_filter)
        self.errors_only.toggled.connect(self.apply_filter)

    def apply_filter(self, *_):
        # 최대 기존 Raw 상한만 순회한다. Backend filter나 새로운 Decode 규칙이 아니다.
        query = self.search.text().strip().casefold()
        selected_format = self.format_combo.currentText()
        for row in range(self.table.rowCount()):
            first = self.table.item(row, 0)
            observation = first.data(Qt.ItemDataRole.UserRole) if first is not None else None
            text = " ".join(self.table.item(row, c).text() for c in range(self.table.columnCount())
                            if self.table.item(row, c) is not None).casefold()
            frame = None if observation is None else observation.frame
            matches = query in text
            if selected_format != "All formats":
                # Error frame을 STD 데이터로 오인하지 않고 원래 format 속성만 사용한다.
                matches = matches and frame is not None and not frame.is_error_frame
                matches = matches and (("EXT" if frame.is_extended_id else "STD") == selected_format)
            if self.errors_only.isChecked():
                result = None if observation is None else observation.decoded
                matches = matches and observation is not None and bool(
                    observation.processing_error or (result is not None and result.decode_status.value == "invalid"))
            self.table.setRowHidden(row, not matches)
