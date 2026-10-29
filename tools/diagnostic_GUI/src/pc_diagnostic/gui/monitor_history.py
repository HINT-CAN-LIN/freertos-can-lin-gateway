"""기존 Raw 표와 동일 상한의 처리 결과. UI Pause는 수신 버퍼와 분리한다."""
from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ObservedFrame:
    sequence: int
    source: str
    source_mode: str
    observation: object


class ObservationHistory:
    def __init__(self, capacity):
        # GUI 메인 스레드 전용이며 payload/Decode를 복제하거나 재해석하지 않는다.
        if type(capacity) is not int or capacity <= 0:
            raise ValueError("history capacity must be positive")
        self.capacity = capacity
        self.records = deque(maxlen=capacity)
        self.sequence = 0

    def record(self, observation, source, source_mode):
        # arrival order를 보존한다. 누락/역전 Timestamp로 정렬하지 않는다.
        self.sequence += 1
        record = ObservedFrame(self.sequence, source, source_mode, observation)
        self.records.append(record)
        return record

    def snapshot(self, *, session_id=None):
        # 불변 per-frame 참조를 유한 tuple로 고정하여 이후 수신과 격리한다.
        return tuple(record for record in self.records
                     if session_id is None or record.observation.session_id == session_id)

    def clear(self):
        # PC 표시 이력만 초기화한다. Signal Cache/Logger/ECU 상태에는 접근하지 않는다.
        self.records.clear()
        self.sequence = 0
