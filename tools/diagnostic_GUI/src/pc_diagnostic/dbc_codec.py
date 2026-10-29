"""DBC-only interpretation. No project signal layout, enum or invalid policy."""

import math
from typing import Mapping

from .dbc_loader import DbcError, DbcLoader, DbcLookupError
from .decoded_message import DecodedMessage, DecodeStatus
from .frame import RawCanFrame


class DbcEncodeError(DbcError):
    pass


class DbcCodec:
    def __init__(self, loader: DbcLoader):
        self.loader = loader

    @staticmethod
    def _require_classic(message) -> None:
        if message.is_fd or message.length > 8 or message.is_container:
            raise ValueError("only ordinary Classic CAN DBC messages are supported")

    def decode(self, frame: RawCanFrame) -> DecodedMessage:
        """Each bad frame is a result, never a stream-ending decode exception.

        Return scaled numeric values (including numeric enum values). DBC reserved/
        invalid patterns and health semantics are not inferred by this layer.
        """
        if not isinstance(frame, RawCanFrame):
            raise TypeError("expected RawCanFrame")
        name = None
        try:
            if not self.loader.is_loaded:
                raise DbcError(self.loader.status.error or "DBC is not loaded")
            if frame.is_remote_frame or frame.is_error_frame:
                raise ValueError("RTR/error frame has no ordinary DBC signal payload")
            try:
                message = self.loader.get_message_by_id(
                    frame.arbitration_id, is_extended_id=frame.is_extended_id,
                )
            except DbcLookupError as exc:
                return DecodedMessage(frame, None, DecodeStatus.UNKNOWN, error=str(exc))
            name = message.name
            self._require_classic(message)
            if frame.dlc != message.length or len(frame.data) != message.length:
                raise ValueError(
                    f"DBC payload length mismatch: expected={message.length}, "
                    f"dlc={frame.dlc}, payload={len(frame.data)}"
                )
            signals = message.decode(frame.data, decode_choices=False, scaling=True,
                                     allow_truncated=False, allow_excess=False)
            return DecodedMessage(frame, name, DecodeStatus.DECODED, signals)
        except Exception as exc:
            return DecodedMessage(frame, name, DecodeStatus.INVALID, error=str(exc))

    def encode(self, message_name: str, signals: Mapping[str, int | float | str]) -> RawCanFrame:
        """Pure operation: strict validation before frame creation, never sends."""
        try:
            message = self.loader.get_message_by_name(message_name)
            self._require_classic(message)
            if not isinstance(signals, Mapping):
                raise ValueError("signals must be a dictionary/mapping")
            values = dict(signals)
            for name, value in values.items():
                if not isinstance(name, str) or type(value) not in (int, float, str):
                    raise ValueError("signal values must be numbers or DBC choice labels")
                if isinstance(value, float) and not math.isfinite(value):
                    raise ValueError(f"signal {name} must be finite")
            data = message.encode(values, scaling=True, padding=False, strict=True)
            return RawCanFrame(message.frame_id, data, dlc=message.length,
                               is_extended_id=message.is_extended_frame, is_rx=False)
        except Exception as exc:
            raise DbcEncodeError(f"DBC encode failed for {message_name}: {exc}") from exc
