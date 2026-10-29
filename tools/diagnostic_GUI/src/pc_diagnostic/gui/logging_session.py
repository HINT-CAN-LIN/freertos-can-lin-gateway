"""Qt 독립 기록 Session. 기존 RawCanLogger의 schema/독점 생성/flush 계약을 재사용한다."""
from collections import deque
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from threading import Condition, Thread
from ..logger import RawCanLogger

# PC 자원/종료 설정이며 CAN 주기 또는 Fault Timeout이 아니다.
LOG_QUEUE_CAPACITY = 512
LOG_CLOSE_SECONDS = 1.0


class LoggingState(str, Enum):
    IDLE = "Idle"
    RECORDING = "Recording"
    STOPPING = "Stopping"
    STOPPED = "Stopped"
    ERROR = "Error"


@dataclass(frozen=True, slots=True)
class LoggingSnapshot:
    state: LoggingState
    path: str | None
    format: str
    received: int
    written: int
    queue_dropped: int
    unconfirmed: int
    pending: int
    in_flight: int
    active: bool
    opened: bool
    closed: bool
    error: str | None
    generation: int


class LoggingSession:
    def __init__(self, *, capacity=LOG_QUEUE_CAPACITY, logger_factory=RawCanLogger):
        # 상태/queue/counter는 하나의 Condition으로 보호한다.
        if type(capacity) is not int or capacity <= 0:
            raise ValueError("logging capacity must be a positive integer")
        self.capacity = capacity
        self._logger_factory = logger_factory
        self._condition = Condition()
        self._thread = None
        self._queue = deque()
        self._state = LoggingState.IDLE
        self._generation = 0
        self._path = None
        self._format = "jsonl"
        self._received = self._written = self._queue_dropped = self._unconfirmed = 0
        self._in_flight = 0
        self._opened = self._closed = False
        self._error = None

    def snapshot(self):
        # GUI가 일관된 immutable 계수를 읽으며 파일 I/O를 수행하지 않는다.
        with self._condition:
            active = self._thread is not None and self._thread.is_alive()
            return LoggingSnapshot(self._state, self._path, self._format,
                                   self._received, self._written, self._queue_dropped,
                                   self._unconfirmed, len(self._queue), self._in_flight,
                                   active, self._opened, self._closed, self._error, self._generation)

    def start(self, path, *, format="jsonl"):
        # 생성/쓰기/close는 worker가 소유한다. 첫 수신 전에 중복 Start를 차단한다.
        with self._condition:
            if self._thread is not None and self._thread.is_alive():
                return False
            self._generation += 1
            self._queue.clear()
            self._received = self._written = self._queue_dropped = self._unconfirmed = 0
            self._in_flight = 0
            self._opened = self._closed = False
            self._error = None
            self._path = None
            if not isinstance(path, (str, Path)) or not str(path).strip() or format not in ("csv", "jsonl"):
                self._state = LoggingState.ERROR
                self._error = "Select an explicit file path and CSV/JSONL format."
                return False
            self._path, self._format = str(path), format
            # opening 중 수신도 queue로 받되 성공 기록 count는 write/flush 완료 뒤만 증가한다.
            self._state = LoggingState.RECORDING
            self._thread = Thread(target=self._run, name="pc-can-log-writer", daemon=False)
            try:
                self._thread.start()
            except Exception as exc:
                # thread 시작 실패에는 파일/프레임이 아직 없다. 재시도 루프를 만들지 않는다.
                self._state = LoggingState.ERROR
                self._error = f"Writer start failed ({type(exc).__name__}): {exc}"
                return False
            return True

    def accept(self, frame):
        # Receiver thread에서 유한 queue에만 넣는다. 느린 파일 I/O는 이 lock 밖이다.
        with self._condition:
            if self._state is not LoggingState.RECORDING:
                return False
            self._received += 1
            if len(self._queue) >= self.capacity:
                # 기존 FIFO를 보존하고 새 프레임만 제외하며 GUI에 불완전 기록 수를 노출한다.
                self._queue_dropped += 1
                return False
            self._queue.append(frame)
            self._condition.notify()
            return True

    def stop(self):
        # admission을 닫은 후 이미 받은 queue만 drain한다. Stop은 비동기이며 반복해도 안전하다.
        with self._condition:
            if self._state is LoggingState.RECORDING:
                self._state = LoggingState.STOPPING
                self._condition.notify_all()

    def wait(self, timeout=LOG_CLOSE_SECONDS):
        # blocking filesystem은 강제 취소하지 않는다. GUI는 유한 wait 실패 시 창을 유지한다.
        with self._condition:
            thread = self._thread
        if thread is None or thread.ident is None:
            return True
        thread.join(timeout)
        return not thread.is_alive()

    def _fail(self, phase, exc):
        # 부분 쓰기 여부는 보장할 수 없어 실패 프레임/남은 queue를 unconfirmed로 표시한다.
        with self._condition:
            self._state = LoggingState.ERROR
            message = f"{phase} failed ({type(exc).__name__}): {exc}"
            self._error = message if self._error is None else self._error + "; " + message
            self._unconfirmed += self._in_flight + len(self._queue)
            self._in_flight = 0
            self._queue.clear()
            self._condition.notify_all()

    def _run(self):
        # 파일 객체의 생성부터 종료까지 한 worker가 소유하며 GUI/Receiver는 접근하지 않는다.
        logger = None
        phase = "Open"
        try:
            logger = self._logger_factory(self._path, format=self._format)
            with self._condition:
                self._opened = True
            while True:
                with self._condition:
                    self._condition.wait_for(lambda: self._queue or self._state is not LoggingState.RECORDING)
                    if not self._queue:
                        break
                    frame = self._queue.popleft()
                    self._in_flight = 1
                phase = "Write/flush"
                logger.write(frame)
                with self._condition:
                    self._written += 1
                    self._in_flight = 0
        except Exception as exc:
            self._fail(phase, exc)
        finally:
            if logger is not None:
                try:
                    logger.close()
                except Exception as exc:
                    # Close 실패도 Error이며 파일 정상 종료를 주장하지 않는다.
                    self._fail("Close", exc)
                else:
                    with self._condition:
                        self._closed = True
            with self._condition:
                if self._state is not LoggingState.ERROR:
                    self._state = LoggingState.STOPPED
