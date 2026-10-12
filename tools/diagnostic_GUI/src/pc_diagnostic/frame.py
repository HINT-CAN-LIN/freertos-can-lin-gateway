"""Classic CAN representation. Constraints are protocol bounds, not a message matrix."""

from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class RawCanFrame:
    arbitration_id: int
    data: bytes = b""
    dlc: int | None = None
    is_extended_id: bool = False
    is_remote_frame: bool = False
    is_error_frame: bool = False
    timestamp: float | None = None
    channel: str | int | None = None
    is_rx: bool = True

    def __post_init__(self) -> None:
        for name in ("is_extended_id", "is_remote_frame", "is_error_frame", "is_rx"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"{name} must be bool")
        # Error frames may carry a backend-specific error mask in the ID field.
        max_id = 0x1FFFFFFF if self.is_extended_id or self.is_error_frame else 0x7FF
        if type(self.arbitration_id) is not int or not 0 <= self.arbitration_id <= max_id:
            raise ValueError("arbitration_id is outside the selected CAN format")
        if not isinstance(self.data, (bytes, bytearray, memoryview)):
            raise ValueError("data must be bytes-like")
        object.__setattr__(self, "data", bytes(self.data))
        if self.dlc is None:
            object.__setattr__(self, "dlc", len(self.data))
        if type(self.dlc) is not int or not 0 <= self.dlc <= 8:
            raise ValueError("Classic CAN dlc must be 0..8")
        if self.is_remote_frame:
            if self.data or self.is_error_frame:
                raise ValueError("RTR must have no payload and cannot be an error frame")
        elif self.dlc != len(self.data):
            raise ValueError("dlc must equal payload length for non-RTR frames")
        if self.timestamp is not None:
            if (type(self.timestamp) not in (int, float)
                    or not math.isfinite(self.timestamp) or self.timestamp < 0):
                raise ValueError("timestamp must be finite, nonnegative, or None")
        if self.channel is not None and type(self.channel) not in (str, int):
            raise ValueError("channel must be str, int, or None")

    def to_record(self) -> dict:
        return {
            "arbitration_id": self.arbitration_id, "data": self.data.hex().upper(),
            "dlc": self.dlc, "is_extended_id": self.is_extended_id,
            "is_remote_frame": self.is_remote_frame, "is_error_frame": self.is_error_frame,
            "timestamp": self.timestamp, "channel": self.channel, "is_rx": self.is_rx,
        }

    @classmethod
    def from_record(cls, record: dict) -> "RawCanFrame":
        if not isinstance(record, dict):
            raise ValueError("frame record must be a JSON object")
        values = dict(record)
        try:
            values["data"] = bytes.fromhex(values.get("data", ""))
            return cls(**values)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid raw frame record: {exc}") from exc
