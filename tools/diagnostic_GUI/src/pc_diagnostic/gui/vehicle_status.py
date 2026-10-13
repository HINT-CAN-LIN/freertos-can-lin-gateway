"""Qt 독립 Vehicle 표시 설정과 Cache 조회. 차량 의미/Decode/Health 규칙은 만들지 않는다."""
from dataclasses import dataclass
from enum import Enum
from ..dbc_loader import DbcLookupError
from ..decoded_message import DecodeStatus

# 이 목록은 표시 후보이며 DBC Signal 이름이나 기본 연결을 정의하지 않는다.
DISPLAY_ITEMS = ("Vehicle Speed", "Motor RPM", "Gear", "Brake", "Torque", "DBC Observation")


class VehicleState(str, Enum):
    NO_DBC = "No DBC"
    NOT_DEFINED = "Not Defined"
    NO_DATA = "No Data"
    VALID = "Valid"
    DECODE_ERROR = "Decode Error"
    AMBIGUOUS = "Ambiguous"


@dataclass(frozen=True, slots=True)
class SignalMapping:
    """사용자가 확인한 표시 출처. None channel도 명시적으로 선택할 수 있다."""
    message_name: str | None
    signal_name: str | None
    channel: str | int | None
    channel_selected: bool = False
    meaning_confirmed: bool = False


@dataclass(frozen=True, slots=True)
class VehicleObservation:
    """기존 Cache 값/시각을 그대로 전달하는 표시 snapshot."""
    state: VehicleState
    value: int | float | None = None
    unit: str | None = None
    timestamp: float | None = None
    age: float | None = None
    detail: str = ""


class VehicleStatusModel:
    def __init__(self):
        # 기본 Production 매핑 없이 고정 개수의 표시 항목만 관리한다.
        self.session_id = None
        self.mappings: dict[str, SignalMapping] = {}

    def sync_session(self, session):
        # DBC 교체/실패로 새 세션이 되면 이전 사용자 연결을 재사용하지 않는다.
        changed = self.session_id != session.session_id
        if changed:
            self.session_id = session.session_id
            self.mappings.clear()
        return changed

    def bind(self, item, mapping, session):
        # 진단 도구 내부 설정만 변경하며 DBC/CAN Interface는 수정하지 않는다.
        if item not in DISPLAY_ITEMS or not isinstance(mapping, SignalMapping):
            raise ValueError("expected a display item and SignalMapping")
        self.sync_session(session)
        self.mappings[item] = mapping

    def unbind(self, item):
        # 다른 표시 항목/정상 수신 Cache에는 영향을 주지 않는다.
        self.mappings.pop(item, None)

    def definitions(self, session):
        # 기존 Loader의 읽기 전용 metadata만 사용하고 별도 DBC parse를 하지 않는다.
        return session.loader.get_messages() if session.loader.is_loaded else ()

    def resolve_definition(self, mapping, session):
        # exact Message/Signal만 조회한다. 유사 문자열 및 단일 후보도 자동 연결하지 않는다.
        if mapping is None or not mapping.signal_name:
            return None, VehicleState.AMBIGUOUS, "Choose an exact Message, Signal and Channel."
        if not mapping.message_name:
            matches = [m for m in self.definitions(session)
                       if any(s.name == mapping.signal_name for s in m.signals)]
            if not matches:
                return None, VehicleState.NOT_DEFINED, "Signal is not defined in this DBC."
            return None, VehicleState.AMBIGUOUS, f"Exact signal occurs in {len(matches)} message(s); choose Message."
        try:
            message = session.loader.get_message_by_name(mapping.message_name)
        except DbcLookupError:
            return None, VehicleState.NOT_DEFINED, "Message is not defined in this DBC."
        signals = [signal for signal in message.signals if signal.name == mapping.signal_name]
        if not signals:
            return None, VehicleState.NOT_DEFINED, "Signal is not defined in the selected Message."
        if len(signals) != 1 or not mapping.channel_selected or not mapping.meaning_confirmed:
            return None, VehicleState.AMBIGUOUS, "Confirm source/meaning and choose an explicit Channel."
        return signals[0], None, ""

    def observe(self, item, session, *, now):
        # 값은 성공 RX Cache에서만 조회한다. Valid는 ECU/물리값/Alive의 정상 판정이 아니다.
        self.sync_session(session)
        if not session.loader.is_loaded:
            return VehicleObservation(VehicleState.NO_DBC, detail="No DBC loaded; no display mapping.")
        mapping = self.mappings.get(item)
        signal, state, detail = self.resolve_definition(mapping, session)
        if state is not None:
            return VehicleObservation(state, detail=detail)
        cached = session.service.cache.get_signal_state(
            mapping.message_name, mapping.signal_name, channel=mapping.channel,
        )
        latest = session.latest_attempts.get((mapping.channel, mapping.message_name))
        cause = None
        if latest is not None:
            cause = latest.processing_error
            if latest.decoded is not None and latest.decoded.decode_status is not DecodeStatus.DECODED:
                cause = latest.decoded.error or latest.decoded.decode_status.value
        # 실패의 원인과 마지막 정상값은 동시에 제공한다. 새로운 값을 합성하지 않는다.
        if cause is not None:
            state, detail = VehicleState.DECODE_ERROR, cause
        elif cached is None:
            state, detail = VehicleState.NO_DATA, "No successful RX value for this exact Channel/Message/Signal."
        else:
            state, detail = VehicleState.VALID, "Last successful decoded RX; not ECU health or physical measurement."
        if latest is not None and not latest.frame.is_rx:
            detail += " Latest attempt is TX; RX cache is unchanged."
        if latest is None and cached is not None:
            detail += " Latest attempt metadata unavailable."
        if cached is None:
            return VehicleObservation(state, unit=signal.unit, detail=detail)
        age = session.service.cache.age(mapping.message_name, channel=mapping.channel, now=now)
        return VehicleObservation(state, cached.value, signal.unit, cached.timestamp, age, detail)
