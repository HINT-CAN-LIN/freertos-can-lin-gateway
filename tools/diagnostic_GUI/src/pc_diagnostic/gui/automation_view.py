"""고정 Mock 시험 Catalog/결과 화면. 사용자 Live 세션에 주입하지 않는다."""
from pathlib import Path
from PySide6.QtCore import Slot
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QFileDialog, QGridLayout,
                              QLabel, QLineEdit, QPlainTextEdit, QPushButton,
                              QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)
from .scenario_runner import ScenarioRunner

RESULT_HEADERS = ("Assertion", "Expected", "Actual observation", "Result", "Reason")


class AutomationView(QWidget):
    def __init__(self, owner, parent=None):
        # Runner/화면은 main thread. 별도 hidden MainWindow 파이프라인을 격리 실행한다.
        super().__init__(parent)
        self.owner = owner
        self.runner = ScenarioRunner(owner)
        self._closed = False
        self._selecting_folder = False
        self._rendered_result = object()
        self.scenario_combo = QComboBox()
        for scenario in self.runner.scenarios:
            self.scenario_combo.addItem(scenario.name,scenario.scenario_id)
        self.description = QPlainTextEdit()
        self.description.setReadOnly(True)
        self.description.setMaximumBlockCount(80)
        self.description.setMaximumHeight(150)
        self.run_button = QPushButton("Run isolated TEST ONLY")
        self.cancel_button = QPushButton("Cancel / Retry cleanup")
        self.clear_button = QPushButton("Clear results")
        self.folder_edit = QLineEdit()
        self.folder_edit.setReadOnly(True)
        self.folder_edit.setPlaceholderText("Logging scenarios only: explicitly select writable test folder")
        self.folder_button = QPushButton("Select test folder...")
        self.state_label = QLabel()
        self.state_label.setWordWrap(True)
        self.time_label = QLabel()
        self.error_label = QLabel()
        self.error_label.setWordWrap(True)
        policy = QLabel("Mock/Fake TEST ONLY software assertions. 실제 CAN/HIL/ECU PASS 아님. "
                        "사용자 Live Source에서는 실행 차단. 사용자 Receiver/Logger 자동 중지·전환 없음. "
                        "Logging 시험 임시 Raw capture는 선택 폴더 아래 새 subfolder에 생성 후 정리; 결과 Report 파일 저장 없음.")
        policy.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.addWidget(policy)
        controls = QGridLayout()
        controls.addWidget(self.scenario_combo,0,0,1,3)
        controls.addWidget(self.run_button,1,0)
        controls.addWidget(self.cancel_button,1,1)
        controls.addWidget(self.clear_button,1,2)
        controls.addWidget(self.folder_edit,2,0,1,2)
        controls.addWidget(self.folder_button,2,2)
        layout.addLayout(controls)
        for widget in (self.description,self.state_label,self.time_label,self.error_label):
            layout.addWidget(widget)
        self.table = QTableWidget(0,len(RESULT_HEADERS))
        self.table.setHorizontalHeaderLabels(RESULT_HEADERS)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table,1)
        self.scenario_combo.currentIndexChanged.connect(self.describe_scenario)
        self.run_button.clicked.connect(self.run_scenario)
        self.cancel_button.clicked.connect(self.runner.cancel)
        self.clear_button.clicked.connect(self.runner.clear_results)
        self.folder_button.clicked.connect(self.select_folder)
        self.runner.changed.connect(self.refresh)
        self.runner.changed.connect(owner.update_controls)
        self.runner.close_ready.connect(owner.close)
        self.describe_scenario()

    @Slot()
    def describe_scenario(self, *_):
        # 고정 Catalog만 선택하며 외부 스크립트/예상값 파일을 실행하지 않는다.
        scenario = next(item for item in self.runner.scenarios if item.scenario_id==self.scenario_combo.currentData())
        lines = [scenario.scenario_id,scenario.description,
                 f"Input: {scenario.input_source}",
                 "DBC: explicitly load unchanged tests/fixtures/test_only.dbc" if scenario.requires_dbc else
                 "DBC: raw-only; unchanged internal TEST ONLY definitions required",
                 "Inputs (test timestamps, not ECU period):"]
        lines.extend(f"0x{frame.arbitration_id:X} {'EXT' if frame.is_extended_id else 'STD'} | {frame.channel} | "
                     f"DLC={frame.dlc} | {frame.data.hex(' ').upper()} | Timestamp={frame.timestamp}"
                     for frame in scenario.input_frames)
        lines.append("Expected assertions (independent of observed output):")
        lines.extend(f"{item.key}: {item.expected!r}" for item in scenario.assertions)
        self.description.setPlainText("\n".join(lines))
        self.refresh()

    @Slot()
    def select_folder(self):
        # 사용자가 명시적으로 선택한 시험 폴더만 쓰며 dialog nested loop 중 Run을 막는다.
        if self.runner.active or self._closed:
            return
        self._selecting_folder = True
        self.refresh()
        try:
            path = QFileDialog.getExistingDirectory(self,"Select writable TEST ONLY Raw logging workspace")
            if path and not self._closed:
                self.folder_edit.setText(path)
        finally:
            self._selecting_folder = False
            self.refresh()

    @Slot()
    def run_scenario(self):
        # 잠긴 버튼의 직접 호출에도 Runner 자체의 Live/중복/DBC guard가 적용된다.
        if not self._closed and not self._selecting_folder:
            folder = self.folder_edit.text().strip()
            self.runner.start(self.scenario_combo.currentData(),work_dir=Path(folder) if folder else None)

    @Slot()
    def refresh(self):
        # 결과는 유한 메모리 snapshot이며 미실행 assertion을 PASS로 표시하지 않는다.
        if self._closed:
            return
        runner = self.runner
        allowed = self.owner.connection_view.mode_combo.currentText()=="Mock"
        self.run_button.setEnabled(allowed and not runner.active and not self._selecting_folder and not self.owner._closing)
        self.run_button.setToolTip("Actual Live Source blocks all automation. Existing Mock Receiver/Logger can continue independently.")
        self.cancel_button.setEnabled(runner.active)
        self.clear_button.setEnabled(not runner.active)
        self.folder_button.setEnabled(not runner.active)
        self.scenario_combo.setEnabled(not runner.active)
        self.state_label.setText(f"Runner: {runner.state.value} | Phase: {runner.phase} | "
                                 f"{'Live Source BLOCKED' if not allowed else 'Isolated TEST ONLY'} | "
                                 f"Results retained: {len(runner.results)}/{runner.results.maxlen}")
        result = runner.result
        self.time_label.setText("Not run" if result is None and not runner.active else
                                f"Start: {runner._started:.6f} | End: {'pending' if result is None else f'{result.ended_at:.6f}'}")
        self.error_label.setText((runner._error or "none") if runner.active else
                                 ("No errors recorded" if result is None else result.error or "No errors recorded"))
        if self._rendered_result is result:
            return
        self._rendered_result = result
        checks = () if result is None else result.assertions
        self.table.setRowCount(len(checks))
        for row, check in enumerate(checks):
            state = "NOT EVALUATED" if check.passed is None else "PASS" if check.passed else "FAIL"
            for column, value in enumerate((check.key,repr(check.expected),repr(check.actual),state,check.reason)):
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))
                self.table.setItem(row,column,item)

    def close_view(self):
        # Parent는 active session을 먼저 비동기 정리한 뒤에만 화면을 닫는다.
        if self.runner.active:
            raise RuntimeError("Automation session is still active")
        self._closed = True
        self.runner.timer.stop()
