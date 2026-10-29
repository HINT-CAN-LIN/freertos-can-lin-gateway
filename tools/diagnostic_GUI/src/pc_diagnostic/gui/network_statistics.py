"""Qt 독립 CAN RX 관측 통계. 프로젝트 Jitter/Health/Bus Load 판정을 생성하지 않는다."""
from collections import OrderedDict
from dataclasses import dataclass
import math
from types import MappingProxyType
from .message_statistics import MessageKey, MAX_STATISTICS_ENTRIES

TIMESTAMP_UNIT = "seconds"
JITTER_STATUS = "Definition Pending"
HARDWARE_STATUS = "NOT VERIFIED"
NETWORK_SCHEMA = "pc-network-observation-v1"


@dataclass(slots=True)
class IntervalAccumulator:
    key: MessageKey
    count: int = 0
    first: float | None = None
    last: float | None = None
    previous: float | None = None
    intervals: int = 0
    span: float = 0.0
    minimum: float | None = None
    maximum: float | None = None
    last_interval: float | None = None
    missing: int = 0
    duplicate: int = 0
    reversed: int = 0
    overflow: int = 0
    segments: int = 0

    def record(self, frame):
        # Timestamp를 바꾸거나 정렬하지 않는다. 통계 저장 공간은 키당 상수다.
        stamp = frame.timestamp
        if self.count == 0:
            self.first = stamp
        self.count += 1
        self.last = stamp
        self.last_interval = None
        if stamp is None:
            self.missing += 1
            self.previous = None
            return
        if self.previous is None:
            self.segments += 1
        else:
            delta = stamp - self.previous
            if not math.isfinite(delta) or not math.isfinite(self.span + delta):
                self.overflow += 1
            elif delta == 0:
                self.duplicate += 1
            elif delta < 0:
                self.reversed += 1
            else:
                self.intervals += 1
                self.span += delta
                self.last_interval = delta
                self.minimum = delta if self.minimum is None else min(self.minimum, delta)
                self.maximum = delta if self.maximum is None else max(self.maximum, delta)
        self.previous = stamp

    def break_interval(self):
        # Stop/Start 대기 구간을 CAN 수신 간격으로 계상하지 않는다.
        self.previous = None
        self.last_interval = None


def expected_metadata(loader, key):
    # 사용자가 로드한 실제 DBC만 조회한다. 프로젝트 ID/주기를 하드코딩하지 않는다.
    if key.is_error_frame or key.is_remote_frame:
        return None, None, None, "Error/RTR: no expected data-message period", None
    if not loader.is_loaded:
        return None, None, None, "No DBC", None
    from ..dbc_loader import DbcLookupError
    try:
        message = loader.get_message_by_id(key.arbitration_id, is_extended_id=key.is_extended_id)
    except DbcLookupError:
        return None, None, None, "Not Defined in current DBC", None
    attribute = None if message.dbc is None else message.dbc.attributes.get("SourceTxType")
    tx_type = None if attribute is None else attribute.value
    source = f"Explicit DBC: {loader.status.path.name}; SourceTxType / GenMsgCycleTime"
    if tx_type == "Event":
        return message.name, tx_type, None, "Event: no expected period", source
    cycle = message.cycle_time
    if tx_type != "Cyclic" or type(cycle) not in (int, float) or not math.isfinite(cycle) or cycle <= 0:
        return message.name, tx_type, None, "Expected Period Definition Pending", source
    return message.name, tx_type, cycle, "DBC metadata only; no approved tolerance", source


class NetworkStatisticsModel:
    def __init__(self, capacity=MAX_STATISTICS_ENTRIES):
        # 기존 통계 키 상한을 재사용한다. CAN/LIN 주기나 KPI threshold가 아니다.
        if type(capacity) is not int or capacity <= 0:
            raise ValueError("network statistics capacity must be a positive integer")
        self.capacity = capacity
        self.generation = 0
        self.clear(source="No Source", source_kind="Unknown", timestamp_source="Raw timestamp, producer unspecified")

    def clear(self, *, source, source_kind, timestamp_source, dropped_baseline=0):
        # 기존 ECU 통계의 Clear/Source/DBC session 초기화 경계를 따른다.
        self.entries = OrderedDict()
        self.source, self.source_kind, self.timestamp_source = source, source_kind, timestamp_source
        self.dropped_baseline = dropped_baseline
        self.buffer_dropped = self.capacity_excluded = self.processed_rx = self.ignored_tx = 0
        self.error_frames = self.receiver_runs = 0
        self.pending_boundary = False
        self.generation += 1

    def begin_receiver(self, *, pending_prior=False):
        # Count는 유지하고 새 수신 run에서 간격 연결만 끊는다.
        self.receiver_runs += 1
        self.pending_boundary |= pending_prior
        for entry in self.entries.values():
            entry.break_interval()
        self.generation += 1

    def note_buffer_drop(self, cumulative):
        # GUI 처리 전에 제외된 수신은 메시지별로 배분하지 않는다. 전체 timing을 N/A 처리한다.
        dropped = max(0, cumulative - self.dropped_baseline)
        if dropped != self.buffer_dropped:
            self.buffer_dropped = dropped
            self.generation += 1

    def record(self, frame):
        # 기존 RawCanFrame만 받으며 별도 수신/Decode/Signal 의미를 구현하지 않는다.
        if not frame.is_rx:
            self.ignored_tx += 1
            self.generation += 1
            return
        self.processed_rx += 1
        self.error_frames += int(frame.is_error_frame)
        key = MessageKey.from_frame(frame)
        entry = self.entries.get(key)
        if entry is None:
            if len(self.entries) >= self.capacity:
                self.capacity_excluded += 1
                self.generation += 1
                return
            entry = self.entries[key] = IntervalAccumulator(key)
        entry.record(frame)
        self.generation += 1

    def timing_status(self, entry):
        # 누락·불연속을 정상 KPI로 포장하지 않고 원인을 표시한다.
        if self.buffer_dropped or self.capacity_excluded or self.pending_boundary:
            return "N/A: incomplete observation (drop/capacity/run boundary)"
        if entry.missing or entry.duplicate or entry.reversed or entry.overflow:
            return "N/A: timestamp missing/duplicate/reversed/overflow"
        if entry.key.is_error_frame or entry.key.is_remote_frame:
            return "N/A: Error/RTR; no periodic data KPI"
        if not entry.intervals:
            return "N/A: insufficient consecutive samples"
        return "Observed intervals only; clock accuracy NOT VERIFIED"

    @property
    def observed_id_count(self):
        # Error mask를 CAN Message ID로 세지 않는다. 상한 제외 시 tracked ID 하한이다.
        return len({(type(e.key.channel), e.key.channel, e.key.arbitration_id, e.key.is_extended_id)
                    for e in self.entries.values() if not e.key.is_error_frame})

    def snapshot_records(self, loader):
        # 파일/GUI에 같은 immutable 유한 snapshot을 제공한다. Source는 모델 구간에 고정된다.
        rows = []
        for entry in self.entries.values():
            key = entry.key
            name, tx_type, expected, comparison, expected_source = expected_metadata(loader, key)
            status = self.timing_status(entry)
            usable = status.startswith("Observed")
            mean = entry.span / entry.intervals if usable else None
            rate = None if mean is None or mean <= 0 else 1 / mean
            if rate is not None and not math.isfinite(rate):
                rate = None
            delta_ms = None if mean is None or expected is None else mean * 1000 - expected
            if delta_ms is not None and not math.isfinite(delta_ms):
                delta_ms = None
            rows.append(MappingProxyType({
                "schema_version": NETWORK_SCHEMA, "record_type": "network_observation",
                "source": self.source, "source_kind": self.source_kind,
                "channel": key.channel, "channel_type": type(key.channel).__name__,
                "arbitration_id": key.arbitration_id, "is_extended_id": key.is_extended_id,
                "is_remote_frame": key.is_remote_frame, "is_error_frame": key.is_error_frame,
                "message_name": name, "frame_count": entry.count,
                "first_timestamp": entry.first, "last_timestamp": entry.last,
                "observed_duration_s": entry.span if usable else None,
                "interval_count": entry.intervals, "interval_segments": entry.segments,
                "last_interval_s": entry.last_interval if usable else None,
                "mean_period_s": mean, "min_period_s": entry.minimum if usable else None,
                "max_period_s": entry.maximum if usable else None,
                "observed_frame_rate_hz": rate,
                "expected_period_ms": expected, "mean_minus_expected_ms": delta_ms,
                "tx_type": tx_type, "expected_source": expected_source, "comparison_status": comparison,
                "timing_status": status, "jitter_status": JITTER_STATUS, "jitter": None,
                "timestamp_source": self.timestamp_source, "timestamp_unit": TIMESTAMP_UNIT,
                "clock_accuracy": "NOT VERIFIED", "hardware_verification": HARDWARE_STATUS,
                "bus_load_percent": None, "controller_state": "Unsupported",
                "timestamp_missing": entry.missing, "timestamp_duplicate": entry.duplicate,
                "timestamp_reversed": entry.reversed, "timestamp_overflow": entry.overflow,
                "buffer_dropped": self.buffer_dropped, "capacity_excluded": self.capacity_excluded,
                "receiver_runs": self.receiver_runs, "pending_run_boundary": self.pending_boundary,
                "processed_rx": self.processed_rx, "error_frame_count": self.error_frames,
            }))
        return tuple(rows)
