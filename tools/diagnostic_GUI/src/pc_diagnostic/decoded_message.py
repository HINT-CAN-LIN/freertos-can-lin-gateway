"""Immutable per-frame decode observation. Status is codec status, not ECU health."""

from dataclasses import dataclass, field
from enum import Enum
import math
from types import MappingProxyType
from typing import Mapping

from .frame import RawCanFrame


class DecodeStatus(str, Enum):
    DECODED = "decoded"
    UNKNOWN = "unknown"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class DecodedMessage:
    raw_frame: RawCanFrame
    message_name: str | None
    decode_status: DecodeStatus
    signals: Mapping[str, int | float] = field(default_factory=dict)
    error: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.raw_frame, RawCanFrame):
            raise ValueError("raw_frame must be RawCanFrame")
        if not isinstance(self.decode_status, DecodeStatus):
            raise ValueError("decode_status must be DecodeStatus")
        values = dict(self.signals)
        if self.decode_status is DecodeStatus.DECODED:
            if not self.message_name or self.error is not None:
                raise ValueError("decoded message requires a name and no error")
            for name, value in values.items():
                if (not isinstance(name, str) or type(value) not in (int, float)
                        or (isinstance(value, float) and not math.isfinite(value))):
                    raise ValueError("decoded signals must be finite numeric observations")
        elif values:
            raise ValueError("unsuccessful decode cannot contain normal signals")
        object.__setattr__(self, "signals", MappingProxyType(values))

    @property
    def timestamp(self) -> float | None:
        return self.raw_frame.timestamp

    @property
    def arbitration_id(self) -> int:
        return self.raw_frame.arbitration_id

    def to_record(self) -> dict:
        return {
            "timestamp": self.timestamp, "arbitration_id": self.arbitration_id,
            "message_name": self.message_name, "signals": dict(self.signals),
            "decode_status": self.decode_status.value, "error": self.error,
            "raw_frame": self.raw_frame.to_record(),
        }
