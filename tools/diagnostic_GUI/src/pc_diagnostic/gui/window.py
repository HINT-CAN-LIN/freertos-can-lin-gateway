"""Raw 관찰/선택 결과/마지막 정상 Cache를 표시하는 thin Qt 화면."""
from pathlib import Path
from time import time
from PySide6.QtCore import QTimer, Qt, Slot
from PySide6.QtWidgets import (QAbstractItemView, QFileDialog, QHBoxLayout, QHeaderView,
                              QLabel, QMainWindow, QPlainTextEdit, QPushButton,
                              QSplitter, QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)
from ..dbc_loader import DbcLoadError
from ..interfaces import MockCanInterface
from .buffer import FrameBuffer
from .connection import LIVE_MODE, MOCK_MODE, MOCK_SOURCE_LABEL, open_live_interface
from .connection_view import ConnectionView
from .decode_session import DecodeSession
from .receiver import CLOSE_WAIT_MS, ReceiveWorker
from .vehicle_view import VehicleStatusView
from .observation_view import EcuObservationView
from .logging_session import LOG_CLOSE_SECONDS, LoggingSession
from .logging_view import LoggingView

# 아래 값은 GUI 표시 자원 제한이며 통신 규격 수치가 아니다.
DISPLAY_REFRESH_MS = 50
AGE_REFRESH_MS = 250
MAX_TABLE_ROWS = 500
MAX_ERROR_LINES = 50
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 850
WINDOW_SCREEN_MARGIN = 60
SIGNAL_HEADERS = ["Message", "Signal", "Value", "Unit", "Last Update / Age (s)", "Decode Status"]


def frame_cells(frame):
    # ID의 숫자를 보존하면서 실제 STD/EXT/ERROR/RTR 속성을 함께 표시한다.
    width = 8 if frame.is_extended_id or frame.is_error_frame else 3
    kind = "ERROR" if frame.is_error_frame else ("EXT" if frame.is_extended_id else "STD")
    if frame.is_remote_frame:
        kind += " RTR"
    timestamp = "unknown" if frame.timestamp is None else f"{frame.timestamp:.6f}"
    channel = "unknown" if frame.channel is None else str(frame.channel)
    return (timestamp, channel, f"0x{frame.arbitration_id:0{width}X} ({kind})",
            str(frame.dlc), frame.data.hex(" ").upper())


def observation_status(observation):
    # 미로드/처리 오류와 기존 Codec 상태를 서로 구분한다.
    if observation.processing_error:
        return observation.processing_error
    if observation.decoded is None:
        return "Decode disabled"
    result = observation.decoded
    status = "Unknown / Undefined" if result.decode_status.value == "unknown" else result.decode_status.value
    return status + (f": {result.error}" if result.error else "")


def configure_table(table, headers):
    # 공통 표시 설정만 담당하며 데이터 해석은 하지 않는다.
    table.setHorizontalHeaderLabels(headers)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setAlternatingRowColors(True)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    table.horizontalHeader().setStretchLastSection(True)


class MainWindow(QMainWindow):
    def __init__(self, interface_factory=MockCanInterface, *, clock=time, live_interface_factory=None):
        # Qt widget와 표시 타이머는 메인 스레드에서만 생성한다.
        super().__init__()
        self._interface_factory = interface_factory
        self._live_interface_factory = live_interface_factory or open_live_interface
        self._source_text = MOCK_SOURCE_LABEL
        self._live_release_failed = False
        self._receiver_error_notice = False
        self._clock = clock
        self.buffer = FrameBuffer()
        self.decode_session = DecodeSession()
        self.logging_session = LoggingSession()
        self.worker = None
        self._failed = False
        self._closing = False
        self._logging_error_notice = None
        self._selecting_dbc = False
        self._processed = 0
        self.setWindowTitle("PC Diagnostic Tool")
        # Windows 배율을 적용한 가용 화면 안에 초기 창을 배치한다.
        available = self.screen().availableGeometry()
        self.resize(min(WINDOW_WIDTH, available.width() - WINDOW_SCREEN_MARGIN),
                    min(WINDOW_HEIGHT, available.height() - WINDOW_SCREEN_MARGIN))
        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        self.banner = QLabel("Mock · DEMO / TEST ONLY — 실제 ECU 데이터가 아닙니다. Hardware NOT VERIFIED")
        self.banner.setWordWrap(True)
        layout.addWidget(self.banner)
        self.connection_view = ConnectionView(self)
        layout.addWidget(self.connection_view)
        dbc_controls = QHBoxLayout()
        self.dbc_button = QPushButton("Select DBC...")
        self.dbc_label = QLabel("DBC: not selected | Decode disabled")
        self.dbc_label.setWordWrap(True)
        dbc_controls.addWidget(self.dbc_button)
        dbc_controls.addWidget(self.dbc_label, 1)
        layout.addLayout(dbc_controls)
        self.dbc_policy_label = QLabel("DBC 변경: Stop 후 잔여 처리 완료 시 가능 · 로드 성공은 Interface 승인이 아닙니다.")
        self.dbc_policy_label.setWordWrap(True)
        layout.addWidget(self.dbc_policy_label)
        controls = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.clear_button = QPushButton("Clear")
        self.stop_button.setEnabled(False)
        for button in (self.start_button, self.stop_button, self.clear_button):
            controls.addWidget(button)
        self.status_label = QLabel("Disconnected")
        self.counter_label = QLabel("Received: 0")
        self.drop_label = QLabel("표시 버퍼 제외: 0")
        self.processed_label = QLabel("Raw/Decode processed: 0")
        for label in (self.status_label, self.counter_label, self.drop_label, self.processed_label):
            controls.addWidget(label)
        layout.addLayout(controls)
        self.table = QTableWidget(0, 5)
        configure_table(self.table, ["Timestamp", "Channel", "CAN ID", "DLC", "DATA"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.selection_label = QLabel("Raw 행을 선택하면 해당 프레임의 결과가 표시됩니다.")
        self.selection_label.setWordWrap(True)
        self.signal_table = QTableWidget(0, len(SIGNAL_HEADERS))
        configure_table(self.signal_table, SIGNAL_HEADERS)
        self.cache_label = QLabel("Last successful RX Cache: 선택 없음 · Age는 Health/Timeout 판정이 아닙니다.")
        self.cache_label.setWordWrap(True)
        self.cache_table = QTableWidget(0, len(SIGNAL_HEADERS))
        configure_table(self.cache_table, SIGNAL_HEADERS)
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.table)
        details = QWidget()
        detail_layout = QVBoxLayout(details)
        detail_layout.addWidget(self.selection_label)
        detail_layout.addWidget(QLabel("Selected frame signals — Last Update는 이 프레임 Timestamp; Age는 아래 Cache 참조"))
        detail_layout.addWidget(self.signal_table)
        detail_layout.addWidget(self.cache_label)
        detail_layout.addWidget(self.cache_table)
        splitter.addWidget(details)
        # 기존 Monitor/Signal 화면을 보존하고 독립 Vehicle 조회 탭만 추가한다.
        self.tabs = QTabWidget()
        self.tabs.addTab(splitter, "CAN Monitor / Signals")
        self.vehicle_view = VehicleStatusView(self.decode_session, lambda: self._clock(), self)
        self.tabs.addTab(self.vehicle_view, "Vehicle Status")
        self.ecu_view = EcuObservationView(self.decode_session, lambda: self._clock(), self)
        self.tabs.addTab(self.ecu_view, "ECU Health Observation")
        self.logging_view = LoggingView(self.logging_session, self.receiver_running, self)
        self.tabs.addTab(self.logging_view, "Logging")
        layout.addWidget(self.tabs, 1)
        layout.addWidget(QLabel("오류 메시지"))
        self.error_area = QPlainTextEdit()
        self.error_area.setReadOnly(True)
        self.error_area.document().setMaximumBlockCount(MAX_ERROR_LINES)
        self.error_area.setMaximumHeight(80)
        layout.addWidget(self.error_area)
        self.timer = QTimer(self)
        self.timer.setInterval(DISPLAY_REFRESH_MS)
        self.timer.timeout.connect(self.refresh_frames)
        self.age_timer = QTimer(self)
        self.age_timer.setInterval(AGE_REFRESH_MS)
        self.age_timer.timeout.connect(self.refresh_cache)
        self.age_timer.timeout.connect(self.vehicle_view.refresh)
        self.age_timer.timeout.connect(self.ecu_view.refresh)
        # Receiver 종료 뒤 비동기 writer drain 완료도 Source 잠금에 반영한다.
        self.age_timer.timeout.connect(self.update_controls)
        self.age_timer.start()
        self.start_button.clicked.connect(self.start_monitor)
        self.stop_button.clicked.connect(self.stop_monitor)
        self.clear_button.clicked.connect(self.clear_monitor)
        self.dbc_button.clicked.connect(self.select_dbc)
        self.table.itemSelectionChanged.connect(self.show_selection)
        self.connection_view.changed.connect(self.input_source_changed)

    def receiver_running(self):
        # Stop 요청/오류/종료 중에는 신규 Logging 시작을 허용하지 않는다.
        active = self.worker is not None and self.stop_button.isEnabled() and not self._failed and not self._closing
        # Mock admission 계약은 유지하되 Live 기록은 실제 open 완료 후만 허용한다.
        return active and (self.connection_view.mode_combo.currentText() == MOCK_MODE or self.worker.ready.is_set())

    def selected_source_text(self):
        # 주입된 시험 backend는 모든 주요 화면에서 TEST ONLY로 식별한다.
        text = self.connection_view.source_text()
        if self.connection_view.mode_combo.currentText() == LIVE_MODE and self._live_interface_factory is not open_live_interface:
            text += " | Injected backend / TEST ONLY"
        return text

    def dbc_source_text(self):
        # 기존 Mock 안내 문구를 유지하면서 Live에서는 실제 선택 출처를 표시한다.
        return "Mock / DEMO ONLY · TEST ONLY" if self.connection_view.mode_combo.currentText() == MOCK_MODE else self._source_text

    def can_change_source(self):
        # 잔여 표시 프레임과 파일 writer 해제까지 기다려 Source 혼합을 방지한다.
        return (not self._closing and not self._selecting_dbc and self.worker is None
                and self.buffer.pending_count == 0 and not self.logging_session.snapshot().active
                and not self._live_release_failed)

    @Slot()
    def input_source_changed(self):
        # 설정 변경은 새 Source 세션이다. 같은 Source의 Stop/Start/Clear 계약은 그대로 유지한다.
        if not self.can_change_source():
            return
        self._source_text = self.selected_source_text()
        self.decode_session.reset_observations()
        self.buffer.clear()
        self.clear_monitor()
        is_mock = self.connection_view.mode_combo.currentText() == MOCK_MODE
        self.vehicle_view.set_input_source(self._source_text, is_mock=is_mock)
        self.ecu_view.set_input_source(self._source_text, is_mock=is_mock)
        # refresh 전에 변경된 Source의 channel 선택 정책으로 selectors를 재구성한다.
        self.vehicle_view.reset_selectors()
        self.ecu_view.reset_selectors()
        self.logging_view.set_input_source(self._source_text)
        if self.decode_session.loader.is_loaded:
            status = self.decode_session.loader.status
            self.dbc_label.setText(f"DBC: {status.path.name} | Loaded ({status.message_count} messages) | Decode enabled · {self.dbc_source_text()}")
        self.banner.setText(f"Input: {self._source_text} | Hardware NOT VERIFIED | 설정 변경 시 과거 관측/매핑 초기화")
        self.connection_view.set_state("Disconnected")
        self.status_label.setText("Disconnected")
        self.update_controls()

    @Slot()
    def receiver_opened(self):
        # queued signal 도착 전에 Stop/실패했으면 Connected라고 표시하지 않는다.
        if self.receiver_running() and self.worker.ready.is_set():
            state = "Connected (application RX only)" if self.connection_view.mode_combo.currentText() == LIVE_MODE else "Mock running"
            self.connection_view.set_state(state)
            self.status_label.setText("Running")
            self.logging_view.refresh()

    def can_change_dbc(self):
        # 정지한 worker의 잔여 프레임까지 기존 DBC로 처리한 뒤 교체한다.
        return not self._closing and self.worker is None and self.buffer.pending_count == 0

    def update_controls(self):
        # 파일 선택 nested event loop 및 종료 중에는 신규 동작을 차단한다.
        self.dbc_button.setEnabled(self.can_change_dbc() and not self._selecting_dbc)
        self.start_button.setEnabled(not self._closing and not self._selecting_dbc and self.worker is None
                                     and not self._live_release_failed)
        self.connection_view.set_locked(not self.can_change_source())
        self.dbc_button.setToolTip("Stop 후 Worker와 잔여 버퍼 정리가 완료되어야 DBC를 변경할 수 있습니다.")

    @Slot()
    def select_dbc(self):
        # 사용자가 명시적으로 선택한 경로만 로드한다. 취소는 기존 세션을 유지한다.
        if not self.can_change_dbc() or self._selecting_dbc:
            if not self._closing:
                self.error_area.appendPlainText("DBC selection blocked: stop and finish pending frames first.")
            return
        self._selecting_dbc = True
        self.update_controls()
        try:
            path, _ = QFileDialog.getOpenFileName(self, "Select DBC — explicit input source", "", "DBC files (*.dbc);;All files (*)")
            if path and not self._closing:
                self.load_dbc(path)
        finally:
            self._selecting_dbc = False
            self.update_controls()

    def load_dbc(self, path):
        # 공개 통신 API 변경 없이 Loader 실패 상태를 UI에 표시하고 Raw 기능을 유지한다.
        if not self.can_change_dbc():
            if not self._closing:
                self.error_area.appendPlainText("DBC load blocked: stop and finish pending frames first.")
            return False
        try:
            self.decode_session.load(path)
        except DbcLoadError as exc:
            self.dbc_label.setText(f"DBC: {Path(path).name} | Load failed | Decode disabled")
            self.error_area.appendPlainText(str(exc))
            success = False
        else:
            status = self.decode_session.loader.status
            self.dbc_label.setText(f"DBC: {status.path.name} | Loaded ({status.message_count} messages) | Decode enabled · {self.dbc_source_text()}")
            success = True
        self.show_selection()
        self.vehicle_view.refresh()
        self.ecu_view.refresh()
        return success

    @Slot()
    def start_monitor(self):
        # 종료 signal 처리 전까지 worker 참조를 유지해 중복 실행을 차단한다.
        if self.worker is not None or self._closing or self._selecting_dbc or self._live_release_failed:
            return
        try:
            settings = self.connection_view.settings()
        except ValueError as exc:
            self.show_error(str(exc))
            return
        factory = self._interface_factory if settings.mode == MOCK_MODE else lambda: self._live_interface_factory(settings)
        self._failed = False
        self.error_area.clear()
        self.worker = ReceiveWorker(self.buffer, factory, self,
                                    frame_sink=self.logging_session.accept, mode=settings.mode)
        self.worker.opened.connect(self.receiver_opened)
        self.worker.failed.connect(self.show_error)
        self.worker.finished.connect(self.worker_finished)
        self.stop_button.setEnabled(True)
        self.update_controls()
        self.status_label.setText("Connecting" if settings.mode == LIVE_MODE else "Running")
        self.connection_view.set_state("Connecting")
        self.timer.start()
        self.worker.start()
        self.logging_view.refresh()

    @Slot()
    def stop_monitor(self):
        # 비동기 정지: UI 응답을 유지하면서 worker의 취소 이벤트만 설정한다.
        self.logging_session.stop()
        self.logging_view.refresh()
        if self.worker is not None:
            self.stop_button.setEnabled(False)
            self.worker.request_stop()
            if not self._failed:
                self.connection_view.set_state("Stopping")

    @Slot(str)
    def show_error(self, message):
        # Error는 worker 종료 후에도 유지하여 실패 원인을 확인할 수 있게 한다.
        self._failed = True
        self.logging_session.stop()
        self.logging_view.refresh()
        self.status_label.setText("Error")
        self.connection_view.set_state("Error")
        self.connection_view.show_error(message)
        self.error_area.appendPlainText(message)

    @Slot()
    def worker_finished(self):
        # 수신 잔여 데이터는 제한된 batch로 처리하고 종료된 thread를 해제한다.
        self.logging_session.stop()
        self.logging_view.refresh()
        if self._closing:
            return
        self.refresh_frames()
        self.stop_button.setEnabled(False)
        if not self._failed:
            self.status_label.setText("Stopped")
            self.connection_view.set_state("Stopped")
        completed = self.worker
        if completed is not None and not completed.wait(CLOSE_WAIT_MS):
            # finished 이후에도 native thread 정리를 확인하지 못하면 참조를 유지한다.
            self.show_error("Worker cleanup timed out; close again after it finishes.")
            self.update_controls()
            return
        if completed is not None and completed.release_failed and self.connection_view.mode_combo.currentText() == LIVE_MODE:
            # Live shutdown 실패는 재연결/Source 변경을 막고 미해제 상태를 명확히 표시한다.
            self._live_release_failed = True
            self.show_error("Live transport shutdown not confirmed; close the application and check the device.")
        self.worker = None
        if completed is not None:
            completed.deleteLater()
        self.update_controls()
        # 정지 후 남은 버퍼도 timer로 비우되 새 수신은 발생하지 않는다.

    @Slot()
    def refresh_frames(self):
        # 한 번에 제한된 행만 해석한다. 제외된 프레임은 Cache 갱신 근거로 쓰지 않는다.
        if self._closing:
            return
        frames, total, dropped = self.buffer.drain()
        for frame in frames:
            self.vehicle_view.observe_channel(frame.channel)
            observation = self.decode_session.process(frame)
            self.ecu_view.record(observation)
            if observation.processing_error:
                self.error_area.appendPlainText(observation.processing_error)
            if self.table.rowCount() >= MAX_TABLE_ROWS:
                self.table.removeRow(0)
            row = self.table.rowCount()
            self.table.insertRow(row)
            for column, value in enumerate(frame_cells(frame)):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, observation)
                self.table.setItem(row, column, item)
            self._processed += 1
        self.counter_label.setText(f"Received: {total}")
        self.drop_label.setText(f"표시 버퍼 제외: {dropped}")
        self.processed_label.setText(f"Raw/Decode processed: {self._processed}")
        self.refresh_cache()
        self.vehicle_view.refresh()
        self.ecu_view.update_coverage(received=total, buffer_dropped=dropped,
                                      pending=self.buffer.pending_count, processed=self._processed)
        self.ecu_view.refresh()
        self.update_controls()
        if self.worker is None and not frames:
            self.timer.stop()

    def selected_observation(self):
        # 행에 보관한 immutable 결과를 사용하여 후속 수신과 프레임 연관성을 보존한다.
        row = self.table.currentRow()
        item = self.table.item(row, 0) if row >= 0 else None
        return None if item is None else item.data(Qt.ItemDataRole.UserRole)

    @Slot()
    def show_selection(self):
        # 선택 프레임의 결과와 실시간 Cache를 별도 화면으로 표시한다.
        observation = self.selected_observation()
        self.signal_table.setRowCount(0)
        if observation is None:
            self.selection_label.setText("Raw 행을 선택하면 해당 프레임의 결과가 표시됩니다.")
        else:
            frame = observation.frame
            result = observation.decoded
            name = observation.message_name or ("Unknown / Undefined" if result and result.decode_status.value == "unknown" else "Not decoded / unresolved")
            stamp, channel, can_id, dlc, payload = frame_cells(frame)
            self.selection_label.setText(
                f"Input: {self._source_text}\nSelected frame: Timestamp={stamp} | Channel={channel} | CAN ID={can_id} | DLC={dlc} | DATA={payload}\n"
                f"DBC session={observation.session_id} | Message={name} | {observation_status(observation)}"
            )
            if result is not None:
                self.fill_signal_table(self.signal_table, result, observation.units, stamp, result.decode_status.value)
        self.refresh_cache()

    def fill_signal_table(self, table, message, units, update_age, status):
        # 값은 기존 Decode 결과 그대로, Unit은 해당 DBC의 메타데이터만 표시한다.
        table.setRowCount(0)
        for signal, value in message.signals.items():
            row = table.rowCount()
            table.insertRow(row)
            values = (message.message_name, signal, str(value), units.get(signal) or "", update_age, status)
            for column, text in enumerate(values):
                table.setItem(row, column, QTableWidgetItem(text))

    @Slot()
    def refresh_cache(self):
        # 수신 정지 후에도 Age만 갱신한다. 값/시각은 마지막 정상 RX snapshot에서 읽는다.
        if self._closing:
            return
        observation = self.selected_observation()
        self.cache_table.setRowCount(0)
        if observation is None:
            self.cache_label.setText("Last successful RX Cache: 선택 없음 · Age는 Health/Timeout 판정이 아닙니다.")
            return
        cached = self.decode_session.cached_message(observation)
        if cached is None:
            reason = "historical DBC session" if observation.session_id != self.decode_session.session_id else "no successful RX"
            self.cache_label.setText(f"Last successful RX Cache: {reason}")
            return
        latest = self.decode_session.latest_attempt(observation)
        status = "latest attempt unavailable"
        if latest is not None:
            status = "processing error" if latest.processing_error else latest.decoded.decode_status.value
            status += " RX" if latest.frame.is_rx else " TX (cache unchanged)"
        cause = None if latest is None else (latest.processing_error or latest.decoded.error)
        error = "" if cause is None else f" | Latest error: {cause}"
        channel = "unknown" if cached.raw_frame.channel is None else str(cached.raw_frame.channel)
        self.cache_label.setText(f"Input: {self._source_text}\nLast successful RX Cache: Channel={channel} | Message={cached.message_name} | Latest processed attempt={status}{error}")
        definition = self.decode_session.loader.get_message_by_name(cached.message_name)
        units = {signal.name: signal.unit for signal in definition.signals}
        age = self.decode_session.cache_age(observation, self._clock())
        stamp = "unknown" if cached.timestamp is None else f"{cached.timestamp:.6f}"
        age_text = "unknown" if age is None else f"{age:.3f}"
        self.fill_signal_table(self.cache_table, cached, units, f"{stamp} / {age_text}", f"cached decoded RX; latest {status}")

    @Slot()
    def clear_monitor(self):
        # 기존 Clear는 화면/표시 계수만 초기화한다. 정상 Cache는 DBC 교체 전까지 유지한다.
        if self._closing:
            return
        self.buffer.clear()
        self.table.setRowCount(0)
        self._processed = 0
        self.counter_label.setText("Received: 0")
        self.drop_label.setText("표시 버퍼 제외: 0")
        self.processed_label.setText("Raw/Decode processed: 0")
        self.show_selection()
        self.vehicle_view.refresh()
        self.ecu_view.clear_observations()
        self.update_controls()

    def closeEvent(self, event):
        # Qt 필수 override 명칭은 snake_case 규칙의 예외이다.
        # 제한 시간 안에 종료되지 않으면 창을 유지하여 실행 중 QThread 파괴를 방지한다.
        self._closing = True
        self.logging_session.stop()
        self.logging_view.refresh()
        self.update_controls()
        if self.worker is not None:
            self.worker.request_stop()
            if not self.worker.wait(CLOSE_WAIT_MS):
                self._closing = False
                self.show_error("Worker stop timed out; close again after it finishes.")
                self.update_controls()
                event.ignore()
                return
        if (self.worker is not None and self.worker.release_failed
                and self.connection_view.mode_combo.currentText() == LIVE_MODE and not self._receiver_error_notice):
            # Close 대기 중 발생한 shutdown 오류도 첫 Close에서 사용자에게 보인다.
            self._receiver_error_notice = True
            self._live_release_failed = True
            self._closing = False
            self.show_error("Live transport shutdown not confirmed; inspect the device and close again to exit.")
            self.update_controls()
            event.ignore()
            return
        if not self.logging_session.wait(LOG_CLOSE_SECONDS):
            # 파일 I/O를 강제 종료하지 않고 창과 writer 참조를 유지한다.
            self._closing = False
            self.show_error("Logging stop timed out; close again after the writer finishes.")
            self.update_controls()
            event.ignore()
            return
        snapshot = self.logging_session.snapshot()
        notice = (id(self.logging_session), snapshot.generation, snapshot.error)
        if snapshot.error and self._logging_error_notice != notice:
            # Thread 종료와 기록 성공은 다르다. 오류를 표시한 뒤 재차 Close를 허용한다.
            self._logging_error_notice = notice
            self._closing = False
            self.show_error(f"Logging ended with error: {snapshot.error}. Review the partial file; close again to exit.")
            self.update_controls()
            event.ignore()
            return
        completed = self.worker
        self.worker = None
        if completed is not None:
            completed.deleteLater()
        self.timer.stop()
        self.age_timer.stop()
        self.vehicle_view.close_view()
        self.ecu_view.close_view()
        self.logging_view.close_view()
        event.accept()
