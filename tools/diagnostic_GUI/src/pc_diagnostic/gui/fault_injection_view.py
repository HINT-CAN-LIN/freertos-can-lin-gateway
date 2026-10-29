"""기존 Fault 관측 옆의 TEST ONLY 실행 패널. 공통 Runner/기존 catalog만 사용한다."""
import json
from PySide6.QtCore import QSignalBlocker
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QGridLayout, QLabel, QPlainTextEdit,
                              QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)
from .fault_injection import FaultInjectionModel, SCENARIO_SCOPE
from .automation import RunnerState
from .theme import role

PREVIEW_HEIGHT = 140
TABLE_HEIGHT = 160
TABLE_HEADER_PADDING = 32
ASSERTION_HEADERS = ("Assertion", "Expected", "Actual observation", "Result", "Reason")
OBSERVATION_HEADERS = ("Order", "Message", "Decode", "Fault state", "Actual signals / units", "Source")


def readonly_table(headers, parent):
    # 유한 결과 표시만 담당하며 내용을 수정하거나 ECU 상태를 판정하지 않는다.
    table = QTableWidget(0, len(headers), parent)
    table.setHorizontalHeaderLabels(headers)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setAlternatingRowColors(True)
    table.setMinimumHeight(TABLE_HEIGHT)
    table.setMaximumHeight(TABLE_HEIGHT)
    table.horizontalHeader().setStretchLastSection(True)
    # 실제 스타일이 적용된 Header 글꼴 폭으로 제목을 보존하고 표 가로 스크롤을 유지한다.
    for index, title in enumerate(headers):
        width = table.horizontalHeader().fontMetrics().horizontalAdvance(title) + TABLE_HEADER_PADDING
        table.setColumnWidth(index, max(table.columnWidth(index), width))
        table.horizontalHeaderItem(index).setToolTip(title)
    return table


class FaultInjectionView(QWidget):
    def __init__(self, owner, parent=None):
        # 기존 Runner 한 개를 공유한다. hidden Automation 없는 창에는 생성하지 않는다.
        super().__init__(parent)
        self.owner = owner
        self.model = FaultInjectionModel(owner, owner.automation_view.runner)
        self._closed = False
        self._history_token = ()
        self._render_token = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.policy_label = role(QLabel(
            "TEST ONLY · No physical CAN open / TX · Hardware NOT VERIFIED\n"
            "Fault_Status/ECU Fault 발생·Recovery 시험은 Open. 기존 TEST ONLY 관측 기반 Assertions만 실행."), "warning")
        self.policy_label.setWordWrap(True)
        layout.addWidget(self.policy_label)
        controls = QGridLayout()
        self.scenario_combo = QComboBox()
        self.scenario_combo.setMinimumContentsLength(8)
        self.scenario_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        for scenario in self.model.scenarios:
            self.scenario_combo.addItem(scenario.name, scenario.scenario_id)
        self.scenario_combo.setCurrentIndex(self.scenario_combo.findData(self.model.selected_id))
        self.scenario_combo.setAccessibleName("Existing Fault TEST ONLY scenario")
        self.run_button = QPushButton("Run Fault TEST ONLY")
        self.cancel_button = QPushButton("Cancel / Retry cleanup")
        self.reset_button = QPushButton("Reset test results")
        for button in (self.run_button, self.cancel_button, self.reset_button):
            button.setAccessibleName(button.text())
        controls.addWidget(self.scenario_combo, 0, 0, 1, 3)
        controls.addWidget(self.run_button, 1, 0)
        controls.addWidget(self.cancel_button, 1, 1)
        controls.addWidget(self.reset_button, 1, 2)
        layout.addLayout(controls)
        self.state_label, self.error_label = QLabel(), QLabel()
        for label in (self.state_label, self.error_label):
            label.setWordWrap(True)
            layout.addWidget(label)
        self.description = QPlainTextEdit()
        self.description.setReadOnly(True)
        self.description.setMaximumHeight(PREVIEW_HEIGHT)
        layout.addWidget(self.description)
        layout.addWidget(QLabel("Test assertions — PASS is Mock software only"))
        self.assertion_table = readonly_table(ASSERTION_HEADERS, self)
        layout.addWidget(self.assertion_table)
        self.history_combo = QComboBox()
        self.history_combo.setMinimumContentsLength(8)
        self.history_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.history_combo.setAccessibleName("Fault TEST run history, not ECU events")
        layout.addWidget(QLabel("Test run history — separate from user Fault History / ECU state"))
        layout.addWidget(self.history_combo)
        self.observation_table = readonly_table(OBSERVATION_HEADERS, self)
        self.observation_table.setAccessibleName("Isolated TEST ONLY Fault History observations")
        layout.addWidget(self.observation_table)
        self.scenario_combo.currentIndexChanged.connect(self.describe_scenario)
        self.run_button.clicked.connect(self.run_test)
        self.cancel_button.clicked.connect(self.cancel_test)
        self.reset_button.clicked.connect(self.reset_tests)
        self.history_combo.currentIndexChanged.connect(self.render_result)
        self.model.runner.changed.connect(self.refresh)
        self.owner.connection_view.mode_combo.currentTextChanged.connect(self.refresh)
        self.describe_scenario()

    def describe_scenario(self, *_):
        # 같은 Scenario 객체/입력/기대값을 참조하며 새 ID/Counter/Fault 데이터를 만들지 않는다.
        self.model.select(self.scenario_combo.currentData())
        scenario = next((s for s in self.model.scenarios if s.scenario_id == self.model.selected_id), None)
        if scenario is None:
            self.description.setPlainText("NOT SUPPORTED")
        else:
            target, scope = SCENARIO_SCOPE[scenario.kind]
            lines = [scenario.scenario_id, f"Target: {target}", scope,
                     "Input: " + scenario.input_source,
                     "DBC: explicit unchanged tests/fixtures/test_only.dbc; no redistribution approval",
                     "PASS: all existing assertions and resource release; FAIL: actual differs/missing",
                     "ERROR: invalid input/DBC/receiver/cleanup; CANCELLED: assertions not evaluated",
                     "BLOCKED: user Live Source, closing, busy Runner, missing/mismatched DBC",
                     "FaultCode/ECUOffline/RecoveryState/SystemState are absent from this TEST ONLY fixture.",
                     "Event / Replay / Resync Open; Status Unknown preserved.",
                     "TEST ONLY input frames:"]
            lines.extend(repr(frame.to_record()) for frame in scenario.input_frames)
            lines.append("Existing expected assertions:")
            lines.extend(f"{a.key}: {a.expected!r}" for a in scenario.assertions)
            self.description.setPlainText("\n".join(lines))
        self.refresh()

    def run_test(self):
        # Slot 직접 호출에도 Model과 기존 Runner의 Source/입력 guard가 적용된다.
        if self._closed:
            return
        if self.model.select(self.scenario_combo.currentData()):
            self.model.run()
        self.refresh()

    def cancel_test(self):
        # 이 패널이 소유한 시험만 취소한다. 사용자 Receiver/Logger는 유지한다.
        self.model.cancel()
        self.refresh()

    def reset_tests(self):
        # 실행 중 Reset을 거부하고 사용자 Fault History에는 Clear를 호출하지 않는다.
        self.model.reset()
        self.refresh()

    def refresh(self, *_):
        # 기존 changed/UI tick에서 동기화한다. 새 Timer는 없다.
        if self._closed:
            return
        self.model.observe()
        runner = self.model.runner
        allowed = self.owner.connection_view.mode_combo.currentText() == "Mock"
        self.run_button.setEnabled(allowed and not runner.active and not self.owner._closing and not self.owner._selecting_dbc)
        self.cancel_button.setEnabled(self.model.active)
        self.reset_button.setEnabled(not runner.active)
        self.scenario_combo.setEnabled(not runner.active)
        self.history_combo.setEnabled(not runner.active)
        busy = " | Shared Automation busy" if runner.active and not self.model.active else ""
        self.state_label.setText(f"Fault TEST: {self.model.state.value} | "
                                f"{'Isolated Mock/Fake only' if allowed else 'Live Source BLOCKED'}{busy} | "
                                f"Retained test runs: {len(self.model.history)}/{self.model.history.maxlen}")
        result = self.model.result
        errors = [self.model.error]
        if result is not None and result.error not in errors:
            errors.append(result.error)
        self.error_label.setText(" / ".join(e for e in errors if e) or "No test error recorded")
        token = tuple(id(record.result) for record in self.model.history)
        if token != self._history_token:
            self._history_token = token
            blocker = QSignalBlocker(self.history_combo)
            self.history_combo.clear()
            for record in self.model.history:
                r = record.result
                self.history_combo.addItem(f"{r.scenario_id} · {r.state.value} · {r.ended_at:.6f}", record)
            self.history_combo.setCurrentIndex(self.history_combo.count() - 1)
            del blocker
        self.render_result()

    def render_result(self, *_):
        # 기존 FaultHistoryEntry만 표시하고 Test Result와 ECU Event를 구분한다.
        selected = self.history_combo.currentData() if not self.model.active else None
        if self.model.state is RunnerState.ERROR and self.model.result is None:
            selected = None  # 준비 오류를 이전 실행 PASS로 대신 표시하지 않는다.
        result = self.model.result if selected is None else selected.result
        observations = self.model.observations if selected is None else selected.observations
        token = id(result), tuple(id(e) for e in observations), self.model.active
        if token == self._render_token:
            return
        self._render_token = token
        checks = () if result is None else result.assertions
        self.assertion_table.setRowCount(len(checks))
        for row, check in enumerate(checks):
            outcome = "NOT EVALUATED" if check.passed is None else "PASS" if check.passed else "FAIL"
            values = (check.key, repr(check.expected), repr(check.actual), outcome, check.reason)
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value));item.setToolTip(str(value))
                self.assertion_table.setItem(row, column, item)
        self.observation_table.setRowCount(len(observations))
        for row, entry in enumerate(observations):
            fields = json.dumps({"signals": dict(entry.signals), "units": dict(entry.units)}, ensure_ascii=False)
            for column, value in enumerate((entry.sequence, entry.message_name, entry.decode_state,
                                            entry.fault_status, fields, entry.source)):
                item = QTableWidgetItem(str(value));item.setToolTip(str(value))
                self.observation_table.setItem(row, column, item)

    def close_view(self):
        # 공유 Runner의 기존 비동기 종료 완료 뒤에만 View를 닫는다.
        if self.model.active:
            raise RuntimeError("Isolated Fault test cleanup is still active")
        self._closed = True
