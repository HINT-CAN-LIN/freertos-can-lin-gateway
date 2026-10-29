"""PC observation storage. No Gateway timeout, health, routing or fault decisions."""

from dataclasses import dataclass
import math
from threading import Lock
from types import MappingProxyType
from typing import Mapping

from .decoded_message import DecodedMessage, DecodeStatus


@dataclass(frozen=True, slots=True)
class SignalState:
    value: int | float
    timestamp: float | None
    arbitration_id: int
    message_name: str
    channel: str | int | None


class SignalStateCache:
    """Use one cache per DBC session. Keys are (channel, message name).

    Latest means process arrival order, not sorting by potentially unsynchronized
    backend clocks. Frame snapshots are immutable; a new mux frame replaces the
    whole message, preventing old branch signals from appearing as current.
    """

    def __init__(self):
        self._lock = Lock()
        self._messages: dict[tuple[str | int | None, str], DecodedMessage] = {}

    def update(self, message: DecodedMessage) -> bool:
        if not isinstance(message, DecodedMessage):
            raise TypeError("expected DecodedMessage")
        if message.decode_status is not DecodeStatus.DECODED or not message.raw_frame.is_rx:
            return False
        key = (message.raw_frame.channel, message.message_name)
        with self._lock:
            self._messages[key] = message
        return True

    def get_message(self, message_name: str, *, channel: str | int | None = None) -> DecodedMessage | None:
        with self._lock:
            return self._messages.get((channel, message_name))

    def has_received(self, message_name: str, *, channel: str | int | None = None) -> bool:
        return self.get_message(message_name, channel=channel) is not None

    def last_timestamp(self, message_name: str, *, channel: str | int | None = None) -> float | None:
        message = self.get_message(message_name, channel=channel)
        return None if message is None else message.timestamp

    def get_signal_state(self, message_name: str, signal_name: str, *,
                         channel: str | int | None = None) -> SignalState | None:
        message = self.get_message(message_name, channel=channel)
        if message is None or signal_name not in message.signals:
            return None
        return SignalState(message.signals[signal_name], message.timestamp,
                           message.arbitration_id, message_name, channel)

    def get_signal(self, message_name: str, signal_name: str, *,
                   channel: str | int | None = None) -> int | float | None:
        signal = self.get_signal_state(message_name, signal_name, channel=channel)
        return None if signal is None else signal.value

    def snapshot(self) -> Mapping[tuple[str | int | None, str], DecodedMessage]:
        with self._lock:
            return MappingProxyType(dict(self._messages))

    def age(self, message_name: str, *, now: float, channel: str | int | None = None) -> float | None:
        """Caller supplies current time in the same clock as RX timestamp.

        No receive/time or backwards clock returns None, not a health verdict.
        Never substitute cache commit time for the source receive timestamp.
        """
        if type(now) not in (int, float) or not math.isfinite(now) or now < 0:
            raise ValueError("now must be finite and nonnegative")
        timestamp = self.last_timestamp(message_name, channel=channel)
        if timestamp is None or now < timestamp:
            return None
        return now - timestamp

    def clear(self) -> None:
        with self._lock:
            self._messages.clear()
