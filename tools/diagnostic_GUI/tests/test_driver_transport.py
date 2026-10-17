"""UART Transport 계약 검증. 실제 Serial I/O와 wire protocol을 실행하지 않는다."""
import pytest
from pc_diagnostic.gui.driver_transport import DriverTransport, TransportConnectionState


class MemoryOnlyTransport:
    """테스트 프로세스 메모리 안에서만 동작하는 UART 계약 대역."""

    def __init__(self):
        self._state = TransportConnectionState.NOT_CONFIGURED
        self._received = []
        self.sent_payloads = []
        self.error = None
        self.cleaned = False

    @property
    def connection_state(self):
        return self._state

    def connect(self):
        self._state = TransportConnectionState.CONNECTED
        self.error = None

    def disconnect(self):
        if self._state == TransportConnectionState.CONNECTED:
            self._state = TransportConnectionState.DISCONNECTED

    def send(self, payload):
        if self._state != TransportConnectionState.CONNECTED:
            self.error = "Memory transport is disconnected."
            self._state = TransportConnectionState.ERROR
            raise RuntimeError(self.error)
        if type(payload) is not bytes:
            raise TypeError("Opaque bytes required.")
        self.sent_payloads.append(bytes(payload))

    def receive(self):
        if self._state != TransportConnectionState.CONNECTED or not self._received:
            return None
        return self._received.pop(0)

    def inject_received_for_test(self, payload):
        """실제 VCU 응답이 아닌 테스트 입력만 대기열에 넣는다."""
        self._received.append(bytes(payload))

    def cleanup(self):
        self.disconnect()
        self._received.clear()
        self.cleaned = True


def test_transport_contract_is_opaque_and_memory_only():
    # 전송 계약은 byte 의미나 ACK 생성 규칙을 정의하지 않는다.
    transport = MemoryOnlyTransport()
    assert isinstance(transport, DriverTransport)
    assert transport.connection_state == TransportConnectionState.NOT_CONFIGURED
    assert transport.receive() is None
    with pytest.raises(RuntimeError):
        transport.send(b"opaque")
    assert transport.connection_state == TransportConnectionState.ERROR
    assert transport.error == "Memory transport is disconnected."

    transport.connect()
    assert transport.connection_state == TransportConnectionState.CONNECTED
    transport.send(b"\x00\xffopaque")
    assert transport.sent_payloads == [b"\x00\xffopaque"]
    assert transport.receive() is None  # Send가 가짜 VCU ACK를 자동 생성하지 않는다.
    transport.inject_received_for_test(b"TEST ONLY")
    assert transport.receive() == b"TEST ONLY"
    transport.disconnect()
    assert transport.connection_state == TransportConnectionState.DISCONNECTED
    transport.cleanup()
    assert transport.cleaned and transport.receive() is None