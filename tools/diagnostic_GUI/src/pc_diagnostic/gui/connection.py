"""Qt 독립 연결 설정과 기존 python-can Adapter 생성. CAN 송신은 요청하지 않는다."""
from dataclasses import dataclass
from importlib.util import find_spec
from ..interfaces import CanInterfaceError, PythonCanInterface

MOCK_MODE = "Mock"
LIVE_MODE = "Live"
LIVE_BACKENDS = ("slcan", "gs_usb")
MOCK_CHANNEL = "DEMO/TEST ONLY"
MOCK_SOURCE_LABEL = "Mock / DEMO / TEST ONLY"
CLUSTER_TEST_BITRATE = 500000  # 현재 Cluster 설정의 시험 기준이며 자동 장치 탐색 결과가 아니다.
DEPENDENCIES = {
    "slcan": ("serial", "python-can[serial]>=4.6,<5"),
    "gs_usb": ("gs_usb", "python-can[gs-usb]>=4.6,<5"),
}


@dataclass(frozen=True, slots=True)
class ConnectionSettings:
    mode: str = MOCK_MODE
    backend: str = ""
    channel: str | int | None = None
    bitrate: int | None = None

    def validate(self):
        # CAN ID/Layout을 정의하지 않고 연결 입력의 형식만 검증한다.
        if self.mode == MOCK_MODE:
            return self
        if self.mode != LIVE_MODE or self.backend not in LIVE_BACKENDS:
            raise ValueError("Live backend must be explicitly selected: slcan or gs_usb.")
        if self.backend == "slcan":
            if not isinstance(self.channel, str) or not self.channel.strip():
                raise ValueError("SLCAN requires an explicit serial port/channel.")
        elif type(self.channel) is not int or self.channel < 0:
            raise ValueError("gs_usb requires an explicit nonnegative device index.")
        if type(self.bitrate) is not int or self.bitrate <= 0:
            raise ValueError("Bitrate must be a positive integer in bit/s.")
        return self

    def source_text(self):
        # Backend의 실제 수신 channel은 RawCanFrame 그대로 유지하며 설정과 구분한다.
        if self.mode == MOCK_MODE:
            return MOCK_SOURCE_LABEL
        return f"Live / {self.backend or 'not selected'} / channel={self.channel!r} / bitrate={self.bitrate}"


def require_live_dependencies(backend):
    # 필수 모듈 검사는 Worker에서 수행하고 설치/드라이버 변경은 하지 않는다.
    packages = [("can", "python-can>=4.6,<5"), DEPENDENCIES[backend]]
    if backend == "gs_usb":
        packages.append(("usb", "python-can[gs-usb]>=4.6,<5"))
    for module, package in packages:
        if find_spec(module) is None:
            raise CanInterfaceError(
                f"Missing Live dependency: {module}. Install with pip install '{package}' "
                "in the active environment after approval. Device firmware/driver is not verified."
            )


def open_live_interface(settings):
    # 기존 CLI Adapter를 재사용한다. listen-only 또는 물리 무송신을 보장하지 않는다.
    settings.validate()
    if settings.mode != LIVE_MODE:
        raise ValueError("Live interface requires Live settings.")
    require_live_dependencies(settings.backend)
    return PythonCanInterface(interface=settings.backend, channel=settings.channel, bitrate=settings.bitrate)
