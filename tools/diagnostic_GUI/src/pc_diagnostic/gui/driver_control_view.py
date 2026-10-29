"""Qt Driver Control: Mock adapter와 VCU UART 요청/ACK를 분리해 표시한다."""
from datetime import datetime
from PySide6.QtCore import Qt, QEvent, QSignalBlocker, QTimer
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QFormLayout, QGridLayout, QHeaderView,
                              QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSlider,
                              QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QApplication,
                              QPlainTextEdit, QAbstractSpinBox)
from .theme import role
from .ui_components import sync_driver_presentation
from .driver_input import (DriverInputModel, DriverInputs, GEAR_CHOICES, HISTORY_CAPACITY,
                           LIVE_MODE, MOCK_MODE, InputState, ACCELERATOR_MIN, ACCELERATOR_MAX)
from .uart_worker import VcuUartWorker
from .uart_log_view import UartConnectionLogDialog

HISTORY_HEADERS = ("PC Time", "Source", "Action", "Inputs", "Result / Error")
HISTORY_INPUTS_COLUMN = 3
HISTORY_ROW_HEIGHT = 72


class DriverControlView(QWidget):
    def __init__(self, owner, parent=None, *, model=None):
        # UART worker만 소유한다. CAN monitor의 수신 worker/codec/bus는 사용하지 않는다.
        super().__init__(parent)
        self.owner = owner
        self.model = model if model is not None else DriverInputModel(clock=owner._clock)
        layout = QVBoxLayout(self)
        self.policy_label = QLabel(
            "VCU UART는 ST-LINK VCP로 현재 입력을 100 ms마다 보내고 VCU ACK를 표시합니다. Arrow-key steering은 VCU에 저장되지만 현재 DBC에 없어 CAN 송신에는 포함되지 않습니다.\n"
            "ACK는 VCU 입력 수신·검증 확인입니다. Gateway/CAN 동작은 확인하지 않으며 Light는 Mock 전용입니다.")
        self.policy_label.setWordWrap(True)
        layout.addWidget(self.policy_label)
        self.source_label = role(QLabel(), "badge")
        self.source_label.setWordWrap(True)
        self.approval_label = QLabel("UART: 115200 8N1 · protocol v2 · 15-byte frame · 100 ms TX · VCU safe timeout 500 ms")
        self.approval_label.setWordWrap(True)
        role(self.approval_label, "warning")
        layout.addWidget(self.source_label)
        layout.addWidget(self.approval_label)
        driving_box = QGroupBox("Driving inputs — Mock / VCU UART")
        form = QFormLayout(driving_box)
        self.accelerator_edit = QLineEdit()
        self.accelerator_edit.setPlaceholderText("미설정 · 정수 % (0..100)")
        self.accelerator_slider = QSlider(Qt.Orientation.Horizontal)
        self.accelerator_slider.setRange(int(ACCELERATOR_MIN), int(ACCELERATOR_MAX))
        accelerator = QHBoxLayout()
        accelerator.addWidget(self.accelerator_slider)
        accelerator.addWidget(self.accelerator_edit)
        self.accelerator_edit.setMaximumWidth(120)
        self.accelerator_edit.setAccessibleName("Accelerator percent")
        self.accelerator_value_label = role(QLabel("Not Configured"), "badge")
        accelerator.addWidget(self.accelerator_value_label)
        form.addRow("Accelerator (%)", accelerator)
        self.ignition_combo = self._choices(("OFF", "ON", "RUN"))
        self.brake_combo = self._choices(("OFF", "ON"))
        self.gear_combo = self._choices(GEAR_CHOICES)
        form.addRow("Ignition", self.ignition_combo)
        form.addRow("Brake", self.brake_combo)
        form.addRow("Gear", self.gear_combo)
        keyboard_row = QWidget()
        keyboard_layout = QVBoxLayout(keyboard_row)
        keyboard_layout.setContentsMargins(0, 0, 0, 0)
        keyboard_header = QHBoxLayout()
        self.keyboard_toggle = QPushButton("Enable Arrow-Key Controls")
        self.keyboard_toggle.setCheckable(True)
        self.keyboard_toggle.setAccessibleName("Enable keyboard accelerator, brake, and steering input")
        keyboard_header.addWidget(self.keyboard_toggle)
        self.keyboard_status_label = QLabel("Disabled · click to arm arrow keys")
        self.keyboard_status_label.setWordWrap(True)
        keyboard_header.addWidget(self.keyboard_status_label, 1)
        keyboard_layout.addLayout(keyboard_header)
        indicators = QHBoxLayout()
        self.arrow_indicators = {}
        for key, text in (("up", "↑ Accelerator"), ("down", "↓ Brake"),
                          ("left", "← Steer Left"), ("right", "→ Steer Right")):
            indicator = QLabel(text)
            indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
            indicator.setProperty("arrow_indicator", True)
            indicator.setProperty("pressed", False)
            self.arrow_indicators[key] = indicator
            indicators.addWidget(indicator)
        keyboard_layout.addLayout(indicators)
        self.steering_status_label = QLabel("Steering: CENTER · UART VCU input")
        keyboard_layout.addWidget(self.steering_status_label)
        form.addRow("Keyboard input", keyboard_row)
        self._held_arrow_keys = set()
        self._steering_direction = None
        self._keyboard_timer = QTimer(self)
        self._keyboard_timer.setInterval(100)
        self._keyboard_timer.timeout.connect(self._keyboard_accelerator_tick)
        self._uart_log_dialog = None
        self.window_combo = self._choices(("OPEN", "CLOSE"))
        self.door_combo = self._choices(("LOCK", "UNLOCK"))
        self.light_combo = self._choices(("ON", "OFF"))
        self.window_open_button = QPushButton("Window Open")
        self.window_close_button = QPushButton("Window Close")
        self.light_on_button = QPushButton("Light ON")
        self.light_off_button = QPushButton("Light OFF")
        body_box = QGroupBox("Body inputs — Mock / VCU UART")
        body_form = QFormLayout(body_box)
        for label, combo, buttons in (
            ("Window (VCU UART intent)", self.window_combo, (self.window_open_button, self.window_close_button)),
            ("Light (Mock only)", self.light_combo, (self.light_on_button, self.light_off_button)),
        ):
            row = QHBoxLayout()
            row.addWidget(combo)
            for button in buttons:
                row.addWidget(button)
            body_form.addRow(label, row)
        body_form.addRow("Door lock request", self.door_combo)
        self._input_boxes = (driving_box, body_box)
        self._input_grid = QGridLayout()
        layout.addLayout(self._input_grid)
        self.set_compact_layout(True)
        self.torque_label = QLabel("TorqueRequest: VCU 계산 결과 관측 전용 · No Data\n"
                                  "실제 RX 값은 CAN Monitor / Signals, 명시 매핑한 Vehicle Status / Signal Graph에서 확인")
        self.torque_label.setWordWrap(True)
        layout.addWidget(self.torque_label)
        actions = QHBoxLayout()
        self.apply_button = role(QPushButton("Apply Mock Input"), "primary")
        self.reset_button = QPushButton("Reset Mock Inputs")
        self.live_tx_button = QPushButton("CAN TX Blocked")
        self.live_tx_button.setEnabled(False)
        self.uart_port_edit = QLineEdit()
        self.uart_port_edit.setPlaceholderText("/dev/cu.usbmodem…")
        self.uart_port_edit.setMaximumWidth(210)
        self.uart_port_edit.setAccessibleName("VCU ST-LINK virtual COM port")
        self.uart_button = QPushButton("Connect VCU UART")
        self.uart_button.setAccessibleName("Connect or disconnect VCU UART")
        self.uart_log_button = QPushButton("UART Connection Log")
        self.uart_log_button.setEnabled(False)
        self.uart_log_button.clicked.connect(self.show_uart_log)
        for button in (self.apply_button, self.reset_button):
            actions.addWidget(button)
        actions.addWidget(QLabel("UART port"))
        actions.addWidget(self.uart_port_edit)
        actions.addWidget(self.uart_button)
        actions.addWidget(self.uart_log_button)
        layout.addLayout(actions)
        self._uart_worker = None
        self._uart_error = ""
        self._uart_ack_text = ""
        self.state_label = QLabel()
        self.state_label.setWordWrap(True)
        self.accepted_label = QLabel()
        self.accepted_label.setWordWrap(True)
        self.ecu_label = QLabel(self.model.ecu_response_status + " · Mock Accepted는 ECU 응답이 아닙니다.")
        self.error_label = role(QLabel(), "error")
        self.error_label.setWordWrap(True)
        self.observation_label = QLabel()
        self.observation_label.setWordWrap(True)
        self.ecu_label.setWordWrap(True)
        self.uart_status_label = QLabel("UART: disconnected")
        self.uart_status_label.setWordWrap(True)
        result_box = QGroupBox("Request result / ECU response")
        result_layout = QVBoxLayout(result_box)
        for label in (self.observation_label, self.state_label, self.accepted_label, self.ecu_label,
                      self.error_label, self.uart_status_label):
            result_layout.addWidget(label)
        result_layout.addWidget(self.live_tx_button)
        layout.addWidget(result_box)
        self.history_table = QTableWidget(0, len(HISTORY_HEADERS))
        self.history_table.setHorizontalHeaderLabels(HISTORY_HEADERS)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.history_table.setWordWrap(True)
        self.history_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(QLabel(f"PC 내부 입력 이력 · 최대 {HISTORY_CAPACITY}건 · CAN Logger/ECU 수신 기록과 별도"))
        layout.addWidget(self.history_table, 1)
        self.history_detail_text = QPlainTextEdit()
        self.history_detail_text.setReadOnly(True)
        self.history_detail_text.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.history_detail_text.setMinimumHeight(120)
        self.history_detail_text.setMaximumHeight(180)
        self.history_detail_text.setPlaceholderText("행을 선택하면 전체 입력값과 처리 결과를 표시합니다. Mock 기록은 ECU 응답이 아닙니다.")
        self.history_detail_text.setAccessibleName("Selected driver input history details")
        layout.addWidget(self.history_detail_text)
        self.history_table.itemSelectionChanged.connect(self.update_history_detail)
        self._widgets = (self.accelerator_edit, self.accelerator_slider, self.ignition_combo, self.brake_combo,
                         self.gear_combo, self.window_combo, self.door_combo, self.light_combo,
                         self.window_open_button, self.window_close_button, self.light_on_button, self.light_off_button,
                         self.keyboard_toggle)
        self.accelerator_slider.valueChanged.connect(self.slider_changed)
        self.accelerator_edit.textChanged.connect(self.edit_inputs)
        for combo in (self.ignition_combo, self.brake_combo, self.gear_combo, self.window_combo,
                      self.door_combo, self.light_combo):
            combo.currentIndexChanged.connect(self.edit_inputs)
        self.window_open_button.clicked.connect(lambda: self.choose_body(self.window_combo, "OPEN"))
        self.window_close_button.clicked.connect(lambda: self.choose_body(self.window_combo, "CLOSE"))
        self.light_on_button.clicked.connect(lambda: self.choose_body(self.light_combo, "ON"))
        self.light_off_button.clicked.connect(lambda: self.choose_body(self.light_combo, "OFF"))
        self.apply_button.clicked.connect(self.apply_mock)
        self.reset_button.clicked.connect(self.reset_inputs)
        self.uart_button.clicked.connect(self.toggle_uart)
        self.keyboard_toggle.toggled.connect(self._keyboard_mode_changed)
        self._app = QApplication.instance()
        if self._app is not None:
            self._app.installEventFilter(self)
            self._app.applicationStateChanged.connect(self._application_state_changed)
        self._rendered_history = ()
        self.refresh()

    def configure_history_table_display(self):
        """페이지 공통 theme 이후 PC 입력 이력의 가독성 설정을 복구한다."""
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(HISTORY_INPUTS_COLUMN, QHeaderView.ResizeMode.Interactive)
        self.history_table.setWordWrap(True)
        self.history_table.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.history_table.verticalHeader().setDefaultSectionSize(HISTORY_ROW_HEIGHT)

    def set_compact_layout(self, compact):
        # 창 폭에 따라 입력 카드 배치만 바꾼다. 모델/선택/Signal은 유지한다.
        if getattr(self, "_compact_layout", None) == compact:
            return
        self._compact_layout = compact
        for box in self._input_boxes:
            self._input_grid.removeWidget(box)
        for index, box in enumerate(self._input_boxes):
            self._input_grid.addWidget(box, index if compact else 0, 0 if compact else index)

    @staticmethod
    def _choices(choices):
        # 첫 항목은 미설정이며 CAN Enum 값으로 인코딩하지 않는다.
        combo = QComboBox()
        combo.addItem("Not Configured", None)
        for choice in choices:
            combo.addItem(choice, choice)
        return combo

    def _input_editable(self):
        # 입력 화면/UART는 CAN Monitor 설정과 독립적이다.
        return not self.owner._closing and not self.model.closed and not self.owner.automation_active()

    def _can_edit(self):
        # Mock Adapter는 기존과 같이 CAN Monitor가 Mock일 때만 처리한다.
        return (self._input_editable()
                and self.owner.connection_view.mode_combo.currentText() == MOCK_MODE
                and self.model.mode == MOCK_MODE)

    def slider_changed(self, value):
        # Slider는 Mock % 표시 도우미이며 CAN Scale을 적용하지 않는다.
        if self._input_editable():
            self.accelerator_edit.setText(str(value))

    def choose_body(self, combo, value):
        # 버튼은 draft만 바꾸며 사용자의 Apply 전에는 Mock Adapter도 호출하지 않는다.
        if not self._input_editable():
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
        ignition = self.ignition_combo.currentData()
        return DriverInputs(accelerator=accelerator,
                            brake=None if brake is None else brake == "ON",
                            gear=self.gear_combo.currentData(),
                            window=self.window_combo.currentData(),
                            light=self.light_combo.currentData(),
                            ignition=ignition,
                            door=self.door_combo.currentData(),
                            steering_direction=self._steering_direction)

    def eventFilter(self, watched, event):
        # Arrow input is explicitly armed and active only on the Driver Control tab.
        if event.type() == QEvent.Type.ApplicationDeactivate:
            self._release_keyboard_keys()
            return False
        key_names = {
            Qt.Key.Key_Up: "up", Qt.Key.Key_Down: "down",
            Qt.Key.Key_Left: "left", Qt.Key.Key_Right: "right",
        }
        if event.type() not in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
            return super().eventFilter(watched, event)
        key = key_names.get(event.key())
        if key is None:
            return super().eventFilter(watched, event)
        pressed = event.type() == QEvent.Type.KeyPress
        if pressed and event.isAutoRepeat() and key in self._held_arrow_keys:
            event.accept()
            return True
        if pressed and key not in self._held_arrow_keys:
            if not self._keyboard_mode_active() or self._focused_control_uses_arrows():
                return super().eventFilter(watched, event)
            self._held_arrow_keys.add(key)
            self._apply_keyboard_state(key_pressed=key)
        elif not pressed and key in self._held_arrow_keys:
            self._held_arrow_keys.discard(key)
            self._apply_keyboard_state(key_released=key)
        else:
            return super().eventFilter(watched, event)
        event.accept()
        return True

    def _keyboard_mode_active(self):
        return (self.keyboard_toggle.isChecked() and self._input_editable() and
                self.owner.tabs.currentWidget() is self)

    def _focused_control_uses_arrows(self):
        focus = QApplication.focusWidget()
        return isinstance(focus, (QLineEdit, QComboBox, QSlider, QAbstractItemView,
                                  QPlainTextEdit, QAbstractSpinBox))

    def _keyboard_mode_changed(self, enabled):
        if enabled:
            self._steering_direction = "CENTER"
            self.keyboard_toggle.setText("Arrow-Key Controls Enabled")
            self.keyboard_status_label.setText(
                "ARMED · hold ↑ to ramp accelerator (+5%/100 ms), ↓ for brake, ←/→ for steering; release to return"
            )
            self.edit_inputs()
            self._refresh_steering_display()
            return
        self.keyboard_toggle.setText("Enable Arrow-Key Controls")
        self.keyboard_status_label.setText("Disabled · click to arm arrow keys")
        self._release_keyboard_keys()
        self._steering_direction = "CENTER" if self._steering_direction is not None else None
        self._refresh_steering_display()
        if self._uart_worker is not None:
            self.edit_inputs()

    def _application_state_changed(self, state):
        if state != Qt.ApplicationState.ApplicationActive:
            self._release_keyboard_keys()

    def _current_accelerator(self):
        try:
            return int(float(self.accelerator_edit.text().strip() or "0"))
        except ValueError:
            return 0

    def _set_keyboard_accelerator(self, value):
        value = max(int(ACCELERATOR_MIN), min(int(ACCELERATOR_MAX), int(value)))
        edit_blocker = QSignalBlocker(self.accelerator_edit)
        slider_blocker = QSignalBlocker(self.accelerator_slider)
        self.accelerator_edit.setText(str(value))
        self.accelerator_slider.setValue(value)
        del edit_blocker, slider_blocker
        self.edit_inputs()

    def _set_keyboard_brake(self, enabled):
        combo = self.brake_combo
        index = combo.findData("ON" if enabled else "OFF")
        if index >= 0 and combo.currentIndex() != index:
            combo.setCurrentIndex(index)
        else:
            self.edit_inputs()

    def _apply_keyboard_state(self, *, key_pressed=None, key_released=None):
        if key_pressed == "down":
            self._keyboard_timer.stop()
            self._set_keyboard_accelerator(0)
            self._set_keyboard_brake(True)
        elif key_pressed == "up":
            if "down" not in self._held_arrow_keys:
                self._set_keyboard_brake(False)
                self._set_keyboard_accelerator(max(5, self._current_accelerator() + 5))
                self._keyboard_timer.start()
        if key_released == "down":
            self._set_keyboard_brake(False)
        if key_released == "up" and "up" not in self._held_arrow_keys:
            self._keyboard_timer.stop()
            self._set_keyboard_accelerator(0)
        elif key_released == "down" and "up" in self._held_arrow_keys:
            self._set_keyboard_brake(False)
            self._keyboard_timer.start()
        self._update_steering_from_keys()
        self._refresh_arrow_indicators()

    def _keyboard_accelerator_tick(self):
        if "up" in self._held_arrow_keys and "down" not in self._held_arrow_keys:
            self._set_keyboard_accelerator(self._current_accelerator() + 5)

    def _update_steering_from_keys(self):
        left = "left" in self._held_arrow_keys
        right = "right" in self._held_arrow_keys
        direction = "LEFT" if left and not right else "RIGHT" if right and not left else "CENTER"
        self._steering_direction = direction if self.keyboard_toggle.isChecked() else None
        self.edit_inputs()
        self._refresh_steering_display()

    def _refresh_arrow_indicators(self):
        for key, indicator in self.arrow_indicators.items():
            pressed = key in self._held_arrow_keys
            if bool(indicator.property("pressed")) != pressed:
                indicator.setProperty("pressed", pressed)
                indicator.style().unpolish(indicator)
                indicator.style().polish(indicator)
                indicator.update()

    def _refresh_steering_display(self):
        direction = self._steering_direction or "CENTER"
        self.steering_status_label.setText(f"Steering: {direction} · UART VCU input")

    def _release_keyboard_keys(self):
        if not self._held_arrow_keys:
            self._keyboard_timer.stop()
            return
        driving_key_was_held = bool(self._held_arrow_keys & {"up", "down"})
        self._held_arrow_keys.clear()
        self._keyboard_timer.stop()
        if driving_key_was_held:
            self._set_keyboard_accelerator(0)
            self._set_keyboard_brake(False)
        if self.keyboard_toggle.isChecked():
            self._steering_direction = "CENTER"
        self._update_steering_from_keys()
        self._refresh_arrow_indicators()

    def _ensure_uart_log(self):
        if self._uart_log_dialog is None:
            self._uart_log_dialog = UartConnectionLogDialog(self.window())
            self.uart_log_button.setEnabled(True)
        return self._uart_log_dialog

    def _append_uart_log(self, message):
        if self._uart_log_dialog is not None:
            self._uart_log_dialog.append_event(message)

    def show_uart_log(self):
        if self._uart_log_dialog is not None:
            self._uart_log_dialog.show_log()

    def edit_inputs(self):
        # Mock 편집은 Mock Adapter에, UART 편집은 별도 worker의 반복 송신 snapshot에 반영한다.
        if not self._input_editable():
            return
        try:
            inputs = self._read_inputs().validated()
        except ValueError as exc:
            if self._can_edit():
                self.model.reject_input(str(exc))
            if self._uart_worker is not None:
                self._uart_worker.set_inputs(None)
                self._uart_error = str(exc)
                self.uart_status_label.setText("UART TX paused · VCU safe inputs return after 500 ms")
        else:
            self._uart_error = ""
            if self._can_edit():
                self.model.stage(inputs)
            if self._uart_worker is not None:
                try:
                    self._uart_worker.set_inputs(inputs)
                    self._uart_error = ""
                    if self.uart_status_label.text().endswith("VCU safe inputs return after 500 ms"):
                        self.uart_status_label.setText("UART: input valid · TX resumes every 100 ms")
                    self._append_uart_log(f"INPUT snapshot updated: {inputs}")
                except ValueError as exc:
                    self._uart_worker.set_inputs(None)
                    self._uart_error = str(exc)
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
        for combo in (self.ignition_combo, self.brake_combo, self.gear_combo, self.window_combo,
                      self.door_combo, self.light_combo):
            combo.setCurrentIndex(0)
        del blockers

    def reset_inputs(self):
        # Reset은 PC 메모리만 비우며 차량 정지 명령이 아니다.
        if self.owner._closing or self.model.closed:
            return
        self.model.reset()
        self._clear_widgets()
        if self._uart_worker is not None:
            self._uart_worker.set_inputs(None)
            self.uart_status_label.setText("UART TX paused · VCU safe inputs return after 500 ms")
        self.refresh()

    def set_input_source(self, source, *, is_mock):
        # Source 변경 때 이전 Mock 결과/미적용 draft를 격리한다.
        mode = MOCK_MODE if is_mock else LIVE_MODE
        changed = (mode, source) != (self.model.mode, self.model.source)
        self.model.set_source(mode, source)
        if changed:
            if self._uart_worker is not None:
                self._stop_uart()
            self._clear_widgets()
        self.refresh()

    def refresh(self):
        # 화면 갱신은 메인 스레드에서 수행하고, Automation/종료 중이면 UART heartbeat를 멈춘다.
        if (self.owner._closing or self.owner.automation_active()) and self._uart_worker is not None:
            self._uart_worker.request_stop()
        enabled = self._input_editable()
        for widget in self._widgets:
            widget.setEnabled(enabled)
        self.apply_button.setEnabled(self._can_edit())
        self.reset_button.setEnabled(not self.owner._closing and not self.model.closed)
        self.live_tx_button.setEnabled(False)
        connected = self._uart_worker is not None
        self.uart_button.setEnabled(enabled or connected)
        self.uart_button.setText("Disconnect UART" if connected else "Connect VCU UART")
        self.uart_port_edit.setEnabled(not connected and not self.owner._closing)
        self.ecu_label.setText(self._uart_ack_text or
                               (self.model.ecu_response_status + " · Mock Accepted는 ECU 응답이 아닙니다."))
        self.error_label.setText(self._uart_error or self.model.error or
                                 "CAN TX Blocked · UART 연결 전에는 실제 VCU 송신이 없습니다.")
        text = self.accelerator_edit.text().strip()
        self.accelerator_value_label.setText(f"{text} %" if text else "Not Configured")
        self.brake_combo.setAccessibleName("Brake Mock OFF or ON")
        self.gear_combo.setAccessibleName("Gear Mock choice")
        self.source_label.setText(f"Input Source: {self.model.source} · {self.model.mode}")
        self.state_label.setText(f"Request State: {self.model.state.value} · Applied to Mock: {self.model.applied}")
        self.observation_label.setText(
            f"ECU Applied: NOT VERIFIED · CAN RX: {self.owner.buffer.total_received} frames\n"
            f"UART TX: {'Connected' if connected else 'Disabled / not sent'} · CAN TX remains blocked")
        receipt = self.model.last_accepted
        self.accepted_label.setText(
            f"Last Mock Accepted: PC #{receipt.command.sequence} @ {receipt.command.timestamp:.6f} · {receipt.command.inputs}"
            if receipt else "Last Mock Accepted: No Data")
        sync_driver_presentation(self)
        history = self.model.history
        if history == self._rendered_history:
            return
        self._rendered_history = history
        self.history_table.setRowCount(len(history))
        for row, record in enumerate(history):
            cells = (format_pc_local_timestamp(record.timestamp),
                     record.source, record.action, input_summary(record.inputs),
                     record.state.value + (f" · {record.error}" if record.error else ""))
            for column, cell in enumerate(cells):
                item = QTableWidgetItem(cell)
                item.setToolTip(cell)
                self.history_table.setItem(row, column, item)
        if history:
            self.history_table.selectRow(len(history) - 1)
        else:
            self.update_history_detail()

    def update_history_detail(self):
        history = self.model.history
        row = self.history_table.currentRow()
        if row < 0 or row >= len(history):
            self.history_detail_text.setPlainText("행을 선택하면 전체 입력값과 PC 처리 결과를 표시합니다. Mock 기록은 ECU 응답이 아닙니다.")
            return
        record = history[row]
        self.history_detail_text.setPlainText(
            f"PC input history · Mock result is not an ECU response\n"
            f"Local time: {format_pc_local_timestamp(record.timestamp)} · Unix timestamp: {record.timestamp!r}\n"
            f"Source: {record.source} · Action: {record.action} · State: {record.state.value}\n"
            f"Inputs: {input_summary(record.inputs)}\nResult / Error: {record.error or 'None'}")

    def toggle_uart(self):
        # PC→VCU 입력을 100 ms마다 보내고 같은 포트의 ACK를 읽는다.
        if self._uart_worker is not None:
            self._append_uart_log("DISCONNECT requested by user")
            self._stop_uart()
            return
        if not self._input_editable():
            return
        port_name = self.uart_port_edit.text().strip()
        if not port_name:
            self._uart_error = "Select the ST-LINK virtual COM port (macOS: /dev/cu.usbmodem...)."
            self.refresh()
            return
        try:
            inputs = self._read_inputs().validated()
            from .uart_protocol import encode_driver_input
            encode_driver_input(0, inputs)
        except ValueError as exc:
            self._uart_error = str(exc)
            self.refresh()
            return
        self._uart_error = ""
        self._uart_ack_text = ""
        dialog = self._ensure_uart_log()
        dialog.append_event(f"CONNECT requested · {port_name} · protocol v2 · inputs={inputs}")
        dialog.show_log()
        self._uart_worker = VcuUartWorker(port_name, inputs, self)
        self._uart_worker.status.connect(self._uart_status)
        self._uart_worker.acknowledgement.connect(self._uart_ack)
        self._uart_worker.error.connect(self._uart_failed)
        self._uart_worker.log_event.connect(self._append_uart_log)
        self._uart_worker.finished.connect(self._uart_finished)
        self.uart_status_label.setText("UART: opening…")
        self._uart_worker.start()
        self.refresh()

    def _stop_uart(self, *, wait=False):
        worker = self._uart_worker
        if worker is None:
            return
        worker.request_stop()
        self.uart_status_label.setText("UART: stopping · VCU safe input timeout is 500 ms")
        if wait:
            worker.wait(1000)
        if not worker.isRunning():
            self._uart_worker = None
            self.uart_status_label.setText("UART: disconnected · VCU returns to safe inputs after 500 ms")
        self.refresh()

    def _uart_status(self, message):
        self.uart_status_label.setText("UART: " + message)

    def _uart_ack(self, sequence, status):
        from .uart_protocol import ACK_STATUS
        result = ACK_STATUS.get(status, f"unknown status {status}")
        self._uart_ack_text = (f"Last VCU UART ACK #{sequence}: {result} · "
                               "ACK confirms VCU packet validation only; Gateway action is unverified")
        self.refresh()

    def _uart_failed(self, message):
        self._uart_error = message
        self._append_uart_log(f"ERROR {message}")
        self.refresh()

    def _uart_finished(self):
        if self._uart_worker is not None and not self._uart_worker.isRunning():
            self._uart_worker = None
        if not self.owner._closing:
            self.uart_status_label.setText("UART: disconnected")
            self.refresh()

    def close_view(self):
        # 종료 전에 UART worker를 정리하고 VCU는 500 ms 입력 timeout으로 안전값에 복귀한다.
        self._stop_uart(wait=True)
        self.model.close()
        self.refresh()


def input_summary(inputs):
    if inputs is None:
        return "Not Configured"
    accelerator = f"{inputs.accelerator}%" if inputs.accelerator is not None else "Not Configured"
    brake = "Not Configured" if inputs.brake is None else ("ON" if inputs.brake else "OFF")
    return (f"Ignition={inputs.ignition or 'Not Configured'} · Accelerator={accelerator}\n"
            f"Brake={brake} · Gear={inputs.gear or 'Not Configured'} · Door={inputs.door or 'Not Configured'}\n"
            f"Window={inputs.window or 'Not Configured'} · Steering={inputs.steering_direction or 'Not Configured'} · "
            f"Light={inputs.light or 'Not Configured'}")


def format_pc_local_timestamp(timestamp):
    if timestamp is None:
        return "unknown"
    try:
        return datetime.fromtimestamp(timestamp).astimezone().isoformat(timespec="milliseconds")
    except (OverflowError, OSError, ValueError):
        return "unavailable"
