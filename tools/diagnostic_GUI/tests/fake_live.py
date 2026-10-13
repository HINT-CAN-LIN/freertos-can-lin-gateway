"""Fake Live TEST ONLY transport. CAN 장치/드라이버/실제 송신을 사용하지 않는다."""
from dataclasses import replace
from threading import Event
from time import time
from pc_diagnostic.interfaces import CanInterface, CanInterfaceError
from pc_diagnostic.gui.demo import make_demo_frame

FAKE_CHANNEL = "FAKE LIVE / TEST ONLY"
FAKE_WAIT_SECONDS = 0.01


def fixture_frames(channel=FAKE_CHANNEL):
    # 기존 test_only.dbc의 합성 payload만 사용하며 Raw 속성은 반환 객체 그대로 검증한다.
    return tuple(replace(make_demo_frame(index), channel=channel, timestamp=time()) for index in range(2))


class FakeLive(CanInterface):
    def __init__(self, frames=None, *, shutdown_error=False, repeat=True):
        # 독립 transport의 수신/해제/미송신 증거를 기록한다.
        self.frames = fixture_frames() if frames is None else tuple(frames)
        self.repeat = repeat
        self.closed = Event()
        self.disconnect = Event()
        self.shutdown_error = shutdown_error
        self.shutdown_calls = 0
        self.send_calls = 0
        self.recv_calls = 0
        self.index = 0

    def recv(self, timeout=None):
        # 실제 finite recv 계약을 모의한다. 입력이 없으면 timeout 후 None을 반환한다.
        self.recv_calls += 1
        if self.disconnect.is_set():
            raise CanInterfaceError("FAKE LIVE TEST ONLY device detached")
        self.closed.wait(min(timeout or FAKE_WAIT_SECONDS, FAKE_WAIT_SECONDS))
        if not self.frames or self.closed.is_set() or (not self.repeat and self.index >= len(self.frames)):
            return None
        frame = self.frames[self.index % len(self.frames)]
        self.index += 1
        return frame

    def send(self, frame, timeout=None):
        # GUI가 TX를 호출하면 모든 자동화/Native Smoke에서 즉시 실패한다.
        self.send_calls += 1
        raise AssertionError("Live GUI must never call send")

    def shutdown(self):
        # 해제 실패도 시험에서만 모의하며 정상 transport는 정확히 한 번 해제해야 한다.
        self.shutdown_calls += 1
        self.closed.set()
        if self.shutdown_error:
            raise CanInterfaceError("FAKE LIVE TEST ONLY shutdown failed")
