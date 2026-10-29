"""기존 Mock/Live transport의 수신을 GUI 스레드에서 분리한다."""
from threading import Event
from PySide6.QtCore import QThread, Signal
from ..interfaces import CanInterface, MockCanInterface
from .connection import MOCK_MODE, LIVE_MODE
from .demo import make_demo_frame

# GUI 데모 표시/취소 설정이며 CAN/LIN 주기 또는 Fault Timeout이 아니다.
DEMO_INTERVAL_SECONDS = 0.1
RECEIVE_POLL_SECONDS = 0.05
CLOSE_WAIT_MS = 1000


class ReceiveWorker(QThread):
    failed = Signal(str)
    opened = Signal()

    def __init__(self, buffer, interface_factory=MockCanInterface, parent=None, *, frame_sink=None, mode=MOCK_MODE):
        # 수신 프레임마다 Qt signal을 보내지 않아 이벤트 큐 누적을 제한한다.
        super().__init__(parent)
        self._buffer = buffer
        self._frame_sink = frame_sink
        self._interface_factory = interface_factory
        self._stop_event = Event()
        self._mode = mode
        self.ready = Event()
        self.release_failed = False

    def request_stop(self):
        # start 직후에도 취소 요청을 보존하며 GUI 스레드에서 recv하지 않는다.
        self._stop_event.set()

    def run(self):
        # transport 생성부터 해제까지 worker가 소유한다.
        transport = None
        try:
            if self._stop_event.is_set():
                return
            transport = self._interface_factory()
            if self._mode == MOCK_MODE and not isinstance(transport, MockCanInterface):
                raise TypeError("Mock mode requires MockCanInterface")
            if self._mode == LIVE_MODE and (not isinstance(transport, CanInterface) or isinstance(transport, MockCanInterface)):
                raise TypeError("Live mode requires a non-Mock CanInterface")
            if self._mode not in (MOCK_MODE, LIVE_MODE):
                raise ValueError("Unknown receiver mode")
            # Open 중 Stop은 backend 생성 완료 직후 확인하며 transport는 finally에서 해제한다.
            if self._stop_event.is_set():
                return
            self.ready.set()
            self.opened.emit()
            index = 0
            while not self._stop_event.is_set():
                # Live에는 generator/inject/send를 호출하는 경로가 없다.
                if self._mode == MOCK_MODE:
                    transport.inject(make_demo_frame(index))
                frame = transport.recv(timeout=RECEIVE_POLL_SECONDS)
                if frame is not None:
                    # Logging Queue는 표시 Buffer drop 이전의 동일 Raw 객체를 받는다.
                    if self._frame_sink is not None:
                        self._frame_sink(frame)
                    self._buffer.append(frame)
                elif self._mode == LIVE_MODE:
                    # 즉시 None을 반환하는 backend에서도 busy polling을 피한다.
                    self._stop_event.wait(RECEIVE_POLL_SECONDS)
                index += 1
                if self._mode == MOCK_MODE and self._stop_event.wait(DEMO_INTERVAL_SECONDS):
                    break
        except Exception as exc:
            # 원인과 예외 종류를 UI에 전달하고 반복 재시도로 숨기지 않는다.
            self.failed.emit(f"Receive failed ({type(exc).__name__}): {exc}")
        finally:
            self.ready.clear()
            if transport is not None:
                try:
                    transport.shutdown()
                except Exception as exc:
                    self.release_failed = True
                    self.failed.emit(f"Shutdown failed ({type(exc).__name__}): {exc}")
