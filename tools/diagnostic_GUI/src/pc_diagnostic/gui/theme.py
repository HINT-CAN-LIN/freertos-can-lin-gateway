"""공통 QSS·테이블 표시 규칙. 통신/상태 판정은 포함하지 않는다."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QAbstractItemView, QStyledItemDelegate, QTableView

# 화면 표시용 디자인 토큰이며 CAN/LIN 주기나 상태 기준이 아니다.
BACKGROUND = "#f2f5f9"
SURFACE = "#ffffff"
INK = "#182b42"
MUTED = "#53657b"
ACCENT = "#087f8c"
WARNING = "#875600"
ERROR = "#b32636"
BORDER = "#d7e0eb"
NAVIGATION = "#14283f"
TABLE_ROW_HEIGHT = 30

STYLE_SHEET = """
QMainWindow, QWidget#workspace { background: #f2f5f9; color: #182b42; }
QWidget { font-family: "Segoe UI"; font-size: 12px; color: #182b42; }
QLabel { background: transparent; }
QLabel[ui_role="compact_title"] { font-size: 16px; font-weight: 700; }
QPushButton[choice="true"]:checked { background: #087f8c; color: white; border-color: #056874; font-weight: 700; }
QLabel[ui_role="title"] { font-size: 23px; font-weight: 700; }
QLabel[ui_role="page_title"] { font-size: 18px; font-weight: 700; }
QLabel[ui_role="muted"] { color: #53657b; }
QLabel[ui_role="metric"] { font-size: 19px; font-weight: 700; }
QLabel[ui_role="warning"] { color: #875600; background: #fff4d9; padding: 3px; border-radius: 5px; }
QLabel[ui_role="error"] { color: #b32636; }
QLabel[ui_role="badge"] { color: #056874; background: #dff3f4; padding: 4px 8px; border-radius: 5px; font-weight: 600; }
QFrame[ui_role="card"], QGroupBox { background: #ffffff; border: 1px solid #d7e0eb; border-radius: 7px; }
QGroupBox { margin-top: 14px; padding: 12px 8px 8px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; }
QPushButton, QToolButton { background: #ffffff; border: 1px solid #c5d1df; border-radius: 5px; padding: 6px 10px; }
QPushButton:hover, QToolButton:hover { background: #eaf1f8; border-color: #8ca4bc; }
QPushButton[ui_role="primary"] { background: #087f8c; color: white; border-color: #087f8c; font-weight: 600; }
QPushButton[ui_role="primary"]:hover { background: #066875; }
QPushButton:disabled, QToolButton:disabled { color: #738196; background: #e9eef4; border-color: #d7e0eb; }
QPushButton:focus, QToolButton:focus, QComboBox:focus, QLineEdit:focus, QListWidget:focus { border: 2px solid #087f8c; }
QLineEdit, QComboBox, QPlainTextEdit { background: white; border: 1px solid #c5d1df; border-radius: 4px; padding: 5px; selection-background-color: #ccebee; }
QComboBox::drop-down { width: 20px; border-left: 1px solid #d7e0eb; }
QComboBox QAbstractItemView { background: white; selection-background-color: #dff3f4; color: #182b42; }
QCheckBox { spacing: 6px; }
QTableView { background: white; alternate-background-color: #f5f8fc; gridline-color: #e6ecf3; border: 1px solid #d7e0eb; selection-background-color: #ccebee; selection-color: #10363d; }
QHeaderView::section { background: #e9eff6; color: #304860; padding: 7px; border: 0; border-right: 1px solid #d7e0eb; font-weight: 600; }
QTableView::item { padding: 3px; }
QTabWidget::pane { border: 0; }
QTabBar::tab { background: #e9eff6; padding: 7px 12px; border-bottom: 2px solid transparent; }
QTabBar::tab:selected { background: white; color: #056874; border-bottom-color: #087f8c; }
QListWidget#navigation { background: #14283f; color: #dce7f3; border: 0; border-radius: 7px; padding: 6px; outline: 0; }
QListWidget#navigation::item { color: #dce7f3; padding: 8px 5px; border-radius: 4px; margin: 2px 0; }
QListWidget#navigation::item:selected { background: #23566b; color: white; font-weight: 600; }
QListWidget#navigation::item:hover { background: #24405d; }
QScrollArea { border: 0; background: transparent; }
QScrollArea > QWidget > QWidget { background: #f2f5f9; }
QSplitter::handle { background: #d7e0eb; }
"""


class DiagnosticDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        # 값/단위 문자열은 그대로 두고 숫자 정렬과 상태의 보조 색상만 적용한다.
        super().initStyleOption(option, index)
        header = str(index.model().headerData(index.column(), Qt.Orientation.Horizontal) or "").lower()
        if any(word in header for word in ("value", "timestamp", "age", "count", "dlc")):
            option.displayAlignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        text = option.text.lower()
        if any(word in text for word in ("error", "failed", "fail")):
            option.palette.setColor(QPalette.ColorRole.Text, QColor(ERROR))
        elif any(word in text for word in ("not verified", "unknown", "no data", "not defined", "no dbc")):
            option.palette.setColor(QPalette.ColorRole.Text, QColor(WARNING))


def role(widget, name):
    # 이름을 통해 같은 의미의 표시 요소에 공통 스타일을 적용한다.
    widget.setProperty("ui_role", name)
    return widget


def apply_theme(window):
    # 창 범위 QSS이므로 CLI/다른 Qt 애플리케이션의 전역 설정을 변경하지 않는다.
    window.setStyleSheet(STYLE_SHEET)
    for table in window.findChildren(QTableView):
        table.setFont(QFont("Consolas", 10))
        table.setAlternatingRowColors(True)
        table.verticalHeader().setDefaultSectionSize(TABLE_ROW_HEIGHT)
        table.setItemDelegate(DiagnosticDelegate(table))
    for widget in window.findChildren(QAbstractItemView):
        widget.setAccessibleName(widget.accessibleName() or "Diagnostic observations")
