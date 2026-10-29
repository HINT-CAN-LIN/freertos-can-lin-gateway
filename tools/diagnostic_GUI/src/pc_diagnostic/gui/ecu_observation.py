"""명시적 ECU/Fault 표시 매핑. 실제 Healthy/Online/Fault 판정은 구현하지 않는다."""
from dataclasses import dataclass
from ..dbc_loader import DbcLookupError
from .message_statistics import MessageKey, MessageStatisticsStore, observation_age

ECU_NAMES = ("Gateway", "VCU", "Motor", "Cluster", "Door", "Light", "Window")
LIN_ECUS = frozenset(("Door", "Light", "Window"))


@dataclass(frozen=True, slots=True)
class MessageMapping:
    message_name: str | None
    channel: str | int | None
    arbitration_id: int | None
    is_extended_id: bool | None
    channel_selected: bool = False
    source_confirmed: bool = False
    signal_name: str | None = None

    @property
    def key(self):
        # 사용자 선택한 DBC 식별자를 data RX 키로 연결한다.
        return MessageKey(self.channel, self.arbitration_id, self.is_extended_id)


@dataclass(frozen=True, slots=True)
class EcuObservation:
    state: str
    count: int = 0
    timestamp: float | None = None
    age: float | None = None
    detail: str = ""
    signal_value: int | float | None = None


class EcuObservationModel:
    def __init__(self, *, capacity=None):
        # ECU 이름은 프로젝트 구성요소이며 기본 Message 연결은 없다.
        self.session_id = None
        self.mappings = {}
        self.fault_mapping = None
        self.statistics = MessageStatisticsStore() if capacity is None else MessageStatisticsStore(capacity)

    def sync_session(self, session):
        # 실패한 Reload도 새 세션이므로 이전 decode/연결/통계를 혼합하지 않는다.
        changed = self.session_id != session.session_id
        if changed:
            self.session_id = session.session_id
            self.mappings.clear()
            self.fault_mapping = None
            self.statistics.clear()
        return changed

    def record(self, observation, session):
        # 과거 세션 프레임은 현재 매핑의 근거로 사용하지 않는다.
        self.sync_session(session)
        if observation.session_id == self.session_id:
            self.statistics.record(observation)

    def bind(self, ecu, mapping, session):
        # 사용자 표시 설정만 변경하며 타 ECU public interface에는 접근하지 않는다.
        if ecu not in ECU_NAMES or not isinstance(mapping, MessageMapping):
            raise ValueError("expected an ECU name and MessageMapping")
        self.sync_session(session)
        self.mappings[ecu] = mapping

    def bind_fault(self, mapping, session):
        # Fault 의미를 사용자가 확인한 Message 전체를 읽기 전용 관찰한다.
        if not isinstance(mapping, MessageMapping):
            raise ValueError("expected MessageMapping")
        self.sync_session(session)
        self.fault_mapping = mapping

    def validate(self, mapping, session, *, ecu=None):
        # 이름/ID/STD-EXT의 exact 일치를 확인하고 송신자 metadata로 ECU를 추론하지 않는다.
        if mapping is None:
            return None, "Not Configured", "Choose an explicit source."
        if not session.loader.is_loaded:
            return None, "No DBC", "Load a DBC explicitly."
        if not mapping.message_name or not mapping.channel_selected or not mapping.source_confirmed:
            return None, "Ambiguous", "Choose Message/Channel and confirm source; no automatic mapping."
        try:
            message = session.loader.get_message_by_name(mapping.message_name)
        except DbcLookupError:
            return None, "Not Defined", "Message does not exist in this DBC."
        if type(mapping.arbitration_id) is not int or mapping.arbitration_id != message.frame_id or type(mapping.is_extended_id) is not bool or mapping.is_extended_id != message.is_extended_frame:
            return None, "Ambiguous", "CAN ID/Frame Format does not match the selected DBC Message."
        if ecu in LIN_ECUS and not mapping.signal_name:
            return None, "Not Available", "An individual LIN ECU Signal is required; CAN Message alone is insufficient."
        if mapping.signal_name:
            matches = [s for s in message.signals if s.name == mapping.signal_name]
            if not matches:
                return None, "Not Defined", "Signal is absent from selected Message."
            if len(matches) != 1:
                return None, "Ambiguous", "Signal is not unique."
        if ecu is not None:
            identity = (mapping.key, mapping.signal_name)
            duplicates = [name for name, other in self.mappings.items()
                          if name != ecu and (other.key, other.signal_name) == identity]
            if duplicates:
                return None, "Ambiguous", "Same source also mapped to: " + ", ".join(duplicates)
        return message, None, ""

    def observe(self, ecu, session, *, now):
        # Count/시각는 처리된 RX의 관측치이며 Age를 Timeout/Offline으로 해석하지 않는다.
        self.sync_session(session)
        mapping = self.mappings.get(ecu)
        message, state, detail = self.validate(mapping, session, ecu=ecu)
        if state:
            return EcuObservation(state, detail=detail)
        return self.source_observation(mapping, now=now)

    def source_observation(self, mapping, *, now):
        # Raw 수신과 decode 실패를 구분하며 누락된 통계를 실제 무수신이라고 단정하지 않는다.
        stat = self.statistics.get(mapping.key)
        if stat is None:
            detail = "No processed RX in this statistics interval."
            if self.statistics.capacity_excluded:
                detail += " Statistics capacity exclusions exist; reception is incomplete."
            return EcuObservation("No Data", detail=detail)
        latest = stat.latest
        cause = latest.processing_error
        if latest.decoded is not None and latest.decoded.decode_status.value != "decoded":
            cause = cause or latest.decoded.error or latest.decoded.decode_status.value
        value = None
        state = "Decode Error" if cause else "Observed"
        detail = cause or "CAN RX observed; does not prove ECU Health, Online or LIN reception."
        if mapping.signal_name:
            signals = {} if latest.decoded is None else latest.decoded.signals
            if not cause and mapping.signal_name not in signals:
                state, detail = "No Data", "Individual Signal is absent from this decoded RX (e.g. inactive mux)."
            value = signals.get(mapping.signal_name)
        return EcuObservation(state, stat.count, stat.last_seen,
                              observation_age(stat.last_seen, now), detail, value)

    def fault_observation(self, session, *, now):
        # 선택한 Fault 출처만 관찰하며 FaultCode/Recovery enum 의미는 생성하지 않는다.
        self.sync_session(session)
        message, state, detail = self.validate(self.fault_mapping, session)
        if state:
            return EcuObservation(state, detail=detail), None, None
        status = self.source_observation(self.fault_mapping, now=now)
        stat = self.statistics.get(self.fault_mapping.key)
        return status, message, None if stat is None else stat.last_good
