"""MainWindow의 화면 배치/탐색만 구성한다. 기존 View와 슬롯은 그대로 재사용한다."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QScrollArea, QSizePolicy, QTabWidget, QToolButton, QVBoxLayout, QWidget,
)
from .dashboard_view import DashboardView
from .theme import apply_theme, role
from .ui_components import Disclosure, ElidedLabel
from .page_layouts import polish_pages, refresh_page_summaries
from PySide6.QtWidgets import QWidgetItem

NAVIGATION_WIDTH = 156
CONTENT_MARGIN = 8
ERROR_TRAY_HEIGHT = 64


class WorkspaceTabs(QTabWidget):
    def __init__(self, parent=None):
        # 기존 tab index/View 접근 API를 유지하며 페이지마다 독립 스크롤을 소유한다.
        super().__init__(parent)
        self._areas = {}

    def addTab(self, widget, label):
        # Qt 필수 API override. 다른 페이지의 최소 크기/스크롤을 현재 화면에 전파하지 않는다.
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setWidget(widget)
        self._areas[widget] = area
        return super().addTab(area, label)

    def widget(self, index):
        # 호출자는 기존처럼 실제 View 객체를 받는다.
        area = super().widget(index)
        return None if area is None else area.widget()

    def currentWidget(self):
        # Qt 표준 API의 기존 View identity를 보존한다.
        return self.widget(self.currentIndex())

    def indexOf(self, widget):
        # 공개 View 참조를 내부 scroll page index로만 변환한다.
        return super().indexOf(self._areas.get(widget, widget))

    def setCurrentWidget(self, widget):
        # 기존 Native/자동화의 직접 페이지 선택도 그대로 동작한다.
        super().setCurrentWidget(self._areas.get(widget, widget))

    def current_scroll(self):
        # 페이지별 스크롤 접근만 제공하며 화면 데이터에는 접근하지 않는다.
        return super().widget(self.currentIndex())


def release_layout(layout):
    # 위젯은 파괴하지 않는다. 기존 임시 배치의 Layout 소유권만 비워 새 shell에 재배치한다.
    while layout.count():
        item = layout.takeAt(0)
        if item.layout() is not None:
            release_layout(item.layout())
            item.layout().deleteLater()
        elif item.widget() is not None:
            item.widget().hide()


def install_workspace(owner, layout):
    # 기존 속성/Tab index/버튼/Signal 계약을 유지하고 레이아웃만 교체한다.
    release_layout(layout)
    owner.centralWidget().setObjectName("workspace")
    layout.setContentsMargins(CONTENT_MARGIN, CONTENT_MARGIN, CONTENT_MARGIN, CONTENT_MARGIN)
    layout.setSpacing(5)
    owner.compact_header = QWidget()
    header = QVBoxLayout(owner.compact_header)
    header.setContentsMargins(0, 0, 0, 0)
    header.setSpacing(3)
    title_row = QHBoxLayout()
    owner.app_title = role(ElidedLabel(), "compact_title")
    owner.app_title.set_full_text("PC Diagnostic Tool")
    title_row.addWidget(owner.app_title, 1)
    owner.source_badge = role(QLabel(), "badge")
    owner.hardware_badge = role(QLabel("Hardware NOT VERIFIED"), "warning")
    owner.tx_badge = role(QLabel("Driver TX BLOCKED · Interface Pending"), "warning")
    for label in (owner.source_badge, owner.hardware_badge, owner.tx_badge):
        label.setWordWrap(True)
        title_row.addWidget(label)
    header.addLayout(title_row)
    toolbar = QHBoxLayout()
    for button in (owner.start_button, owner.stop_button, owner.clear_button, owner.dbc_button):
        toolbar.addWidget(button)
        button.show()
        button.setAccessibleName(button.text().replace("...", ""))
    role(owner.start_button, "primary")
    owner.connection_toggle = QToolButton()
    owner.connection_toggle.setText("Connection settings")
    owner.connection_toggle.setCheckable(True)
    owner.connection_toggle.setAccessibleName("Show connection settings")
    toolbar.addWidget(owner.connection_toggle)
    toolbar.addStretch()
    header.addLayout(toolbar)
    owner.dbc_summary = role(ElidedLabel(), "muted")
    status_row = QHBoxLayout()
    status_row.addWidget(owner.dbc_summary, 1)
    for label in (owner.status_label, owner.counter_label):
        status_row.addWidget(label)
        label.show()
    header.addLayout(status_row)
    layout.addWidget(owner.compact_header)
    owner.connection_panel = role(QFrame(), "card")
    connection_layout = QVBoxLayout(owner.connection_panel)
    connection_layout.addWidget(owner.connection_view)
    owner.connection_view.show()
    layout.addWidget(owner.connection_panel)
    owner.connection_panel.hide()
    owner.connection_toggle.toggled.connect(owner.connection_panel.setVisible)
    # 상세 문구/계수는 보존하며 상시 안전 badge와 구분한다.
    owner.header_details = Disclosure(owner.centralWidget(), layout, "Source / DBC / RX details",
        [QWidgetItem(widget) for widget in
         (owner.dbc_label, owner.banner, owner.drop_label, owner.processed_label, owner.dbc_policy_label)])

    owner.dashboard_view = DashboardView(owner, owner)
    owner.tabs.addTab(owner.dashboard_view, "Dashboard")
    owner.tabs.tabBar().hide()
    owner.navigation = QListWidget()
    owner.navigation.setObjectName("navigation")
    owner.navigation.setFixedWidth(NAVIGATION_WIDTH)
    owner.navigation.setAccessibleName("Diagnostic pages")
    owner._navigation_shortcuts = []
    pages = [
        ("Dashboard", owner.dashboard_view),
        ("Driver Control", owner.driver_control_view),
        ("CAN Monitor / Decode", owner.tabs.widget(0)),
        ("Vehicle Status", owner.vehicle_view),
        ("ECU Observation", owner.ecu_view),
        ("Fault Monitor", owner.fault_monitor_view),
        ("Signal Graph", owner.graph_view),
        ("Logging", owner.logging_view),
    ]
    if owner.automation_view is not None:
        pages.append(("Test Automation", owner.automation_view))
    for row, (title, page) in enumerate(pages):
        item = QListWidgetItem(title)
        item.setData(Qt.ItemDataRole.UserRole, owner.tabs.indexOf(page))
        item.setToolTip(f"{title} · Alt+{row + 1}")
        owner.navigation.addItem(item)
        shortcut = QShortcut(QKeySequence(f"Alt+{row + 1}"), owner)
        shortcut.activated.connect(lambda index=row: owner.navigation.setCurrentRow(index))
        owner._navigation_shortcuts.append(shortcut)
    owner.navigation.currentRowChanged.connect(
        lambda row: owner.tabs.setCurrentIndex(owner.navigation.item(row).data(Qt.ItemDataRole.UserRole)) if row >= 0 else None)
    owner.page_title = role(QLabel(), "page_title")
    owner.page_scroll = owner.tabs.current_scroll()
    owner.tabs.show()
    content = QVBoxLayout()
    content.addWidget(owner.page_title)
    content.addWidget(owner.tabs, 1)
    body = QHBoxLayout()
    body.addWidget(owner.navigation)
    body.addLayout(content, 1)
    layout.addLayout(body, 1)
    owner.tabs.currentChanged.connect(lambda *_: sync_navigation(owner))
    sync_navigation(owner)
    owner.error_area.setMaximumHeight(ERROR_TRAY_HEIGHT)
    owner.error_area.setAccessibleName("Application errors")
    owner.activity_section = Disclosure(owner.centralWidget(), layout, "Activity & Errors",
                                        [QWidgetItem(owner.error_area)])
    def update_error_tray():
        # 새 오류는 즉시 펼쳐 보여 종료 실패의 원인을 숨기지 않는다.
        has_error = bool(owner.error_area.toPlainText().strip())
        owner.activity_section.button.setText("Activity & Errors" + (" · Entries" if has_error else " · Empty"))
        owner.activity_section.set_expanded(has_error)
    owner.error_area.textChanged.connect(update_error_tray)
    update_error_tray()
    polish_pages(owner)

    # 긴 Message/Source 이름은 선택 목록과 tooltip에 남기고 작은 화면의 최소 폭을 줄인다.
    for combo in owner.findChildren(QComboBox):
        combo.setMinimumContentsLength(8)
        combo.setToolTip(combo.currentText())
        combo.currentTextChanged.connect(combo.setToolTip)
        combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    for edit in owner.findChildren(QLineEdit):
        edit.setMinimumWidth(60)
    apply_theme(owner)
    # CAN ID 전체 숫자와 STD/EXT/RTR을 함께 읽을 수 있는 표시 폭을 확보한다.
    owner.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
    owner.table.setColumnWidth(2, 180)
    refresh_workspace(owner)


def sync_navigation(owner):
    # 기존 tests/API의 tabs.setCurrentWidget도 사이드 탐색과 제목에 반영한다.
    current = owner.tabs.currentIndex()
    owner.page_scroll = owner.tabs.current_scroll()
    for row in range(owner.navigation.count()):
        item = owner.navigation.item(row)
        if item.data(Qt.ItemDataRole.UserRole) == current:
            owner.navigation.setCurrentRow(row)
            owner.page_title.setText(item.text())
            return


def refresh_workspace(owner):
    # 기존 UI timer에서만 호출한다. 새 통신·타이머·승인 상태를 만들지 않는다.
    if not hasattr(owner, "dashboard_view") or owner._closing:
        return
    mode = owner.connection_view.mode_combo.currentText()
    owner.source_badge.setText("MOCK / TEST ONLY" if mode == "Mock" else "LIVE / RX only")
    owner.source_badge.setToolTip(owner.selected_source_text())
    owner.dbc_summary.set_full_text(owner.dbc_label.text())
    refresh_page_summaries(owner)
    owner.dashboard_view.refresh()
