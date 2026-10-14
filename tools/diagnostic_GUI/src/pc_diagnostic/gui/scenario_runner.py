"""격리 Fake 세션을 기존 MainWindow 파이프라인으로 실행하는 유한 Qt Runner."""
from collections import deque
from dataclasses import replace
from itertools import islice
from pathlib import Path
import csv
import math
import tempfile
from time import monotonic, time
from PySide6.QtCore import QObject, QTimer, Qt, Signal
from ..frame import RawCanFrame
from ..logger import read_jsonl
from .automation import (MAX_RESULTS, MAX_SCENARIO_FRAMES, SECOND_CHANNEL, TEST_CHANNEL,
                         AssertionResult, RunResult, RunnerState, ScenarioInput,
                         catalog, evaluate, fixture_path, frame_value, signal_value,
                         validate_catalog, validate_fixture)

RUNNER_TICK_MS = 25  # PC 시험 event-loop 정책. CAN Period/Fault Timeout이 아니다.
RUN_LIMIT_SECONDS = 5.0
CLEANUP_LIMIT_SECONDS = 3.0


def select_channel(view, channel):
    # 기존 View의 typed Channel 목록과 명시적 선택 계약을 사용한다.
    view.observe_channel(channel)
    index = next(i for i in range(1, view.channel_combo.count())
                 if type(view.channel_combo.itemData(i)) is type(channel) and view.channel_combo.itemData(i)==channel)
    view.channel_combo.setCurrentIndex(index)


def select_message(view, name):
    # 기존 문자열/tuple Combo 계약을 구분하고 첫 후보/유사 이름을 쓰지 않는다.
    index = next(i for i in range(1,view.message_combo.count())
                 if (view.message_combo.itemData(i)[0] if isinstance(view.message_combo.itemData(i),tuple)
                     else view.message_combo.itemData(i)) == name)
    view.message_combo.setCurrentIndex(index)


def configure_views(session, channel):
    # 시험 표시 매핑은 TEST ONLY에 한정하며 각 기존 View의 Apply 경로를 통과한다.
    vehicle = session.vehicle_view
    vehicle.item_combo.setCurrentText("DBC Observation")
    select_channel(vehicle,channel)
    select_message(vehicle,"TestOnlySample")
    vehicle.signal_combo.setCurrentIndex(vehicle.signal_combo.findText("Measurement"))
    vehicle.confirm_box.setChecked(True)
    vehicle.apply_mapping()
    ecu = session.ecu_view
    ecu.target_combo.setCurrentText("Gateway")
    select_channel(ecu,channel)
    select_message(ecu,"TestOnlySample")
    ecu.confirm_box.setChecked(True)
    ecu.apply_mapping()
    fault = session.fault_monitor_view
    select_channel(fault,channel)
    select_message(fault,"TestOnlySample")
    fault.confirm_box.setChecked(True)
    fault.add_source()
    graph = session.graph_view
    select_channel(graph,channel)
    select_message(graph,"TestOnlySample")
    graph.signal_combo.setCurrentIndex(graph.signal_combo.findData("Measurement"))
    graph.apply_signal()


def capture_observations(session):
    # 주입 transport 입력 목록이 아닌 Raw table의 처리 결과만 수집한다.
    return tuple(session.table.item(row,0).data(Qt.ItemDataRole.UserRole)
                 for row in range(session.table.rowCount()))


def logging_records(path, fmt):
    # 기존 Raw file 계약만 읽는다. 무제한 읽기/새 Report schema를 도입하지 않는다.
    if fmt=="jsonl":
        return tuple(tuple(frame.to_record().items()) for frame in islice(read_jsonl(path),MAX_SCENARIO_FRAMES+1))
    result = []
    with Path(path).open(encoding="utf-8",newline="") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != tuple(RawCanFrame.__dataclass_fields__):
            raise ValueError("CSV header differs from existing RawCanLogger contract")
        for row in islice(reader,MAX_SCENARIO_FRAMES+1):
            # CSV에 정의된 scalar 표현을 변환할 뿐 Payload/Signal은 Decode하지 않는다.
            values = dict(row)
            for name in ("arbitration_id","dlc"):
                values[name] = int(values[name])
            for name in ("is_extended_id","is_remote_frame","is_error_frame","is_rx"):
                values[name] = {"True":True,"False":False}[values[name]]
            values["timestamp"] = None if not values["timestamp"] else float(values["timestamp"])
            result.append(tuple(RawCanFrame.from_record(values).to_record().items()))
    return tuple(result)


class ScenarioRunner(QObject):
    changed = Signal()
    close_ready = Signal()

    def __init__(self, owner, *, scenarios=None, run_limit=RUN_LIMIT_SECONDS,
                 cleanup_limit=CLEANUP_LIMIT_SECONDS):
        # 모든 상태/Widget 접근은 Qt main thread. Receiver/Writer만 기존 별도 thread를 사용한다.
        super().__init__(owner)
        self.owner = owner
        self.scenarios = tuple(catalog() if scenarios is None else scenarios)
        validate_catalog(self.scenarios)
        if any(type(value) not in (int,float) or not math.isfinite(value) or value<=0 for value in (run_limit,cleanup_limit)):
            raise ValueError("Runner limits must be positive PC test limits")
        self.run_limit, self.cleanup_limit = run_limit, cleanup_limit
        self.state = RunnerState.IDLE
        self.phase = "IDLE"
        self.result = None
        self.results = deque(maxlen=MAX_RESULTS)
        self.session = None
        self.streams = []
        self._stream_factory = ScenarioInput
        self._pending_state = None
        self._error = ""
        self._cancelled = self._close_requested = False
        self._temporary = None
        self._logging_path = None
        self._source_reset = None
        self._stage = 0
        self.timer = QTimer(self)
        self.timer.setInterval(RUNNER_TICK_MS)
        self.timer.timeout.connect(self.tick)

    @property
    def active(self):
        # cleanup 실패에도 session 참조를 유지하여 active QThread가 파괴되지 않게 한다.
        return self.session is not None or self.state==RunnerState.RUNNING

    def start(self, scenario_id, *, work_dir=None):
        # 사용자 Live source에서는 별도 Fake 주입도 차단하며 현재 수신/Logger를 중지하지 않는다.
        if self.active:
            return False
        self.result = None
        self._started = time()
        self._deadline = monotonic()+self.run_limit
        self._pending_state = None
        self._error = ""
        self._cancelled = self._close_requested = False
        self._temporary = self._logging_path = self._source_reset = None
        self.streams = []
        self._stage = 0
        self._parent_settings = self.owner.connection_view.raw_values()
        self._scenario = next((item for item in self.scenarios if item.scenario_id==scenario_id),None)
        try:
            if self._scenario is None:
                raise ValueError("NOT SUPPORTED: unknown fixed Scenario ID")
            if self.owner.connection_view.mode_combo.currentText()!="Mock" or self.owner._closing:
                raise ValueError("BLOCKED: select Mock user Source; actual Live automation/injection is prohibited")
            if self.owner._selecting_dbc:
                raise ValueError("BLOCKED: DBC selection is in progress")
            validate_fixture(fixture_path())
            self._dbc_path = None
            if self._scenario.requires_dbc:
                if not self.owner.decode_session.loader.is_loaded:
                    raise ValueError("No DBC: explicitly load tests/fixtures/test_only.dbc first")
                self._dbc_path = validate_fixture(self.owner.decode_session.loader.status.path)
            if self._scenario.kind in ("jsonl","csv"):
                if work_dir is None or not Path(work_dir).is_dir():
                    raise ValueError("Select an explicit writable test folder for temporary Raw Logging")
                self._work_dir = Path(work_dir).resolve()
                self._temporary = tempfile.TemporaryDirectory(prefix="hint48-mock-",dir=self._work_dir)
                self._logging_path = Path(self._temporary.name)/("capture."+self._scenario.kind)
            self.state, self.phase = RunnerState.RUNNING, "PREPARING"
            self.changed.emit()
            if self._cancelled:
                # PREPARING signal의 취소 재진입도 새 시험 subfolder를 먼저 반환한다.
                self.cleanup_files()
                self.finish(RunnerState.CANCELLED)
                return True
            self.create_session()
            self.timer.start()
        except Exception as exc:
            # 준비 오류도 실제 원인과 ERROR로 기록하고 부분 준비 자원을 정리한다.
            self._error = f"{type(exc).__name__}: {exc}"
            if self.session is None:
                try:
                    for stream in self.streams:
                        stream.shutdown()
                    self.cleanup_files()
                except Exception as cleanup_error:
                    self._error += f" | Preparation cleanup failed: {cleanup_error}"
                self.finish(RunnerState.ERROR)
            else:
                self.begin_cleanup(RunnerState.ERROR)
        return True

    def create_session(self):
        # 실제 transport factory를 호출하지 않는 별도 기존 MainWindow. 재귀 Automation tab은 제외한다.
        from .window import MainWindow
        stream = self._stream_factory(self._scenario.input_frames)
        if not isinstance(stream,ScenarioInput):
            raise TypeError("Automation requires the isolated ScenarioInput; no user backend execution")
        self.streams.append(stream)
        self.session = MainWindow(live_interface_factory=lambda settings:stream, automation_enabled=False)
        child = self.session
        child.setWindowTitle("Isolated Automation / TEST ONLY (not a hardware session)")
        child.connection_view.mode_combo.setCurrentText("Live")
        child.connection_view.backend_combo.setCurrentIndex(child.connection_view.backend_combo.findData("slcan"))
        child.connection_view.channel_edit.setText("AUTO_FAKE_TEST_ONLY_A")
        if self._dbc_path is not None:
            if not child.load_dbc(self._dbc_path):
                raise ValueError("Isolated explicit DBC load failed")
            configure_views(child,TEST_CHANNEL)
        self.phase = "OPENING"
        child.start_monitor()

    def tick(self):
        # bounded event-loop step이며 recv/file write/Thread wait를 GUI thread에서 수행하지 않는다.
        if not self.active:
            self.timer.stop()
            return
        try:
            child = self.session
            if self.phase=="CLEANING":
                self.cleanup_tick()
                return
            if monotonic()>=self._deadline:
                raise TimeoutError("PC Scenario execution limit exceeded; no ECU timeout inference")
            if child._failed or child._live_release_failed:
                raise RuntimeError(child.error_area.toPlainText() or "Isolated Receiver failed")
            snapshot = child.logging_session.snapshot()
            if snapshot.error:
                raise RuntimeError(snapshot.error)
            if self.phase=="OPENING" and child.receiver_running():
                if self._logging_path is not None:
                    child.logging_view.set_output_path(self._logging_path)
                    child.logging_view.format_combo.setCurrentIndex(
                        child.logging_view.format_combo.findData(self._scenario.kind))
                    child.logging_view.start_recording()
                    self.phase = "WRITER_OPENING"
                else:
                    self.streams[-1].release.set()
                    self.phase = "RECEIVING"
            elif self.phase=="WRITER_OPENING" and snapshot.opened:
                self.streams[-1].release.set()
                self.phase = "RECEIVING"
            elif self.phase=="RECEIVING":
                if child.worker is None:
                    raise RuntimeError("Receiver ended before Scenario completed")
                observations = capture_observations(child)
                if len(observations)>=len(self._scenario.input_frames) and child.buffer.pending_count==0:
                    child.stop_monitor()
                    self.phase = "STOPPING"
            elif self.phase=="STOPPING" and child.worker is None and not snapshot.active and child.buffer.pending_count==0:
                if self._scenario.kind=="source" and self._stage==0:
                    # 실제 Source editor UI unlock까지 기다린 뒤 hidden session만 전환한다.
                    if child.can_change_source() and child.connection_view.mode_combo.isEnabled():
                        self.switch_source()
                else:
                    self.begin_cleanup()
            self.changed.emit()
        except Exception as exc:
            # 실패 시 격리된 session만 stop/drain. 사용자 Receiver/Logger에는 접근하지 않는다.
            self._error = f"{type(exc).__name__}: {exc}"
            self.begin_cleanup(RunnerState.ERROR)

    def switch_source(self):
        # Source reset의 실제 GUI/model snapshot을 고정 expected tuple과 독립적으로 수집한다.
        child = self.session
        previous = child.decode_session.session_id
        child.connection_view.channel_edit.setText("AUTO_FAKE_TEST_ONLY_B")
        self._source_reset = (child.table.rowCount(), len(child.decode_session.service.cache.snapshot()),
                              len(child.graph_view.model.samples),len(child.fault_monitor_view.model.entries),
                              not child.vehicle_view.model.mappings and not child.ecu_view.model.mappings
                              and not child.fault_monitor_view.model.sources and child.graph_view.model.selection is None,
                              child.decode_session.session_id>previous)
        frames = tuple(replace(frame,channel=SECOND_CHANNEL) for frame in self._scenario.input_frames)
        stream = self._stream_factory(frames)
        if not isinstance(stream,ScenarioInput):
            raise TypeError("Isolated ScenarioInput required")
        self.streams.append(stream)
        child._live_interface_factory = lambda settings:stream
        configure_views(child,SECOND_CHANNEL)
        self._stage = 1
        child.start_monitor()
        self.phase = "OPENING"

    def cancel(self):
        # 취소도 observer 결과를 PASS로 바꾸지 않는다. 알려진 ERROR는 CANCELLED로 숨기지 않는다.
        if not self.active:
            return False
        self._cancelled = True
        if self.session is None:
            return True
        target = self._pending_state if self._pending_state==RunnerState.ERROR else RunnerState.CANCELLED
        self.begin_cleanup(target)
        return True

    def request_close(self):
        # 사용자 Close 요청은 비동기 cancel/cleanup 후 parent close 재시도로 이어진다.
        self._close_requested = True
        return self.cancel()

    def begin_cleanup(self, state=None):
        # Stop 요청은 즉시 admission을 닫으며 처리/파일 drain은 기존 계약으로 진행한다.
        self._pending_state = state or self._pending_state
        self.phase = "CLEANING"
        self._cleanup_deadline = monotonic()+self.cleanup_limit
        self.session.stop_monitor()
        self.timer.start()
        self.changed.emit()

    def cleanup_tick(self):
        # 정리 미완료는 참조를 유지하는 ERROR이며 무한 polling/강제 thread 종료를 하지 않는다.
        child = self.session
        snapshot = child.logging_session.snapshot()
        if child.worker is not None or snapshot.active:
            if monotonic()>=self._cleanup_deadline:
                self._error = "Resource cleanup timed out; isolated session retained. Cancel/Close to retry."
                self.record_cleanup_error()
            return
        if child.buffer.pending_count:
            if monotonic()>=self._cleanup_deadline:
                self._error = "Pending observation drain timed out; Cancel/Close to retry."
                self.record_cleanup_error()
                return
            child.refresh_frames()
            return
        try:
            if child._failed or child._live_release_failed or snapshot.error:
                self._pending_state = RunnerState.ERROR
                self._error = self._error or child.error_area.toPlainText() or snapshot.error or "Shutdown not confirmed"
            try:
                actual = self.collect_actual()
            except Exception as observation_error:
                # 쓰기/open 실패의 불완전한 파일도 ERROR로 남기고 자원 해제는 계속한다.
                actual = {}
                self._pending_state = RunnerState.ERROR
                self._error = self._error or f"Observation unavailable: {observation_error}"
            # 시작 전에 cancel한 Worker는 transport를 생성하지 않을 수 있어 미사용 Mock도 반환한다.
            for stream in self.streams:
                if not stream.closed.is_set():
                    stream.shutdown()
            closed = child.close()
            if not closed:
                # Receiver/Writer는 이미 종료. hidden error notice를 결과에 보존하고 bounded 재시도한다.
                self._pending_state = RunnerState.ERROR
                self._error = self._error or child.error_area.toPlainText() or "Isolated close failed"
                closed = child.close()
            if not closed:
                raise RuntimeError("Isolated close not accepted; resources retained")
            actual["application_tx"] = sum(stream.send_calls for stream in self.streams)
            actual["resources_released"] = (all(stream.closed.is_set() and stream.shutdown_calls==1 for stream in self.streams)
                                            and not child.timer.isActive() and not child.age_timer.isActive()
                                            and not child.graph_view.timer.isActive() and not child.logging_view.timer.isActive()
                                            and not child._live_release_failed
                                            and (self._logging_path is None or snapshot.closed))
            actual["parent_source_unchanged"] = self.owner.connection_view.raw_values()==self._parent_settings
            assertions = evaluate(self._scenario.assertions,actual)
            if self._pending_state is None:
                state = RunnerState.PASSED if all(item.passed for item in assertions) else RunnerState.FAILED
            else:
                state = self._pending_state
                if state==RunnerState.CANCELLED:
                    assertions = tuple(AssertionResult(item.key,item.expected,"NOT EVALUATED",None,"Cancelled before final assertions")
                                       for item in self._scenario.assertions)
            self.cleanup_files()
            self.session = None
            child.deleteLater()
            self.finish(state,assertions)
        except Exception as exc:
            # Cleanup 자체 오류는 기존 사용자 logging/source를 변경하지 않고 명시적으로 남긴다.
            self._error = f"Cleanup failed ({type(exc).__name__}): {exc}"
            self.record_cleanup_error()

    def record_cleanup_error(self):
        # 미해제 참조와 중간 ERROR 결과를 함께 보존한다. 종료 확인 전 PASS/최종 history 추가 없음.
        self.state = self._pending_state = RunnerState.ERROR
        self.timer.stop()
        checks = tuple(AssertionResult(item.key,item.expected,
                                       False if item.key=="resources_released" else "NOT EVALUATED",
                                       False if item.key=="resources_released" else None,self._error)
                       for item in self._scenario.assertions)
        self.result = RunResult(self._scenario.scenario_id,self._started,time(),RunnerState.ERROR,
                                checks,self._error,self._cancelled,cleanup_complete=False)
        self.changed.emit()

    def collect_actual(self):
        # 모든 feature actual은 격리된 기존 GUI 파이프라인에서만 읽는다.
        child = self.session
        observations = capture_observations(child)
        actual = {"raw_frames":tuple(frame_value(item.frame) for item in observations),
                  "decode_states":tuple(None if item.decoded is None else item.decoded.decode_status.value for item in observations),
                  "signals":tuple(signal_value(item.decoded.message_name,item.decoded.signals)
                                  for item in observations if item.decoded is not None),
                  "invalid_signals_empty":any(item.decoded is not None and item.decoded.decode_status.value=="invalid"
                                              and not item.decoded.signals for item in observations)}
        channel = SECOND_CHANNEL if self._stage else TEST_CHANNEL
        cached = child.decode_session.service.cache.get_message("TestOnlySample",channel=channel)
        if cached is not None:
            actual["cache"] = (cached.signals.get("Measurement"),cached.timestamp)
        vehicle = child.vehicle_view.table
        actual["vehicle"] = tuple(vehicle.item(5,column).text() for column in (3,4,7))
        ecu = child.ecu_view.model.observe("Gateway",child.decode_session,now=time())
        actual["ecu"] = (child.ecu_view.cards["Gateway"]["state"].text(),ecu.count)
        actual["fault"] = tuple((entry.sequence,entry.decode_state,entry.fault_status,entry.signals.get("Measurement"))
                                for entry in child.fault_monitor_view.model.entries)
        actual["graph"] = tuple((sample.value,sample.timestamp,sample.unit) for sample in child.graph_view.model.samples)
        if self._source_reset is not None:
            actual["source_reset"] = self._source_reset
        if self._logging_path is not None:
            snap = child.logging_session.snapshot()
            actual["logging_complete"] = (snap.closed,snap.received,snap.written,snap.queue_dropped,snap.unconfirmed)
            actual["logging_records"] = logging_records(self._logging_path,self._scenario.kind)
        return actual

    def cleanup_files(self):
        # 사용자 명시 폴더 아래 새 TemporaryDirectory만 제거한다. 기존 파일·일반 CAN log는 대상이 아니다.
        if self._temporary is not None:
            # 재귀 삭제 전에 새 시험 subfolder의 절대 경계와 이름을 검증한다.
            target = Path(self._temporary.name).resolve()
            if target.parent != self._work_dir or not target.name.startswith("hint48-mock-"):
                raise RuntimeError("Unsafe temporary cleanup boundary; folder retained")
            self._temporary.cleanup()
            self._temporary = None

    def finish(self, state, assertions=()):
        # 유한 결과만 메모리에 저장하고 새 Report/자동 파일 저장을 하지 않는다.
        self.timer.stop()
        self.state, self.phase = state, "FINISHED"
        identifier = "" if self._scenario is None else self._scenario.scenario_id
        if not assertions and self._scenario is not None:
            assertions = tuple(AssertionResult(item.key,item.expected,"NOT EVALUATED",None,self._error or state.value)
                               for item in self._scenario.assertions)
        self.result = RunResult(identifier,self._started,time(),state,tuple(assertions),self._error,self._cancelled)
        self.results.append(self.result)
        self.changed.emit()
        if self._close_requested and not self.active:
            self.close_ready.emit()

    def clear_results(self):
        # 실행/미해제 자원이 있으면 결과를 지워 오류를 숨기지 않는다.
        if self.active:
            return False
        self.results.clear()
        self.result = None
        self.state, self.phase = RunnerState.IDLE,"IDLE"
        self.changed.emit()
        return True
