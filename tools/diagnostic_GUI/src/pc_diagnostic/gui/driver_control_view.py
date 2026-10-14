"""Qt 메인 스레드의 Driver Control 표시. Mock 요청/ECU 관측을 분리한다."""
from PySide6.QtCore import Qt, QSignalBlocker
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QFormLayout,
                              QHBoxLayout, QLabel, QLineEdit, QPushButton, QSlider,
                              QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)
from .driver_input import (DriverInputModel, DriverInputs, GEAR_CHOICES, HISTORY_CAPACITY,
                           LIVE_MODE, MOCK_MODE, InputState, ACCELERATOR_MIN, ACCELERATOR_MAX)

HISTORY_HEADERS = ("PC Time", "Source", "Action", "Inputs", "Result / Error")


class DriverControlView(QWidget):
    def __init__(self, owner, parent=None, *, model=None):
        # 이 화면은 수신 Worker/Codec/Bus를 소유하거나 호출하지 않는다.
        super().__init__(parent)
        self.owner = owner
        self.model = model if model is not None else DriverInputModel(clock=owner._clock)
        layout = QVBoxLayout(self)
        self.policy_label = QLabel(
            "DEMO / TEST ONLY · 메모리 Mock 입력만 처리 · 물리 CAN 송신 없음\n"
            "0–100% / Brake ON·OFF / P·N·D·R / OPEN·CLOSE / ON·OFF는 Mock 정책입니다.\n"
            "동시 Accelerator+Brake는 그대로 기록하며 제어 우선순위는 VCU 검토 필요입니다.")
        self.policy_label.setWordWrap(True)
        layout.addWidget(self.policy_label)
        self.source_label = QLabel()
        self.approval_label = QLabel(self.model.approval_status + " · PC 입력 CAN ID/Payload/주기/Timeout 미승인")
        self.approval_label.setWordWrap(True)
        layout.addWidget(self.source_label)
        layout.addWidget(self.approval_label)
        form = QFormLayout()
        self.accelerator_edit = QLineEdit()
        self.accelerator_edit.setPlaceholderText("미설정 · Mock % (0..100)")
        self.accelerator_slider = QSlider(Qt.Orientation.Horizontal)
        self.accelerator_slider.setRange(int(ACCELERATOR_MIN), int(ACCELERATOR_MAX))
        accelerator = QHBoxLayout()
        accelerator.addWidget(self.accelerator_slider)
        accelerator.addWidget(self.accelerator_edit)
        form.addRow("Accelerator (Mock %)", accelerator)
        self.brake_combo = self._choices(("OFF", "ON"))
        self.gear_combo = self._choices(GEAR_CHOICES)
        form.addRow("Brake (Mock bool)", self.brake_combo)
        form.addRow("Gear (Mock choice)", self.gear_combo)
        self.window_combo = self._choices(("OPEN", "CLOSE"))
        self.light_combo = self._choices(("ON", "OFF"))
        self.window_open_button = QPushButton("Window Open")
        self.window_close_button = QPushButton("Window Close")
        self.light_on_button = QPushButton("Light ON")
        self.light_off_button = QPushButton("Light OFF")
        for label, combo, buttons in (
            ("Window (Mock intent)", self.window_combo, (self.window_open_button, self.window_close_button)),
            ("Light (Mock intent)", self.light_combo, (self.light_on_button, self.light_off_button)),
        ):
            row = QHBoxLayout()
            row.addWidget(combo)
            for button in buttons:
                row.addWidget(button)
            form.addRow(label, row)
        layout.addLayout(form)
        self.torque_label = QLabel("TorqueRequest: VCU 계산 결과 관측 전용 · No Data\n"
                                  "실제 RX 값은 CAN Monitor / Signals, 명시 매핑한 Vehicle Status / Signal Graph에서 확인")
        self.torque_label.setWordWrap(True)
        layout.addWidget(self.torque_label)
        actions = QHBoxLayout()
        self.apply_button = QPushButton("Apply Mock Input")
        self.reset_button = QPushButton("Reset Mock Inputs")
        self.live_tx_button = QPushButton("Live TX Blocked")
        self.live_tx_button.setEnabled(False)
        for button in (self.apply_button, self.reset_button, self.live_tx_button):
            actions.addWidget(button)
        layout.addLayout(actions)
        self.state_label = QLabel()
        self.accepted_label = QLabel()
        self.accepted_label.setWordWrap(True)
        self.ecu_label = QLabel(self.model.ecu_response_status + " · Mock Accepted는 ECU 응답이 아닙니다.")
        self.error_label = QLabel()
        self.error_label.setWordWrap(True)
        for label in (self.state_label, self.accepted_label, self.ecu_label, self.error_label):
            layout.addWidget(label)
        self.history_table = QTableWidget(0, len(HISTORY_HEADERS))
        self.history_table.setHorizontalHeaderLabels(HISTORY_HEADERS)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(QLabel(f"PC 내부 입력 이력 · 최대 {HISTORY_CAPACITY}건 · CAN Logger/ECU 수신 기록과 별도"))
        layout.addWidget(self.history_table, 1)
        self._widgets = (self.accelerator_edit, self.accelerator_slider, self.brake_combo, self.gear_combo,
                         self.window_combo, self.light_combo, self.window_open_button, self.window_close_button,
                         self.light_on_button, self.light_off_button)
        self.accelerator_slider.valueChanged.connect(self.slider_changed)
        self.accelerator_edit.textChanged.connect(self.edit_inputs)
        for combo in (self.brake_combo, self.gear_combo, self.window_combo, self.light_combo):
            combo.currentIndexChanged.connect(self.edit_inputs)
        self.window_open_button.clicked.connect(lambda: self.choose_body(self.window_combo, "OPEN"))
        self.window_close_button.clicked.connect(lambda: self.choose_body(self.window_combo, "CLOSE"))
        self.light_on_button.clicked.connect(lambda: self.choose_body(self.light_combo, "ON"))
        self.light_off_button.clicked.connect(lambda: self.choose_body(self.light_combo, "OFF"))
        self.apply_button.clicked.connect(self.apply_mock)
        self.reset_button.clicked.connect(self.reset_inputs)
        self._rendered_history = ()
        self.refresh()

    @staticmethod
    def _choices(choices):
        # 첫 항목은 미설정이며 CAN Enum 값으로 인코딩하지 않는다.
        combo = QComboBox()
        combo.addItem("Not Configured", None)
        for choice in choices:
            combo.addItem(choice, choice)
        return combo

    def _can_edit(self):
        # 실제 선택 모드도 점검하여 직접 Slot 호출로 Live 차단을 우회하지 못하게 한다.
        return (not self.owner._closing and not self.model.closed
                and self.owner.connection_view.mode_combo.currentText() == MOCK_MODE
                and self.model.mode == MOCK_MODE and not self.owner.automation_active())

    def slider_changed(self, value):
        # Slider는 Mock % 표시 도우미이며 CAN Scale을 적용하지 않는다.
        if self._can_edit():
            self.accelerator_edit.setText(str(value))

    def choose_body(self, combo, value):
        # 버튼은 draft만 바꾸며 사용자의 Apply 전에는 Mock Adapter도 호출하지 않는다.
        if not self._can_edit():
            return
        index = combo.findData(value)
        if index == combo.currentIndex():
            self.edit_inputs()  # 반복 입력 사실도 유한 이력에 남긴다.
        else:
            combo.setCurrentIndex(index)

    def _read_inputs(self):
        # 빈 값/미선택과 0/OFF를 구분한다. 변환 실패는 UI에서 숨기지 않는다.
        text = self.accelerator_edit.text().strip()
        accelerator = float(text) if text else None
        brake = self.brake_combo.currentData()
        return DriverInputs(accelerator, None if brake is None else brake == "ON",
                            self.gear_combo.currentData(), self.window_combo.currentData(),
                            self.light_combo.currentData())

    def edit_inputs(self):
        # 메인 스레드의 편집을 독립 모델에 전달하고 실제 ECU Cache는 갱신하지 않는다.
        if not self._can_edit():
            return
        try:
            inputs = self._read_inputs()
        except ValueError:
            self.model.reject_input("Accelerator numeric conversion failed.")
        else:
            self.model.stage(inputs)
        self.refresh()

    def apply_mock(self):
        # Live/종료/Automation 중에는 직접 호출도 무효이며 어떤 Bus.send도 실행하지 않는다.
        if not self._can_edit():
            self.refresh()
            return None
        self.edit_inputs()
        receipt = self.model.apply_mock() if self.model.state == InputState.MOCK_INPUT else None
        self.refresh()
        return receipt

    def _clear_widgets(self):
        # 초기화 과정의 Qt signal이 새 입력 이력으로 처리되지 않도록 막는다.
        blockers = [QSignalBlocker(widget) for widget in self._widgets]
        self.accelerator_edit.clear()
        self.accelerator_slider.setValue(int(ACCELERATOR_MIN))
        for combo in (self.brake_combo, self.gear_combo, self.window_combo, self.light_combo):
            combo.setCurrentIndex(0)
        del blockers

    def reset_inputs(self):
        # Reset은 PC 메모리만 비우며 차량 정지 명령이 아니다.
        if self.owner._closing or self.model.closed:
            return
        self.model.reset()
        self._clear_widgets()
        self.refresh()

    def set_input_source(self, source, *, is_mock):
        # Source 변경 때 이전 Mock 결과/미적용 draft를 격리한다.
        mode = MOCK_MODE if is_mock else LIVE_MODE
        changed = (mode, source) != (self.model.mode, self.model.source)
        self.model.set_source(mode, source)
        if changed:
            self._clear_widgets()
        self.refresh()

    def refresh(self):
        # Worker signal을 연결하지 않는다. Qt 메인 스레드 이벤트에서만 화면을 갱신한다.
        enabled = self._can_edit()
        for widget in self._widgets:
            widget.setEnabled(enabled)
        self.apply_button.setEnabled(enabled)
        self.reset_button.setEnabled(not self.owner._closing and not self.model.closed)
        self.live_tx_button.setEnabled(False)
        self.source_label.setText(f"Input Source: {self.model.source} · {self.model.mode}")
        self.state_label.setText(f"Request State: {self.model.state.value} · Applied to Mock: {self.model.applied}")
        receipt = self.model.last_accepted
        self.accepted_label.setText(
            f"Last Mock Accepted: PC #{receipt.command.sequence} @ {receipt.command.timestamp:.6f} · {receipt.command.inputs}"
            if receipt else "Last Mock Accepted: No Data")
        self.error_label.setText(self.model.error or "Live TX Blocked · Awaiting Interface Approval · No physical TX")
        history = self.model.history
        if history == self._rendered_history:
            return
        self._rendered_history = history
        self.history_table.setRowCount(len(history))
        for row, record in enumerate(history):
            cells = ("unknown" if record.timestamp is None else f"{record.timestamp:.6f}",
                     record.source, record.action, str(record.inputs) if record.inputs else "Not Configured",
                     record.state.value + (f" · {record.error}" if record.error else ""))
            for column, cell in enumerate(cells):
                self.history_table.setItem(row, column, QTableWidgetItem(cell))

    def close_view(self):
        # 종료 후 재진입을 막고 메모리 Adapter를 정리한다. 추가 Thread/Timer는 없다.
        self.model.close()
        self.refresh()
