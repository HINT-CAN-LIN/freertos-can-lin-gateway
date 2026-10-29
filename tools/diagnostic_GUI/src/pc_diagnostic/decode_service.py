"""Shared composition boundary for CLI and future thin UI consumers."""

from .dbc_codec import DbcCodec
from .decoded_message import DecodedMessage
from .frame import RawCanFrame
from .state_cache import SignalStateCache


class DecodeService:
    def __init__(self, codec: DbcCodec, cache: SignalStateCache | None = None):
        self.codec = codec
        self.cache = cache if cache is not None else SignalStateCache()

    def process(self, frame: RawCanFrame) -> DecodedMessage:
        message = self.codec.decode(frame)
        self.cache.update(message)
        return message
