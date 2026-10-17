"""PC↔VCU 운전자 전송 계약. 실제 UART/Serial I/O 구현은 포함하지 않는다."""
from enum import Enum
from typing import Protocol, runtime_checkable


class TransportConnectionState(str, Enum):
    """향후 Transport 구현이 보고할 연결 상태 계약."""

    NOT_CONFIGURED = "NOT CONFIGURED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    ERROR = "ERROR"


@runtime_checkable
class DriverTransport(Protocol):
    """직렬화 규약과 분리된 opaque bytes 전송 계약.

    메서드는 계약 선언일 뿐이다. 이 Phase에는 포트 탐색, Open, Read, Write,
    패킷 Codec, ACK 또는 재전송 구현이 없다.
    """

    @property
    def connection_state(self) -> TransportConnectionState:
        """현재 연결 상태를 반환한다."""
        ...

    @property
    def error(self) -> str | None:
        """마지막 Transport 오류를 반환하거나 오류가 없으면 None을 반환한다."""
        ...

    def connect(self) -> None:
        """향후 승인된 장치 연결을 요청한다. GUI 메인 스레드에서 실행하지 않는다."""
        ...

    def disconnect(self) -> None:
        """연결을 끊고 대기 중인 작업을 취소한다."""
        ...

    def send(self, payload: bytes) -> None:
        """승인된 상위 계층 payload를 전달한다. bytes 내부 의미는 이 계약에 없다."""
        ...

    def receive(self) -> bytes | None:
        """수신 chunk를 반환하며, 데이터가 없으면 None을 반환한다."""
        ...

    def cleanup(self) -> None:
        """Worker 및 Transport 리소스를 안전하게 정리한다."""
        ...