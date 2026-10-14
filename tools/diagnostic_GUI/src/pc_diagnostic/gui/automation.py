"""고정 TEST ONLY 시나리오/결과 계약. 실제 CAN 송신·Fault 상태 판정 없음."""
from dataclasses import dataclass, replace
from enum import Enum
from hashlib import sha256
from pathlib import Path
from threading import Event
from ..frame import RawCanFrame
from ..interfaces import CanInterface, CanInterfaceError, MockCanInterface
from .demo import TEST_ONLY_ID, TEST_ONLY_PAYLOADS

TEST_CHANNEL = "AUTOMATION / TEST ONLY"
SECOND_CHANNEL = "AUTOMATION SECOND / TEST ONLY"
TEST_DBC_SHA256 = "9ff1750df33163d0b9591912f202be56dda2a61af9dd97fa398f5a2c2c13a93b"
MAX_SCENARIO_FRAMES = 8
MAX_ASSERTIONS = 16
MAX_RESULTS = 10
SCENARIO_KINDS = frozenset(("raw", "decode", "decode-error", "cache", "vehicle", "ecu",
                          "fault", "graph", "jsonl", "csv", "source"))


class RunnerState(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    ERROR = "ERROR"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class AssertionSpec:
    key: str
    expected: object


@dataclass(frozen=True, slots=True)
class AssertionResult:
    key: str
    expected: object
    actual: object
    passed: bool | None
    reason: str = ""


@dataclass(frozen=True, slots=True)
class Scenario:
    scenario_id: str
    name: str
    description: str
    kind: str
    requires_dbc: bool
    input_frames: tuple[RawCanFrame, ...]
    assertions: tuple[AssertionSpec, ...]
    input_source: str = "Isolated Fake Live / MockCanInterface FIFO / TEST ONLY"


@dataclass(frozen=True, slots=True)
class RunResult:
    scenario_id: str
    started_at: float
    ended_at: float
    state: RunnerState
    assertions: tuple[AssertionResult, ...]
    error: str = ""
    cancelled: bool = False
    hardware: str = "NOT VERIFIED"
    cleanup_complete: bool = True


def frame_value(frame):
    # 기대 Raw와 실제 Raw 모두 같은 표현으로 비교하되 실제값은 GUI 관측에서만 가져온다.
    return (frame.arbitration_id, frame.is_extended_id, type(frame.channel).__name__, frame.channel,
            frame.dlc, frame.data.hex().upper(), frame.timestamp, frame.is_rx,
            frame.is_remote_frame, frame.is_error_frame)


def signal_value(name, signals):
    # Signal 기대값은 고정 fixture 예제에서 선언하며 Decode 결과로 기대값을 계산하지 않는다.
    return name, tuple(sorted(signals.items()))


def fixture_path():
    # 현재 Repository MVP의 내부 시험 자료다. 설치본에 없으면 준비 실패로 보고한다.
    return Path(__file__).resolve().parents[3] / "tests/fixtures/test_only.dbc"


def validate_fixture(path):
    # 동일 Scenario ID의 golden 계약을 고정하고 Production/변경된 DBC를 대신 사용하지 않는다.
    path = Path(path)
    if sha256(path.read_bytes()).hexdigest() != TEST_DBC_SHA256:
        raise ValueError("Unsupported DBC: explicitly load the unchanged tests/fixtures/test_only.dbc")
    return path


def catalog():
    # ID/STD·EXT/payload는 기존 demo와 test_only.dbc 예제만 사용한다.
    first = RawCanFrame(TEST_ONLY_ID, TEST_ONLY_PAYLOADS[0], timestamp=10.0, channel=TEST_CHANNEL)
    second = replace(first, timestamp=11.0)
    extended = RawCanFrame(TEST_ONLY_ID, TEST_ONLY_PAYLOADS[1], is_extended_id=True,
                           timestamp=11.0, channel=TEST_CHANNEL)
    malformed = replace(second, data=first.data[:1], dlc=1)
    rows = (
        ("raw", "Raw CAN RX", "기존 Raw table의 STD/EXT/Channel/Payload 관측", (first, extended), ()),
        ("decode", "DBC Decode success", "기존 fixture의 -10/test_unit 및 515 관측", (first, extended),
         (AssertionSpec("decode_states", ("decoded", "decoded")),
          AssertionSpec("signals", (signal_value("TestOnlySample", {"Measurement":-10.0,"Mode":1,"Counter":7}),
                                   signal_value("TestOnlyExtended", {"Reading":515}))))),
        ("decode-error", "DBC Decode failure", "길이 오류 Raw 보존; 실패에 정상값을 붙이지 않음", (first, malformed),
         (AssertionSpec("decode_states", ("decoded", "invalid")),
          AssertionSpec("invalid_signals_empty", True))),
        ("cache", "Signal Cache update", "반복 정상 RX의 최신 timestamp/값 저장", (first, second),
         (AssertionSpec("cache", (-10.0, 11.0)),)),
        ("vehicle", "Vehicle DBC Observation", "차량 측정이 아닌 TEST ONLY 표시 항목", (first, second),
         (AssertionSpec("vehicle", ("-10.0", "test_unit", "Valid")),)),
        ("ecu", "ECU Observation label", "Gateway 카드의 TEST ONLY 관측; 실제 ECU Health 아님", (first, second),
         (AssertionSpec("ecu", ("State: Observed", 2)),)),
        ("fault", "Fault History infrastructure", "TEST ONLY source의 반복 이력; 실제 Fault 상태 Unknown", (first, second),
         (AssertionSpec("fault", ((1, "Observed", "Status Unknown", -10.0),
                                 (2, "Observed", "Status Unknown", -10.0))),)),
        ("graph", "Signal Graph sample", "기존 Decode 결과의 두 점/값/시각 보존", (first, second),
         (AssertionSpec("graph", ((-10.0,10.0,"test_unit"),(-10.0,11.0,"test_unit"))),)),
        ("jsonl", "JSONL Raw Logging", "선택 시험 폴더의 임시 Raw capture/동일 입력 기록", (first, extended),
         (AssertionSpec("logging_complete", (True,2,2,0,0)),)),
        ("csv", "CSV Raw Logging", "기존 CSV schema/동일 입력 기록", (first, extended),
         (AssertionSpec("logging_complete", (True,2,2,0,0)),)),
        ("source", "Isolated Source transition", "별도 시험 창의 Source 변경 때 관측/매핑 초기화", (first, second),
         (AssertionSpec("source_reset", (0,0,0,0,True,True)),
          AssertionSpec("cache", (-10.0,11.0)))),
    )
    result = []
    for kind, name, description, frames, extra in rows:
        final_frames = tuple(replace(frame, channel=SECOND_CHANNEL) for frame in frames) if kind=="source" else frames
        checks = (AssertionSpec("raw_frames", tuple(frame_value(frame) for frame in final_frames)), *extra,
                  AssertionSpec("application_tx",0), AssertionSpec("resources_released",True),
                  AssertionSpec("parent_source_unchanged",True))
        if kind in ("jsonl","csv"):
            checks += (AssertionSpec("logging_records", tuple(tuple(frame.to_record().items()) for frame in frames)),)
        result.append(Scenario(f"HINT48-MOCK-{kind.upper()}-v1", name, description, kind, kind!="raw", frames, checks))
    validate_catalog(result)
    return tuple(result)


def validate_catalog(scenarios):
    # 중복 ID와 무한 입력/결과 및 코드 정의 밖 kind를 시작 전에 거부한다.
    ids = [scenario.scenario_id for scenario in scenarios]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate Scenario ID")
    for scenario in scenarios:
        if (not isinstance(scenario, Scenario) or scenario.kind not in SCENARIO_KINDS
                or not 0 < len(scenario.input_frames) <= MAX_SCENARIO_FRAMES
                or not 0 < len(scenario.assertions) <= MAX_ASSERTIONS
                or len({item.key for item in scenario.assertions}) != len(scenario.assertions)):
            raise ValueError("Invalid or unbounded Scenario contract")


def evaluate(assertions, actual):
    # 실제 관측 누락도 FAIL이다. 성공 주입/기대값 자체를 실제값으로 대신 사용하지 않는다.
    return tuple(AssertionResult(item.key, item.expected, actual.get(item.key, "NOT OBSERVED"),
                                 item.key in actual and actual[item.key] == item.expected,
                                 "" if item.key in actual and actual[item.key] == item.expected else
                                 "Observation missing" if item.key not in actual else "Expected and actual differ")
                 for item in assertions)


class ScenarioInput(CanInterface):
    def __init__(self, frames):
        # 기존 FIFO Mock transport를 조합한 Fake Live; 실제 Bus 객체를 만들지 않는다.
        if not 0 < len(frames) <= MAX_SCENARIO_FRAMES:
            raise ValueError("Scenario input must be finite and nonempty")
        self.mock = MockCanInterface(frames)
        self.release = Event()
        self.closed = Event()
        self.send_calls = self.shutdown_calls = 0

    def recv(self, timeout=None):
        # Logger가 실제 open되기 전 입력을 보류한다. Worker의 기존 finite poll 계약을 따른다.
        if not self.release.wait(timeout):
            return None
        if self.closed.is_set():
            return None
        return self.mock.recv(timeout)

    def send(self, frame, timeout=None):
        # 시험 입력은 FIFO RX로만 전달한다. API 오용도 TX0 assertion에서 검출한다.
        self.send_calls += 1
        raise CanInterfaceError("ScenarioInput is RX TEST ONLY; send is prohibited")

    def shutdown(self):
        # Worker 미시작 취소도 자원을 반환하며 반복 호출은 안전하게 처리한다.
        if not self.closed.is_set():
            self.shutdown_calls += 1
            self.closed.set()
            self.release.set()
            self.mock.shutdown()
