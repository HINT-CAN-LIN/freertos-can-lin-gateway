"""CAN 인터페이스와 독립된 메모리 전용 Mock 운전자 입력 Adapter."""
from collections import deque
from .driver_input import DriverCommand, HISTORY_CAPACITY, MockReceipt


class MockDriverAdapter:
    def __init__(self):
        # 수락 이력도 유한하며 실제 ECU/Bus/Receiver 상태를 보관하지 않는다.
        self._receipts = deque(maxlen=HISTORY_CAPACITY)
        self.closed = False

    @property
    def receipts(self):
        # 외부에서 수락 이력을 변조하지 못하도록 불변 뷰를 제공한다.
        return tuple(self._receipts)

    def accept(self, command):
        # PC 내부 요청 검증만 수행한다. RawCanFrame 생성이나 send 호출은 없다.
        if self.closed:
            raise RuntimeError("Mock adapter closed.")
        if not isinstance(command, DriverCommand):
            raise TypeError("DriverCommand required.")
        command.inputs.validated()
        receipt = MockReceipt(command)
        self._receipts.append(receipt)
        return receipt

    def shutdown(self):
        # 종료는 메모리 상태 정리이며 CAN 제어/안전 정지 명령이 아니다.
        self.closed = True
        self._receipts.clear()
