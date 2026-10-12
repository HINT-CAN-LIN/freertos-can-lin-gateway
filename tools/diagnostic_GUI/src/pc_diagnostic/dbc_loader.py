"""Explicit, strict DBC loading. Loading does not certify project approval."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cantools.database.can import Message


class DbcError(ValueError):
    """DBC operation failed without changing any bus or interface definitions."""


class DbcLoadError(DbcError):
    pass


class DbcLookupError(DbcError):
    pass


class DbcLoadState(str, Enum):
    UNLOADED = "unloaded"
    LOADED = "loaded"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class DbcLoadStatus:
    state: DbcLoadState = DbcLoadState.UNLOADED
    path: Path | None = None
    message_count: int = 0
    error: str | None = None


class DbcLoader:
    """Caller supplies a path. A failed load clears the previous database.

    Configure/load before starting a decode thread. Lookups return cantools Message
    objects; callers must treat them as read-only. Reload requires a new cache.
    """

    def __init__(self):
        self._status = DbcLoadStatus()
        self._by_name: dict = {}
        self._by_id: dict = {}

    @property
    def status(self) -> DbcLoadStatus:
        return self._status

    @property
    def is_loaded(self) -> bool:
        return self._status.state is DbcLoadState.LOADED

    def load(self, path: str | Path) -> "DbcLoader":
        self._by_name = {}
        self._by_id = {}
        source = None
        try:
            source = Path(path).resolve()
            if not source.is_file():
                raise DbcLoadError(f"DBC file does not exist or is not a file: {source}")
            try:
                import cantools
            except ImportError as exc:
                raise DbcLoadError("install gateway-pc-diagnostic[dbc] for cantools") from exc
            database = cantools.database.load_file(source, database_format="dbc", strict=True)
            if not database.messages:
                raise DbcLoadError("DBC contains no CAN messages")
            by_name = {}
            by_id = {}
            # The format bit is part of identity. Avoid lookup masking/overwriting
            # when standard and extended messages share their numeric ID.
            for message in database.messages:
                key = (message.frame_id, message.is_extended_frame)
                if message.name in by_name or key in by_id:
                    raise DbcLoadError(f"ambiguous duplicate message name or CAN ID: {message.name}")
                by_name[message.name] = message
                by_id[key] = message
            self._by_name, self._by_id = by_name, by_id
            self._status = DbcLoadStatus(DbcLoadState.LOADED, source, len(by_name))
            return self
        except Exception as exc:
            error = f"DBC load failed: {exc}"
            self._status = DbcLoadStatus(DbcLoadState.ERROR, source, error=error)
            raise DbcLoadError(error) from exc

    def _ensure_loaded(self) -> None:
        if not self.is_loaded:
            raise DbcLookupError(self._status.error or "DBC is not loaded")

    def get_message_by_name(self, name: str) -> "Message":
        self._ensure_loaded()
        try:
            return self._by_name[name]
        except KeyError as exc:
            raise DbcLookupError(f"unknown DBC message name: {name}") from exc

    def get_message_by_id(self, arbitration_id: int, *, is_extended_id: bool = False) -> "Message":
        self._ensure_loaded()
        if type(arbitration_id) is not int or type(is_extended_id) is not bool:
            raise DbcLookupError("CAN lookup requires an integer ID and bool format")
        try:
            return self._by_id[(arbitration_id, is_extended_id)]
        except KeyError as exc:
            raise DbcLookupError(
                f"unknown DBC CAN ID: 0x{arbitration_id:X} extended={is_extended_id}"
            ) from exc
