"""Qt 독립 단일 Signal 관측 버퍼. Payload decode/ECU 유효성 판정은 하지 않는다."""
from collections import deque
from dataclasses import dataclass
import math
from ..decoded_message import DecodeStatus

GRAPH_SAMPLE_CAPACITY = 1000  # 표시 이력 상한이며 CAN 주기/Fault Timeout이 아니다.


def finite_number(value):
    # bool/text와 float 변환 불가·NaN/Infinity를 표시 가능한 숫자와 구분한다.
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(float(value))
    except (OverflowError, ValueError):
        return False


@dataclass(frozen=True, slots=True)
class GraphSelection:
    channel: str | int | None
    message_name: str
    arbitration_id: int
    is_extended_id: bool
    signal_name: str
    channel_selected: bool = True


@dataclass(frozen=True, slots=True)
class GraphSample:
    source: str
    session_id: int
    channel: str | int | None
    arbitration_id: int
    is_extended_id: bool
    message_name: str
    signal_name: str
    unit: str | None
    timestamp: float
    value: int | float
    segment: int


class SignalGraphModel:
    def __init__(self, capacity=GRAPH_SAMPLE_CAPACITY):
        # 모든 데이터는 MainWindow의 제한된 GUI 처리 batch에서만 갱신한다.
        if type(capacity) is not int or capacity <= 0:
            raise ValueError("graph capacity must be positive")
        self.capacity = capacity
        self.samples = deque(maxlen=capacity)
        self.selection = None
        self.session_id = None
        self.source = ""
        self.buffer_dropped = 0
        self.clear()

    def clear(self):
        # Graph 데이터만 비우고 CAN/Cache/Statistics/Logging에는 접근하지 않는다.
        self.samples.clear()
        self.accepted = self.history_omitted = self.decode_errors = 0
        self.value_excluded = self.timestamp_excluded = 0
        self.latest_value = self.latest_timestamp = self.unit = None
        self._last_timestamp = None
        self._segment = 0
        self._gap_pending = False
        self.state = "No Data"
        self.detail = "No samples since selection/Clear Graph."

    def sync_session(self, session, source):
        # DBC/Source generation 변경은 과거 선택과 Pause snapshot까지 새 세션으로 분리한다.
        changed = self.session_id != session.session_id or self.source != source
        if changed:
            self.session_id, self.source = session.session_id, source
            self.selection = None
            self.buffer_dropped = 0
            self.clear()
        if not session.loader.is_loaded:
            self.state, self.detail = "No DBC", "Load a DBC explicitly."
        return changed

    def definition(self, session):
        # 이름 유사성/첫 후보를 사용하지 않고 Message ID/STD·EXT/Signal을 모두 확인한다.
        chosen = self.selection
        if not session.loader.is_loaded:
            return None, "No DBC", "Load a DBC explicitly."
        if chosen is None or not chosen.channel_selected:
            return None, "No Data", "Select exact Channel, Message ID/Format/Name and Signal."
        messages = [m for m in session.loader.get_messages()
                    if m.name == chosen.message_name and m.frame_id == chosen.arbitration_id
                    and m.is_extended_frame is chosen.is_extended_id]
        if len(messages) != 1:
            return None, "Not Defined" if not messages else "Ambiguous", "Exact message must be unique."
        signals = [s for s in messages[0].signals if s.name == chosen.signal_name]
        if len(signals) != 1:
            return None, "Not Defined" if not signals else "Ambiguous", "Exact signal must be unique."
        return signals[0], None, ""

    def bind(self, selection, session, source):
        # 새 표시 선택은 이전 그래프 이력을 비우며 Cache 값을 sample로 복사하지 않는다.
        self.sync_session(session, source)
        self.selection = selection
        self.clear()
        signal, state, detail = self.definition(session)
        if state:
            self.state, self.detail = state, detail
        else:
            self.unit = signal.unit
        return state is None

    def note_buffer_drop(self, dropped):
        # 이 값은 GUI 처리 전 제외량이며 실제 CAN bus 손실량이 아니다.
        if dropped > self.buffer_dropped:
            self._gap_pending = True
        self.buffer_dropped = dropped

    def reject(self, state, detail):
        # 실패 뒤 정상점 사이를 연결하지 않아 관측 공백을 연속 데이터로 오인하지 않는다.
        self.state, self.detail = state, detail
        self._gap_pending = True

    def record(self, observation, session, source):
        # 기존 per-frame Decode 결과만 사용한다. timer/Cache polling으로 Sample을 합성하지 않는다.
        self.sync_session(session, source)
        signal, state, detail = self.definition(session)
        if state:
            self.state, self.detail = state, detail
            return False
        frame, chosen = observation.frame, self.selection
        if (observation.session_id != self.session_id or not frame.is_rx or frame.is_error_frame
                or type(frame.channel) is not type(chosen.channel) or frame.channel != chosen.channel
                or frame.arbitration_id != chosen.arbitration_id
                or frame.is_extended_id is not chosen.is_extended_id):
            return False
        result = observation.decoded
        if observation.processing_error or result is None or result.decode_status is not DecodeStatus.DECODED:
            self.decode_errors += 1
            self.reject("Decode Error", observation.processing_error or getattr(result, "error", None) or "Decode unavailable.")
            return False
        if result.message_name != chosen.message_name or chosen.signal_name not in result.signals:
            self.reject("No Data", "Selected signal absent in this decoded frame (e.g. inactive mux branch).")
            return False
        value = result.signals[chosen.signal_name]
        if not finite_number(value):
            self.value_excluded += 1
            self.reject("Unsupported Value", "Only finite numeric decoded values can be plotted; no conversion/inference.")
            return False
        self.latest_value, self.latest_timestamp, self.unit = value, frame.timestamp, signal.unit
        if (not finite_number(frame.timestamp) or frame.timestamp < 0
                or (self._last_timestamp is not None and frame.timestamp < self._last_timestamp)):
            self.timestamp_excluded += 1
            self.reject("Unsupported Timestamp", "Missing/backwards timestamp: value observed, time point excluded; no synthetic time.")
            return False
        if self._gap_pending:
            self._segment += 1
            self._gap_pending = False
        sample = GraphSample(source, self.session_id, frame.channel, frame.arbitration_id,
                             frame.is_extended_id, chosen.message_name, chosen.signal_name,
                             signal.unit, frame.timestamp, value, self._segment)
        if len(self.samples) == self.capacity:
            self.history_omitted += 1
        self.samples.append(sample)
        self.accepted += 1
        self._last_timestamp = frame.timestamp
        self.state = "Data"
        self.detail = "Decoded observation only; not ECU Healthy/physical validity. Numeric enums remain numeric."
        return True
