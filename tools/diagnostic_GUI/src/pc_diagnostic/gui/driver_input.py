"""PC 내부 Mock 운전자 입력 계약. CAN Signal/Frame/전송 계약이 아니다."""
from collections import deque
from dataclasses import dataclass
from enum import Enum
from math import isfinite
from time import time

# 핸드북 9.1/임시안 신호_제안의 입력 모델 예시이며 Production encoding이 아니다.
ACCELERATOR_MIN = 0.0
ACCELERATOR_MAX = 100.0
GEAR_CHOICES = ("P", "N", "D", "R")
IGNITION_CHOICES = ("OFF", "ON", "RUN")  # 내부 문자열이며 CAN Enum Encoding은 TBD다.
WINDOW_CHOICES = ("OPEN", "CLOSE")
LIGHT_CHOICES = ("ON", "OFF")
HISTORY_CAPACITY = 128  # PC 메모리 표시 상한; CAN 주기/Timeout과 무관하다.
MOCK_MODE = "Mock"
LIVE_MODE = "Live"
APPROVAL_STATUS = "Awaiting Interface Approval"
ECU_RESPONSE_STATUS = "ECU Response Not Verified"


class InputState(str, Enum):
    NOT_CONFIGURED = "Not Configured"
    MOCK_INPUT = "Mock Input"
    MOCK_ACCEPTED = "Mock Accepted"
    LIVE_BLOCKED = "Live TX Blocked"
    INPUT_ERROR = "Input Error"


@dataclass(frozen=True)
class DriverInputs:
    accelerator: float | None = None
    brake: bool | None = None
    gear: str | None = None
    window: str | None = None
    light: str | None = None
    ignition: str | None = None  # 기존 위치 인자를 보존하기 위해 마지막에 추가한다.

    def validated(self):
        # 미선택과 OFF/0을 구분하고, 범위 밖 값을 조용히 보정하지 않는다.
        value = self.accelerator
        if value is not None and (type(value) not in (int, float)
                                  or not ACCELERATOR_MIN <= value <= ACCELERATOR_MAX
                                  or not isfinite(value)):
            raise ValueError("Accelerator must be a finite number in Mock range 0..100%.")
        if self.brake is not None and type(self.brake) is not bool:
            raise ValueError("Brake must be an explicit Mock ON/OFF value.")
        for name, choices in (("gear", GEAR_CHOICES), ("window", WINDOW_CHOICES), ("light", LIGHT_CHOICES),
                              ("ignition", IGNITION_CHOICES)):
            value = getattr(self, name)
            if value is not None and (type(value) is not str or value not in choices):
                raise ValueError(f"Unsupported Mock {name} choice.")
        if all(getattr(self, name) is None for name in self.__dataclass_fields__):
            raise ValueError("Select at least one Mock input.")
        return self


@dataclass(frozen=True)
class DriverCommand:
    sequence: int  # PC 이력용 번호; CAN AliveCounter가 아니다.
    timestamp: float
    inputs: DriverInputs
    source: str


@dataclass(frozen=True)
class MockReceipt:
    command: DriverCommand
    accepted: bool = True


@dataclass(frozen=True)
class InputRecord:
    sequence: int
    timestamp: float | None
    source: str
    action: str
    inputs: DriverInputs | None
    state: InputState
    error: str


class DriverInputModel:
    def __init__(self, *, adapter_factory=None, clock=time):
        # Qt/통신 의존성이 없는 Application Logic만 구성한다.
        if adapter_factory is None:
            from .driver_adapter import MockDriverAdapter
            adapter_factory = MockDriverAdapter
        self._adapter_factory = adapter_factory
        self._clock = clock
        self._adapter = None
        self._history = deque(maxlen=HISTORY_CAPACITY)
        self._sequence = 0
        self._busy = False
        self.closed = False
        self.mode = MOCK_MODE
        self.source = "Mock / DEMO / TEST ONLY"
        self.draft = None
        self.last_accepted = None
        self.state = InputState.NOT_CONFIGURED
        self.error = ""

    @property
    def history(self):
        # 변경 가능한 컨테이너 대신 불변 이력 스냅샷을 제공한다.
        return tuple(self._history)

    @property
    def approval_status(self):
        # 이번 코드에는 승인 또는 Live 송신 활성화 경로가 없다.
        return APPROVAL_STATUS

    @property
    def ecu_response_status(self):
        # Mock 수락은 ECU 처리/수신 증거가 아니다.
        return ECU_RESPONSE_STATUS

    @property
    def applied(self):
        # 현재 편집/실패를 과거 Mock 수락과 혼동하지 않는다.
        return self.state == InputState.MOCK_ACCEPTED

    def _record(self, action, inputs):
        # 생성 시각 조회 실패도 Input Error로 기록하고 재시도하지 않는다.
        self._sequence += 1
        try:
            timestamp = self._clock()
            if type(timestamp) not in (int, float) or not isfinite(timestamp):
                raise ValueError("Invalid PC clock")
        except Exception:
            timestamp = None
            self.state = InputState.INPUT_ERROR
            self.error = "PC input timestamp unavailable."
        record = InputRecord(self._sequence, timestamp, self.source, action, inputs, self.state, self.error)
        self._history.append(record)
        return record

    def _blocked(self):
        # 버튼 비활성화와 별개로 Live/종료 상태의 직접 호출도 차단한다.
        if self.mode != MOCK_MODE or self.closed:
            self.draft = None
            self.last_accepted = None
            self.state = InputState.LIVE_BLOCKED if not self.closed else InputState.NOT_CONFIGURED
            self.error = "Live TX Blocked: interface approval absent." if not self.closed else "Driver panel closed."
            return True
        return False

    def stage(self, inputs):
        # 편집은 Mock Input만 생성한다. Adapter나 기존 Sender는 호출하지 않는다.
        if self._blocked() or self._busy:
            return False
        self.error = ""
        try:
            if not isinstance(inputs, DriverInputs):
                raise ValueError("DriverInputs required.")
            self.draft = inputs.validated()
            self.state = InputState.MOCK_INPUT
        except ValueError as exc:
            self.draft = None
            self.state = InputState.INPUT_ERROR
            self.error = str(exc)
        self._record("edit", self.draft)
        return self.state == InputState.MOCK_INPUT

    def reject_input(self, message):
        # GUI 숫자 변환 실패도 기록하며 이전 draft를 다시 적용하지 않는다.
        if self._blocked() or self._busy:
            return
        self.draft = None
        self.state = InputState.INPUT_ERROR
        self.error = message
        self._record("edit rejected", None)

    def apply_mock(self):
        # 동기 메모리 처리만 실행한다. 중복/재진입 호출을 큐에 쌓지 않는다.
        if self._blocked() or self._busy:
            return None
        if self.draft is None:
            self.reject_input("Configure valid Mock inputs before Apply.")
            return None
        self.state = InputState.MOCK_INPUT
        self.error = ""
        record = self._record("request", self.draft)
        if record.timestamp is None:
            return None
        command = DriverCommand(record.sequence, record.timestamp, self.draft, self.source)
        self._busy = True
        try:
            from .driver_adapter import MockDriverAdapter
            if self._adapter is None:
                adapter = self._adapter_factory()
                if not isinstance(adapter, MockDriverAdapter):
                    raise TypeError("Only an in-process Mock adapter is supported.")
                self._adapter = adapter
            receipt = self._adapter.accept(command)
            if not isinstance(receipt, MockReceipt) or receipt.command != command or receipt.accepted is not True:
                raise ValueError("Mock receipt mismatch/rejection")
            self.last_accepted = receipt
            self.state = InputState.MOCK_ACCEPTED
            self.error = ""
            self._history.append(InputRecord(record.sequence, record.timestamp, self.source,
                                             "Mock result", command.inputs, self.state, ""))
            return receipt
        except Exception as exc:
            # 예외 종류로 원인을 알리고 인증정보/내부 경로는 표시하지 않는다.
            self.state = InputState.INPUT_ERROR
            self.error = f"Mock adapter failed ({type(exc).__name__}); ECU response not verified."
            self._history.append(InputRecord(record.sequence, record.timestamp, self.source,
                                             "Mock failure", command.inputs, self.state, self.error))
            return None
        finally:
            self._busy = False

    def reset(self):
        # Mock 상태만 폐기하며 차량 정지/물리 제어 명령을 생성하지 않는다.
        if self._busy:
            return False
        self.draft = None
        self.last_accepted = None
        self._history.clear()
        self.state = InputState.LIVE_BLOCKED if self.mode != MOCK_MODE else InputState.NOT_CONFIGURED
        self.error = ""
        if self._adapter is not None:
            adapter, self._adapter = self._adapter, None
            try:
                adapter.shutdown()
            except Exception as exc:
                self.state = InputState.INPUT_ERROR
                self.error = f"Mock cleanup failed ({type(exc).__name__})."
        return not self.error

    def set_source(self, mode, source):
        # Source 변경 시 미처리 입력과 Mock 결과를 폐기하고 Live 관측에 쓰지 않는다.
        if mode not in (MOCK_MODE, LIVE_MODE) or not isinstance(source, str) or not source:
            raise ValueError("Explicit Mock/Live source required.")
        if self._busy or self.closed:
            return False
        if (mode, source) != (self.mode, self.source):
            self.mode, self.source = mode, source
            self.reset()
        return True

    def close(self):
        # Adapter는 스레드/버스/파일을 소유하지 않으며 종료 후 재적용을 차단한다.
        self.closed = True
        return self.reset()
