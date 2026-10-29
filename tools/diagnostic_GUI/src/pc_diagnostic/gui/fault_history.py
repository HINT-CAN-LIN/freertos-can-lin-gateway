"""Qt 독립 Fault 관련 프레임 이력. 실제 Fault 상태 머신은 구현하지 않는다."""
from collections import deque
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping
from ..decoded_message import DecodeStatus
from ..frame import RawCanFrame
from .ecu_observation import EcuObservationModel, MessageMapping

FAULT_HISTORY_CAPACITY = 500  # 기존 Raw 표의 500행 정책과 맞춘 PC 로컬 이력 상한.
MAX_FAULT_SOURCES = 32  # 사용자 표시 매핑의 자원 제한이며 ECU/Queue/Fault 규격이 아니다.


def channel_key(channel):
    # 0/'0'/None을 구분하고 None을 wildcard로 사용하지 않는다.
    return type(channel).__name__, channel


def mapping_key(mapping):
    # 같은 이름만으로 연결하지 않고 실제 Channel/ID/STD·EXT/Message를 보존한다.
    return channel_key(mapping.channel), mapping.arbitration_id, mapping.is_extended_id, mapping.message_name


@dataclass(frozen=True, slots=True)
class FaultHistoryEntry:
    sequence: int
    source: str
    session_id: int
    receiver_run: int | None
    frame: RawCanFrame
    message_name: str
    decode_state: str
    signals: Mapping[str, int | float]
    units: Mapping[str, str | None]
    choices: Mapping[str, str]
    error: str | None
    timestamp_note: str
    fault_status: str = "Status Unknown"


class FaultHistoryModel:
    def __init__(self, capacity=FAULT_HISTORY_CAPACITY):
        # FrameObservation 입력과 제한된 immutable snapshot만 소유한다.
        if type(capacity) is not int or capacity <= 0:
            raise ValueError("fault history capacity must be positive")
        self.capacity = capacity
        self.entries = deque(maxlen=capacity)
        self.sources = {}
        self.validator = EcuObservationModel()
        self.session_id = None
        self.source = ""
        self.receiver_generation = 0
        self.receiver_run = None
        self.sequence = 0
        self.revision = 0
        self.clear()

    def clear(self):
        # PC 이력만 비운다. ECU Clear/TX, 공통 Cache, Raw Logger에는 접근하지 않는다.
        self.entries.clear()
        self.observed = self.history_omitted = 0
        self.missing_timestamps = self.reversed_timestamps = 0
        self.buffer_dropped = 0
        self._timestamps = {}
        self.revision += 1

    def sync_session(self, session, source):
        # DBC/Source 변경은 과거 Decode 값과 선택을 새 Interface에 재해석하지 않는다.
        changed = self.session_id != session.session_id or self.source != source
        if changed:
            self.session_id, self.source = session.session_id, source
            self.sources.clear()
            self.sequence = self.receiver_generation = 0
            self.receiver_run = None
            self.clear()
        return changed

    def resolve_source(self, mapping, session):
        # 기존 검증에 exact metadata의 유일성을 추가하여 첫 이름 후보 연결을 방지한다.
        message, state, detail = self.validator.validate(mapping, session)
        if state:
            return message, state, detail
        matches = [m for m in session.loader.get_messages()
                   if (m.name, m.frame_id, m.is_extended_frame) ==
                   (mapping.message_name, mapping.arbitration_id, mapping.is_extended_id)]
        if len(matches) != 1:
            return None, "Ambiguous", "Exact DBC message definition must be unique"
        return message, None, ""

    def add_source(self, mapping, session, source):
        # 기존 Fault Observation의 명시적 매핑 검증 계약을 재사용한다.
        self.sync_session(session, source)
        if not isinstance(mapping, MessageMapping):
            raise ValueError("expected an explicit MessageMapping")
        message, state, detail = self.resolve_source(mapping, session)
        if state:
            raise ValueError(f"{state}: {detail}")
        key = mapping_key(mapping)
        if key not in self.sources and len(self.sources) >= MAX_FAULT_SOURCES:
            raise ValueError("Fault display source capacity reached")
        self.sources[key] = mapping
        self.revision += 1
        return message

    def remove_source(self, key):
        # 수집 대상만 제거한다. 이미 수신한 이력을 삭제/재해석하지 않는다.
        self.sources.pop(key, None)
        self._timestamps.pop(key, None)
        self.revision += 1

    def begin_receiver(self, *, pending_prior=False):
        # 새 Start 구간을 표기한다. 이전 backlog가 섞일 수 있으면 run을 추측하지 않는다.
        self.receiver_generation += 1
        self.receiver_run = None if pending_prior else self.receiver_generation
        self.revision += 1

    def note_buffer_drop(self, dropped):
        # GUI 처리 전 제외량은 Fault 이력 상한 제외 및 실제 CAN 유실과 다른 값이다.
        if self.buffer_dropped != dropped:
            self.buffer_dropped = dropped
            self.revision += 1

    def record(self, observation, session, source):
        # DecodeSession의 per-frame 결과만 사용하고 payload/cache를 다시 해석하지 않는다.
        self.sync_session(session, source)
        frame = observation.frame
        if observation.session_id != self.session_id or not frame.is_rx or frame.is_error_frame:
            return False
        key = (channel_key(frame.channel), frame.arbitration_id, frame.is_extended_id, observation.message_name)
        mapping = self.sources.get(key)
        if mapping is None:
            return False
        message, state, _ = self.resolve_source(mapping, session)
        if state:
            return False
        result = observation.decoded
        success = (not observation.processing_error and result is not None
                   and result.decode_status is DecodeStatus.DECODED
                   and result.message_name == message.name)
        signals = {} if not success else dict(result.signals)
        error = observation.processing_error
        if not success:
            error = error or (None if result is None else result.error) or "No successful per-frame Decode result"
        definitions = {signal.name: signal for signal in message.signals}
        choices = {}
        for name, value in signals.items():
            # DBC Choice는 파일 metadata로만 표시하며 ACTIVE/CLEARED 상태로 판정하지 않는다.
            definition = definitions.get(name)
            choice = None if definition is None else (definition.choices or {}).get(value)
            if choice is not None:
                choices[name] = str(choice)
        stamp = frame.timestamp
        note = "Provided"
        if stamp is None:
            note = "Missing; preserved without synthetic timestamp"
            self.missing_timestamps += 1
        else:
            previous = self._timestamps.get(key)
            if previous is not None and stamp < previous:
                note = "Reversed versus previous observation; arrival order retained"
                self.reversed_timestamps += 1
            self._timestamps[key] = stamp
        self.sequence += 1
        entry = FaultHistoryEntry(
            self.sequence, source, self.session_id, self.receiver_run, frame, message.name,
            "Observed" if success else "Decode Error",
            MappingProxyType(signals), MappingProxyType(dict(observation.units)),
            MappingProxyType(choices), error, note,
        )
        if len(self.entries) == self.capacity:
            self.history_omitted += 1
        self.entries.append(entry)
        self.observed += 1
        self.revision += 1
        return True

    def filtered(self, *, fault_code=None, channel=None, message=None, errors_only=False):
        # 필터는 관측 이력을 삭제/정렬하지 않고 정확한 값만 비교한다.
        return tuple(entry for entry in self.entries
                     if (fault_code is None or entry.signals.get("FaultCode") == fault_code)
                     and (channel is None or channel_key(entry.frame.channel) == channel)
                     and (message is None or (entry.message_name, entry.frame.arbitration_id,
                                              entry.frame.is_extended_id) == message)
                     and (not errors_only or entry.decode_state == "Decode Error"))
