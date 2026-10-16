"""접이식 정보·긴 이름·선택 버튼의 표시 도우미. 통신/입력 계약은 변경하지 않는다."""
from PySide6.QtCore import QEvent, QObject, Qt, QSignalBlocker
from PySide6.QtWidgets import (
    QButtonGroup, QHBoxLayout, QLabel, QPushButton, QToolButton, QVBoxLayout, QWidget,
)


class ElidedLabel(QLabel):
    def __init__(self, parent=None):
        # 전체 문자열은 tooltip/accessibility에 보존하고 화면 폭만 제한한다.
        super().__init__(parent)
        self.full_text = ""
        self.setMinimumWidth(0)

    def set_full_text(self, text):
        # 원래 Label/Model 값을 수정하지 않는 읽기 전용 표시 사본이다.
        self.full_text = str(text)
        self.setToolTip(self.full_text)
        self.setAccessibleName(self.full_text)
        self._render()

    def _render(self):
        # 중요한 문자열 끝도 볼 수 있도록 중간만 생략한다.
        self.setText(self.fontMetrics().elidedText(self.full_text, Qt.TextElideMode.ElideMiddle, max(1, self.width())))

    def resizeEvent(self, event):
        # Qt 필수 override: 크기 변경은 표시만 갱신한다.
        super().resizeEvent(event)
        self._render()

    def minimumSizeHint(self):
        # 긴 DBC 이름이 페이지/창의 최소 폭을 강제하지 않게 한다.
        from PySide6.QtCore import QSize
        return QSize(0, super().minimumSizeHint().height())


def take_items(layout):
    # 기존 위젯/Signal은 보존하고 배치 항목만 이동할 수 있게 한다.
    result = []
    while layout.count():
        item = layout.takeAt(0)
        if item.layout() is not None:
            item.layout().setParent(None)
        result.append(item)
    return result


def put_item(layout, item, stretch=0):
    # 같은 parent의 배치만 옮겨 findChildren/공개 Widget identity를 보존한다.
    if item.widget() is not None:
        layout.addWidget(item.widget(), stretch)
    elif item.layout() is not None:
        layout.addLayout(item.layout(), stretch)
    else:
        layout.addItem(item)


def item_widgets(item):
    # QWidget 내부까지 임의 재귀하지 않고 그 Widget의 기존 자식 소유권을 유지한다.
    if item.widget() is not None:
        return [item.widget()]
    if item.layout() is not None:
        return [widget for i in range(item.layout().count()) for widget in item_widgets(item.layout().itemAt(i))]
    return []


class Disclosure(QObject):
    def __init__(self, parent, root_layout, title, items, *, expanded=False):
        # 별도 content QWidget으로 재부모화하지 않아 기존 Widget 검색 순서를 보존한다.
        super().__init__(parent)
        self.button = QToolButton(parent)
        self.button.setText(title)
        self.button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.button.setCheckable(True)
        self.button.setAccessibleName(title)
        self.content = QVBoxLayout()
        self.content.setContentsMargins(0, 0, 0, 0)
        self.content.setSpacing(3)
        self.widgets = []
        root_layout.addWidget(self.button)
        root_layout.addLayout(self.content)
        for item in items:
            self.widgets.extend(item_widgets(item))
            put_item(self.content, item)
        self.button.toggled.connect(self.set_expanded)
        self.button.setChecked(expanded)
        self.set_expanded(expanded)

    def set_expanded(self, expanded):
        # enabled/선택/값은 바꾸지 않고 정보의 접기/펼치기만 수행한다.
        self.button.setArrowType(Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow)
        if self.button.isChecked() != expanded:
            self.button.setChecked(expanded)
        for widget in self.widgets:
            widget.setVisible(expanded)


class ChoiceStrip(QWidget):
    def __init__(self, combo, choices, parent=None, *, buttons=None):
        # 기존 ComboBox를 단일 선택 기준으로 쓰며 새 입력 모델/Enum을 만들지 않는다.
        super().__init__(parent)
        self.combo = combo
        self.choices = tuple(choices)
        self.buttons = {}
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        for index, choice in enumerate(self.choices):
            button = buttons[index] if buttons is not None else QPushButton(str(choice))
            button.setCheckable(True)
            button.setProperty("choice", True)
            button.setAccessibleName(f"{combo.accessibleName() or 'Mock choice'} {choice}")
            self.group.addButton(button)
            layout.addWidget(button)
            self.buttons[choice] = button
            if buttons is None:
                button.clicked.connect(lambda checked=False, value=choice: self.choose(value))
        combo.currentIndexChanged.connect(self.sync)
        combo.installEventFilter(self)
        combo.hide()
        self.sync()

    def choose(self, value):
        # 비활성 기존 편집기를 우회하지 않는다. 기존 Signal/Validation 경로만 호출한다.
        if self.combo.isEnabled():
            self.combo.setCurrentIndex(self.combo.findData(value))
        self.sync()

    def sync(self, *_):
        # Reset의 signal blocker 이후도 호출 가능하며 미설정 상태를 강제 선택하지 않는다.
        value = self.combo.currentData()
        self.group.setExclusive(False)
        for choice, button in self.buttons.items():
            button.setChecked(value == choice)
            button.setEnabled(self.combo.isEnabled())
        self.group.setExclusive(True)

    def eventFilter(self, watched, event):
        # Qt 필수 override: Live/종료/Automation 잠금의 기존 enabled 상태를 따른다.
        if watched is self.combo and event.type() == QEvent.Type.EnabledChange:
            self.sync()
        return super().eventFilter(watched, event)


def sync_driver_presentation(view):
    # UI 정수 slider와 실제 입력 소수값을 분리하며 signal 재진입/값 반올림 저장을 막는다.
    for strip in getattr(view, "choice_strips", {}).values():
        strip.sync()
    draft = view.model.draft
    if draft is not None and draft.accelerator is not None:
        blocker = QSignalBlocker(view.accelerator_slider)
        view.accelerator_slider.setValue(round(draft.accelerator))
        del blocker
    if hasattr(view, "receipt_summary"):
        receipt = view.model.last_accepted
        view.receipt_summary.setText(f"Mock Accepted · PC #{receipt.command.sequence}" if receipt else "Mock Accepted: No Data")
        view.error_label.setVisible(bool(view.model.error))
