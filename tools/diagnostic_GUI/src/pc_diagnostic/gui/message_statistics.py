"""Qt 독립 Raw RX 통계. 처리된 부분집합을 계수하며 ECU 판정은 하지 않는다."""
from collections import OrderedDict
from dataclasses import dataclass
import math

# PC 화면의 저장 상한이며 CAN/LIN 규격 또는 Fault 정책이 아니다.
MAX_STATISTICS_ENTRIES = 512


def observation_age(timestamp, now):
    # 수신 시각이 없거나 clock이 역행하면 나이를 합성하지 않는다.
    if timestamp is None or not math.isfinite(now) or now < timestamp:
        return None
    return now - timestamp


@dataclass(frozen=True, slots=True)
class MessageKey:
    channel: str | int | None
    arbitration_id: int
    is_extended_id: bool
    is_error_frame: bool = False
    is_remote_frame: bool = False

    @classmethod
    def from_frame(cls, frame):
        # 오류 mask/RTR도 data frame과 섞지 않고 실제 Raw 속성을 보존한다.
        return cls(frame.channel, frame.arbitration_id, frame.is_extended_id,
                   frame.is_error_frame, frame.is_remote_frame)


@dataclass(frozen=True, slots=True)
class MessageStatistics:
    key: MessageKey
    count: int
    first_seen: float | None
    last_seen: float | None
    dlc: int
    latest: object
    last_good: object | None


class MessageStatisticsStore:
    def __init__(self, capacity=MAX_STATISTICS_ENTRIES):
        # 잘못된 GUI 설정을 즉시 거부한다.
        if type(capacity) is not int or capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        self.capacity = capacity
        self.clear()

    def clear(self):
        # Clear/DBC 새 세션은 새 통계 구간이다. 기존 Signal Cache와 독립이다.
        self.entries = OrderedDict()
        self.processed_rx = 0
        self.ignored_tx = 0
        self.capacity_excluded = 0

    def record(self, observation):
        # 기존 DecodeSession의 결과를 받으며 Decode를 다시 수행하지 않는다.
        frame = observation.frame
        if not frame.is_rx:
            self.ignored_tx += 1
            return
        self.processed_rx += 1
        key = MessageKey.from_frame(frame)
        old = self.entries.get(key)
        if old is None and len(self.entries) >= self.capacity:
            # 이미 저장한 키의 count를 보존하며 새 키 프레임만 제외한다.
            self.capacity_excluded += 1
            return
        good = (observation.decoded is not None
                and observation.decoded.decode_status.value == "decoded"
                and not observation.processing_error)
        self.entries[key] = MessageStatistics(
            key, 1 if old is None else old.count + 1,
            frame.timestamp if old is None else old.first_seen,
            frame.timestamp, frame.dlc, observation,
            observation if good else (None if old is None else old.last_good),
        )

    def get(self, key):
        # 동일 Channel/ID/format에 대한 immutable snapshot만 제공한다.
        return self.entries.get(key)

    def snapshot(self):
        # GUI 갱신용 유한 snapshot이며 수신 스레드에서 사용하지 않는다.
        return tuple(self.entries.values())
