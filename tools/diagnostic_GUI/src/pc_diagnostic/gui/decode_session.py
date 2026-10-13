"""Qt 독립 조합 계층: 기존 DBC/Decode/Cache 계약을 GUI에 연결한다."""
from collections import OrderedDict
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from ..dbc_codec import DbcCodec
from ..dbc_loader import DbcLoader, DbcLookupError
from ..decode_service import DecodeService
from ..decoded_message import DecodedMessage
from ..frame import RawCanFrame

# 최신 시도 메타데이터 제한이며 CAN/ECU 정책이 아니다.
MAX_LATEST_ATTEMPTS = 512


@dataclass(frozen=True, slots=True)
class FrameObservation:
    """Raw 객체와 해당 프레임의 결과/DBC 메타데이터를 한 묶음으로 보관한다."""
    frame: RawCanFrame
    decoded: DecodedMessage | None
    units: Mapping[str, str | None]
    session_id: int
    processing_error: str | None = None
    message_name: str | None = None


class DecodeSession:
    def __init__(self):
        # 파일 자동 로드 없이 빈 세션으로 시작한다.
        self.session_id = 0
        self.loader = DbcLoader()
        self.service = DecodeService(DbcCodec(self.loader))
        self.latest_attempts = OrderedDict()

    def load(self, path):
        # Loader의 재로드 계약: 실패를 포함한 파일 교체마다 새 Cache를 사용한다.
        self.session_id += 1
        self.loader = DbcLoader()
        self.service = DecodeService(DbcCodec(self.loader))
        self.latest_attempts.clear()
        self.loader.load(path)

    def process(self, frame):
        # Bit/scale/enum 처리 및 정상 RX 저장은 기존 서비스에만 위임한다.
        result = None
        units = {}
        error = None
        name = None
        if self.loader.is_loaded:
            try:
                result = self.service.process(frame)
            except Exception as exc:
                # 예상 밖 application 오류도 Raw 행을 잃거나 수신을 종료하지 않는다.
                error = f"Processing failed ({type(exc).__name__}): {exc}"
            if frame.is_error_frame:
                # Error ID는 backend mask일 수 있으므로 DBC Message ID로 해석하지 않는다.
                return FrameObservation(frame, result, MappingProxyType(units), self.session_id, error)
            try:
                # 길이 오류/RTR도 정의된 Message 이름만 조회한다. Signal을 직접 해석하지 않는다.
                definition = self.loader.get_message_by_id(
                    frame.arbitration_id, is_extended_id=frame.is_extended_id,
                )
            except DbcLookupError:
                # Unknown ID는 이름/Unit을 합성하지 않는다.
                pass
            else:
                name = definition.name
                units = {signal.name: signal.unit for signal in definition.signals}
        observation = FrameObservation(frame, result, MappingProxyType(units),
                                       self.session_id, error, name)
        if name is not None:
            key = (frame.channel, name)
            self.latest_attempts[key] = observation
            self.latest_attempts.move_to_end(key)
            if len(self.latest_attempts) > MAX_LATEST_ATTEMPTS:
                self.latest_attempts.popitem(last=False)
        return observation

    def cached_message(self, observation):
        # 이전 DBC 세션의 Raw 이력을 현재 정의/Cache와 혼합하지 않는다.
        if observation.session_id != self.session_id or observation.message_name is None:
            return None
        return self.service.cache.get_message(
            observation.message_name, channel=observation.frame.channel,
        )

    def latest_attempt(self, observation):
        # 표시는 Channel/Message별 최신 처리 상태이며 ECU Health 판정이 아니다.
        if observation.session_id != self.session_id or observation.message_name is None:
            return None
        return self.latest_attempts.get((observation.frame.channel, observation.message_name))

    def cache_age(self, observation, now):
        # DEMO RX timestamp와 동일한 PC wall clock을 기존 Cache API에 전달한다.
        return self.service.cache.age(
            observation.message_name, channel=observation.frame.channel, now=now,
        )
