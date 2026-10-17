"""기존 View의 배치만 구성한다. 값·매핑·수신·파일 기록 계약은 그대로 둔다."""
from PySide6.QtCore import Qt, QObject, QEvent
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidgetItem, QHeaderView
from .theme import role
from .ui_components import ChoiceStrip, Disclosure, ElidedLabel, take_items, put_item, sync_driver_presentation

PAGE_SPACING = 5
HISTORY_MIN_HEIGHT = 150


def caption(layout, text):
    # 주요 작업/관측 영역을 문자로 구분한다.
    label = role(QLabel(text), "muted")
    label.setWordWrap(True)
    layout.addWidget(label)
    return label


def reset_page(view):
    # 기존 Widget의 parent와 Signal 연결을 보존하는 배치 이동이다.
    layout = view.layout()
    items = take_items(layout)
    layout.setContentsMargins(4, 4, 4, 4)
    layout.setSpacing(PAGE_SPACING)
    view.ui_sections = []
    return layout, items


def fold(view, layout, title, items, *, expanded=False):
    # 기존 상세 문자열은 삭제하지 않고 키보드로 펼칠 수 있게 한다.
    section = Disclosure(view, layout, title, items, expanded=expanded)
    view.ui_sections.append(section)
    return section


class ResponsiveFields(QObject):
    def __init__(self, view, grid, field_count):
        # 선택 상태는 유지하고 좁은 페이지의 폼만 두 열로 재배치한다.
        super().__init__(view)
        self.view, self.grid, self.field_count = view, grid, field_count
        self.original = [(grid.itemAt(i).widget(), grid.getItemPosition(i)) for i in range(grid.count())]
        self.compact = None
        view.installEventFilter(self)
        self.arrange()

    def arrange(self):
        # 최소 창 폭을 강제하지 않도록 긴 확인 문구는 전체 행에 배치한다.
        compact = self.view.width() < 760
        if compact == self.compact:
            return
        self.compact = compact
        for widget, _ in self.original:
            if widget is not None:
                self.grid.removeWidget(widget)
        if not compact:
            for widget, position in self.original:
                if widget is not None:
                    self.grid.addWidget(widget, *position)
            return
        extras = []
        for widget, (row, column, rows, columns) in self.original:
            if widget is None:
                continue
            if row < 2 and column < self.field_count:
                self.grid.addWidget(widget, 2 * (column // 2) + row, column % 2)
            else:
                extras.append(widget)
        next_row = 2 * ((self.field_count + 1) // 2)
        for widget in extras:
            self.grid.addWidget(widget, next_row, 0, 1, 2)
            next_row += 1

    def eventFilter(self, watched, event):
        # Qt 필수 override. 별도 타이머/이벤트 Queue를 만들지 않는다.
        if event.type() in (QEvent.Type.Resize, QEvent.Type.Show):
            self.arrange()
        return super().eventFilter(watched, event)


def polish_mapping(view, *, ecu=False):
    # 명시적 출처 확인/Apply 계약은 유지하며 관측 테이블과 설정을 구분한다.
    layout, items = reset_page(view)
    view.ui_fields = ResponsiveFields(view, items[2].layout(), 4)
    caption(layout, "Observed ≠ Healthy / Online · CAN RX 관측만 표시" if ecu else
            "명시적 Signal 매핑 · Valid ≠ ECU Health · 자동 매핑 없음")
    fold(view, layout, "Mapping settings · explicit source confirmation", [items[2]], expanded=True)
    fold(view, layout, "Source / definition / policy details",
         items[:2] + items[3:5] if ecu else items[:2] + [items[3]])
    caption(layout, "ECU observations / CAN statistics / Fault observation" if ecu else "Vehicle values / last valid cache")
    put_item(layout, items[-1], 1)
    if not ecu:
        # 시각적 열 순서만 변경한다. 기존 logical column/테스트 접근은 그대로다.
        header = view.table.horizontalHeader()
        for visual, logical in enumerate((0, 3, 4, 7, 6, 5, 1, 2, 8)):
            header.moveSection(header.visualIndex(logical), visual)


def polish_driver(view):
    # 입력 모델/Validation을 복제하지 않고 기존 ComboBox를 버튼 표시의 기준으로 쓴다.
    view.choice_strips = {}
    for name, choices in (("ignition", ("OFF", "ON", "RUN")), ("brake", ("OFF", "ON")), ("gear", ("P", "N", "D", "R"))):
        combo = getattr(view, name + "_combo")
        strip = ChoiceStrip(combo, choices, view)
        form = view._input_boxes[0].layout()
        form.replaceWidget(combo, strip)
        combo.hide()
        view.choice_strips[name] = strip
    body_form = view._input_boxes[1].layout()
    for name, choices, buttons in (
        ("window", ("OPEN", "CLOSE"), (view.window_open_button, view.window_close_button)),
        ("light", ("ON", "OFF"), (view.light_on_button, view.light_off_button)),
    ):
        row = body_form.itemAt(0 if name == "window" else 1, body_form.ItemRole.FieldRole).layout()
        take_items(row)
        strip = ChoiceStrip(getattr(view, name + "_combo"), choices, view, buttons=buttons)
        row.addWidget(strip)
        view.choice_strips[name] = strip
    layout, items = reset_page(view)
    caption(layout, "MOCK / TEST ONLY · 0x600 PC → VCU · Payload Pending · Live TX BLOCKED")
    put_item(layout, items[5])  # 주요 Apply / Reset을 입력 및 이력보다 먼저 노출한다.
    put_item(layout, items[3])
    result_box = items[6].widget()
    result_layout = result_box.layout()
    result_layout.removeWidget(view.accepted_label)
    view.receipt_summary = QLabel()
    result_layout.insertWidget(1, view.receipt_summary)
    put_item(layout, items[6])
    fold(view, layout, "Input source / approval / receipt details",
         items[:3] + [items[4], QWidgetItem(view.accepted_label)])
    put_item(layout, items[7])
    view.history_table.setMinimumHeight(HISTORY_MIN_HEIGHT)
    put_item(layout, items[8], 1)
    sync_driver_presentation(view)


def polish_graph(view):
    # 그래프 Sample/Timer/Pause 정책을 변경하지 않고 캔버스 표시 공간을 확보한다.
    layout, items = reset_page(view)
    caption(layout, "Explicit DBC Signal · Pause: display only · No Data until received")
    put_item(layout, items[2])
    view.ui_value = ElidedLabel()
    view.ui_state = ElidedLabel()
    layout.addWidget(view.ui_value)
    layout.addWidget(view.ui_state)
    put_item(layout, items[6], 1)
    fold(view, layout, "Source / full value / statistics / policy details", items[:2] + items[3:6])


def polish_logging(view):
    # 파일 보호/Writer/Flush/Queue에는 접근하지 않는다.
    layout, items = reset_page(view)
    role(view.state_label, "metric")
    put_item(layout, items[3])
    caption(layout, "Output file / format / recording controls · new file only")
    put_item(layout, items[2])
    put_item(layout, items[6])  # 부분 파일/오류 경고는 접지 않는다.
    put_item(layout, items[7])
    put_item(layout, items[8])
    view.error_area.textChanged.connect(lambda: view.error_area.setVisible(bool(view.error_area.toPlainText())))
    view.error_area.setVisible(bool(view.error_area.toPlainText()))
    fold(view, layout, "Recording statistics / source / file policy details",
         items[:2] + items[4:6] + [items[9]])
    layout.addStretch()


def polish_automation(view):
    # Catalog/Scenario/Assertion을 그대로 두고 실행·결과의 계층만 구분한다.
    layout, items = reset_page(view)
    caption(layout, "MOCK / FAKE TEST ONLY · 실제 CAN / HIL / ECU PASS 아님")
    caption(layout, "Scenario selection / Run / Cancel")
    put_item(layout, items[1])
    fold(view, layout, "Scenario description", [items[2]])
    role(view.state_label, "page_title")
    put_item(layout, items[3])
    put_item(layout, items[5])
    caption(layout, "Result summary / assertion details")
    put_item(layout, items[6], 1)
    fold(view, layout, "Execution time / policy details", [items[0], items[4]])


def polish_fault(view):
    # Status Unknown 및 ECU 해제와의 차이를 상시 표시한다.
    layout, items = reset_page(view)
    view.ui_fields = ResponsiveFields(view, items[2].layout(), 3)
    view.ui_filters = ResponsiveFields(view, items[3].layout(), 3)
    caption(layout, "Status Unknown · 관측 ≠ Active Fault · Clear History ≠ ECU Fault 해제")
    put_item(layout, items[4])
    fold(view, layout, "Observation source settings", [items[2]], expanded=True)
    caption(layout, "History filters · displayed rows only")
    put_item(layout, items[3])
    caption(layout, "Fault History / selected observation detail")
    put_item(layout, items[6], 1)
    fold(view, layout, "Source / counts / interpretation details", items[:2] + [items[5]])


def polish_pages(owner):
    # UI 레이어에만 적용한다. 원본 View의 공개 속성/상태 문자열은 유지한다.
    polish_driver(owner.driver_control_view)
    polish_mapping(owner.vehicle_view)
    polish_mapping(owner.ecu_view, ecu=True)
    polish_fault(owner.fault_monitor_view)
    polish_graph(owner.graph_view)
    polish_logging(owner.logging_view)
    if owner.automation_view is not None:
        polish_automation(owner.automation_view)
    monitor = owner.tabs.widget(0)
    monitor.layout().insertWidget(0, role(QLabel("RAW CAN frames · filters affect display only / Decode + Signal Cache below"), "muted"))
    owner.table.setFont(QFont("Consolas", 10))
    owner.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
    owner.table.setColumnWidth(0, owner.table.fontMetrics().horizontalAdvance("0000000000.000000") + 24)
    refresh_page_summaries(owner)


def refresh_page_summaries(owner):
    # 기존 UI 갱신에서 표시 문자열만 읽는다. 새로운 polling/통신은 없다.
    graph = owner.graph_view
    if hasattr(graph, "ui_value"):
        graph.ui_value.set_full_text(graph.value_label.text().split("\n")[-1])
        graph.ui_state.set_full_text(" | ".join(graph.state_label.text().split(" | ")[:2]))
