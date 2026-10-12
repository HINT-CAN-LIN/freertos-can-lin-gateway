import time
from typing import Callable

from .frame import RawCanFrame
from .interfaces import CanInterface, validate_timeout


def format_frame(frame: RawCanFrame) -> str:
    timestamp = "unknown" if frame.timestamp is None else f"{frame.timestamp:.6f}"
    width = 8 if frame.is_extended_id or frame.is_error_frame else 3
    kind = "ERROR" if frame.is_error_frame else "RTR" if frame.is_remote_frame else "DATA"
    return (f"{timestamp} {'RX' if frame.is_rx else 'TX'} ch={frame.channel!r} "
            f"{'EXT' if frame.is_extended_id else 'STD'} "
            f"0x{frame.arbitration_id:0{width}X} {kind} DLC={frame.dlc} "
            f"{frame.data.hex(' ').upper()}").rstrip()


def capture(interface: CanInterface, on_frame: Callable[[RawCanFrame], None], *,
            count: int | None = None, duration: float | None = None) -> int:
    """Stop at either limit; idle receives do not consume count. Ctrl+C is caller-owned."""
    if count is not None and (type(count) is not int or count <= 0):
        raise ValueError("count must be positive")
    validate_timeout(duration)
    deadline = None if duration is None else time.monotonic() + duration
    received = 0
    while count is None or received < count:
        timeout = 0.1  # CLI responsiveness, not a CAN cycle/timeout specification.
        if deadline is not None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            timeout = min(timeout, remaining)
        frame = interface.recv(timeout)
        if frame is not None:
            on_frame(frame)
            received += 1
    return received
