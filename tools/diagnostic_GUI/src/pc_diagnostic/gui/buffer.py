"""Qt와 독립된 유한 수신 버퍼 및 표시 카운터."""
from collections import deque
from threading import Lock

BUFFER_CAPACITY = 512
DISPLAY_BATCH_SIZE = 100


class FrameBuffer:
    def __init__(self, capacity=BUFFER_CAPACITY):
        # 잘못된 표시 설정은 버퍼 생성 단계에서 차단한다.
        if type(capacity) is not int or capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        self._frames = deque(maxlen=capacity)
        self._lock = Lock()
        self.total_received = 0
        self.dropped = 0

    def append(self, frame):
        # GUI가 늦어지면 가장 오래된 표시 대기 프레임을 제외한다.
        with self._lock:
            if len(self._frames) == self._frames.maxlen:
                self.dropped += 1
            self._frames.append(frame)
            self.total_received += 1

    def drain(self, limit=DISPLAY_BATCH_SIZE):
        # 프레임과 카운터를 동일 lock 안에서 읽어 화면의 일관성을 유지한다.
        if type(limit) is not int or limit <= 0:
            raise ValueError("limit must be a positive integer")
        with self._lock:
            frames = [self._frames.popleft() for _ in range(min(limit, len(self._frames)))]
            return frames, self.total_received, self.dropped

    def clear(self):
        # Clear 이후 수신된 프레임부터 다시 계수한다.
        with self._lock:
            self._frames.clear()
            self.total_received = 0
            self.dropped = 0
