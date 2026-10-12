"""Transport boundary; no Gateway IDs, signals, or bus configuration defaults."""

from abc import ABC, abstractmethod
from collections import deque
from dataclasses import replace
import math
from threading import Condition
from typing import Iterable

from .frame import RawCanFrame


class CanInterfaceError(RuntimeError):
    """Transport unavailable, closed, unsupported, or failed."""


def validate_timeout(timeout: float | None) -> None:
    if timeout is not None and (
        type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout < 0
    ):
        raise ValueError("timeout must be finite and nonnegative, or None")


class CanInterface(ABC):
    @abstractmethod
    def recv(self, timeout: float | None = None) -> RawCanFrame | None:
        """Receive one frame; None on timeout. timeout=0 polls, None waits."""

    @abstractmethod
    def send(self, frame: RawCanFrame, timeout: float | None = None) -> None:
        """Submit a frame. Success does not prove ECU receipt or execution."""

    @abstractmethod
    def shutdown(self) -> None:
        """Release resources; repeated shutdown is harmless."""

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.shutdown()


class MockCanInterface(CanInterface):
    """FIFO fixture transport, with optional TX echo. No generated bus traffic."""

    def __init__(self, frames: Iterable[RawCanFrame] = (), *, loopback: bool = False):
        self._rx: deque[RawCanFrame] = deque()
        self._sent: list[RawCanFrame] = []
        self._condition = Condition()
        self._closed = False
        self._loopback = loopback
        for frame in frames:
            self.inject(frame)

    def _ensure_open(self):
        if self._closed:
            raise CanInterfaceError("CAN interface is closed")

    @property
    def sent_frames(self) -> tuple[RawCanFrame, ...]:
        with self._condition:
            return tuple(self._sent)

    def inject(self, frame: RawCanFrame) -> None:
        if not isinstance(frame, RawCanFrame):
            raise TypeError("expected RawCanFrame")
        with self._condition:
            self._ensure_open()
            self._rx.append(frame)
            self._condition.notify()

    def recv(self, timeout=None):
        validate_timeout(timeout)
        with self._condition:
            self._ensure_open()
            self._condition.wait_for(lambda: self._rx or self._closed, timeout)
            self._ensure_open()
            return self._rx.popleft() if self._rx else None

    def send(self, frame, timeout=None):
        validate_timeout(timeout)
        if not isinstance(frame, RawCanFrame):
            raise TypeError("expected RawCanFrame")
        with self._condition:
            self._ensure_open()
            self._sent.append(replace(frame, is_rx=False))
            if self._loopback:
                self._rx.append(replace(frame, is_rx=False))
                self._condition.notify()

    def shutdown(self):
        with self._condition:
            self._closed = True
            self._condition.notify_all()


class PythonCanInterface(CanInterface):
    """python-can adapter skeleton. Device/driver integration requires hardware validation.

    An injected bus is owned by this adapter and shut down on exit.
    Backend exceptions retain their cause through CanInterfaceError.
    """

    def __init__(self, *, interface: str | None = None, channel: str | int | None = None,
                 bitrate: int | None = None, bus=None):
        try:
            import can
        except ImportError as exc:
            raise CanInterfaceError("install gateway-pc-diagnostic[can] for python-can") from exc
        self._can = can
        self._closed = False
        if bus is not None:
            if interface is not None or channel is not None or bitrate is not None:
                raise ValueError("injected bus cannot be combined with connection settings")
            self._bus = bus
            return
        if not interface or channel is None or channel == "":
            raise ValueError("interface and channel must be specified")
        if bitrate is not None and (type(bitrate) is not int or bitrate <= 0):
            raise ValueError("bitrate must be a positive integer")
        if interface != "virtual" and bitrate is None:
            raise ValueError("explicit bitrate required for hardware backend")
        options = {} if bitrate is None else {"bitrate": bitrate}
        try:
            self._bus = can.Bus(interface=interface, channel=channel,
                                ignore_config=True, **options)
        except Exception as exc:
            raise CanInterfaceError(f"CAN open failed: {exc}") from exc

    def _ensure_open(self):
        if self._closed:
            raise CanInterfaceError("CAN interface is closed")

    def recv(self, timeout=None):
        validate_timeout(timeout)
        self._ensure_open()
        try:
            message = self._bus.recv(timeout)
        except Exception as exc:
            raise CanInterfaceError(f"CAN receive failed: {exc}") from exc
        if message is None:
            return None
        if message.is_fd or message.bitrate_switch or message.error_state_indicator:
            raise CanInterfaceError("CAN FD is unsupported in Phase 1; frame was not logged")
        try:
            return RawCanFrame(**{name: getattr(message, name) for name in (
                "arbitration_id", "data", "dlc", "is_extended_id", "is_remote_frame",
                "is_error_frame", "timestamp", "channel", "is_rx",
            )})
        except ValueError as exc:
            raise CanInterfaceError(f"unsupported or malformed received frame: {exc}") from exc

    def send(self, frame, timeout=None):
        validate_timeout(timeout)
        self._ensure_open()
        if not isinstance(frame, RawCanFrame):
            raise TypeError("expected RawCanFrame")
        if frame.is_error_frame:
            raise ValueError("error frames are capture-only in Phase 1")
        try:
            message = self._can.Message(
                arbitration_id=frame.arbitration_id, data=frame.data, dlc=frame.dlc,
                is_extended_id=frame.is_extended_id, is_remote_frame=frame.is_remote_frame,
                is_rx=False, check=True,
            )
            self._bus.send(message, timeout=timeout)
        except Exception as exc:
            raise CanInterfaceError(f"CAN send failed: {exc}") from exc

    def shutdown(self):
        if not self._closed:
            self._closed = True
            try:
                self._bus.shutdown()
            except Exception as exc:
                raise CanInterfaceError(f"CAN shutdown failed: {exc}") from exc
