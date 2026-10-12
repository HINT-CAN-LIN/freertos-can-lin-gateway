from dataclasses import replace

from .frame import RawCanFrame
from .interfaces import CanInterface


class RawCanSender:
    """Single raw transmission, without scheduling or signal encoding."""

    def __init__(self, interface: CanInterface):
        self.interface = interface

    def send(self, frame: RawCanFrame, *, timeout: float | None = None) -> None:
        if frame.is_error_frame:
            raise ValueError("error frames are capture-only in Phase 1")
        self.interface.send(replace(frame, is_rx=False), timeout=timeout)
