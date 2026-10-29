"""Background USB serial transport; Qt UI stays responsive during UART I/O."""
from threading import Lock
from time import monotonic

from PySide6.QtCore import QThread, Signal

from .uart_protocol import ACK_SIZE, SYNC, decode_ack, encode_driver_input, ACK_STATUS

BAUD_RATE = 115200
SEND_PERIOD_S = 0.100
ACK_TIMEOUT_S = 0.600


class VcuUartWorker(QThread):
    status = Signal(str)
    acknowledgement = Signal(int, int)
    error = Signal(str)
    log_event = Signal(str)

    def __init__(self, port_name, inputs, parent=None):
        super().__init__(parent)
        self.port_name = port_name
        self._inputs = inputs
        self._inputs_lock = Lock()
        self._stop_requested = False

    def set_inputs(self, inputs):
        if inputs is not None:
            encode_driver_input(0, inputs)  # validate the complete snapshot before publishing it
        with self._inputs_lock:
            self._inputs = inputs

    def request_stop(self):
        self._stop_requested = True

    def run(self):
        try:
            try:
                import serial
            except ImportError:
                self.error.emit('pyserial is missing; install with pip install -e ".[gui,uart]".')
                return
            with serial.Serial(self.port_name, BAUD_RATE, timeout=0.02, write_timeout=0.5) as port:
                opened = f"OPEN {self.port_name} · {BAUD_RATE} 8N1 · TX 100 ms"
                self.status.emit(opened)
                self.log_event.emit(opened)
                sequence = 0
                started_at = monotonic()
                next_send = started_at
                last_ack = None
                ack_missing_reported = False
                pending = {}
                rx = bytearray()
                while not self._stop_requested:
                    now = monotonic()
                    if now >= next_send:
                        with self._inputs_lock:
                            inputs = self._inputs
                        if inputs is not None:
                            packet = encode_driver_input(sequence, inputs)
                            written = port.write(packet)
                            if written != len(packet):
                                raise OSError(f"short UART write: {written}/{len(packet)} bytes")
                            self.log_event.emit(
                                f"TX #{sequence} ({written} bytes): {packet.hex(' ').upper()}"
                            )
                            pending[sequence] = now
                            if len(pending) > 64:
                                pending.pop(next(iter(pending)))
                            sequence = (sequence + 1) & 0xFFFF
                        next_send = now + SEND_PERIOD_S
                    chunk = port.read(max(1, min(port.in_waiting, 64)))
                    if chunk:
                        rx.extend(chunk)
                    while True:
                        start = rx.find(SYNC)
                        if start < 0:
                            keep = 1 if rx and rx[-1] == SYNC[0] else 0
                            if keep:
                                rx[:] = rx[-1:]
                            else:
                                rx.clear()
                            break
                        if start:
                            del rx[:start]
                        if len(rx) < ACK_SIZE:
                            break
                        candidate = bytes(rx[:ACK_SIZE])
                        try:
                            ack_sequence, ack_status = decode_ack(candidate)
                        except ValueError:
                            del rx[0]
                            continue
                        del rx[:ACK_SIZE]
                        if ack_sequence in pending:
                            pending.pop(ack_sequence, None)
                            last_ack = monotonic()
                            ack_missing_reported = False
                            ack_text = f"RX ACK #{ack_sequence}: {ACK_STATUS.get(ack_status, 'unknown status')}"
                            self.acknowledgement.emit(ack_sequence, ack_status)
                            self.status.emit(
                                f"VCU ACK #{ack_sequence}: {ACK_STATUS.get(ack_status, 'unknown status')}"
                            )
                            self.log_event.emit(ack_text)
                    now = monotonic()
                    ack_deadline = (last_ack + ACK_TIMEOUT_S) if last_ack is not None else (started_at + 1.0)
                    if pending and now >= ack_deadline:
                        if not ack_missing_reported:
                            missing = "NO ACK · check UART port, cable, firmware, and RX/TX path"
                            self.status.emit("No VCU ACK · check UART port, cable, firmware, and RX/TX path")
                            self.log_event.emit(missing)
                            ack_missing_reported = True
        except Exception as exc:
            message = f"UART failed ({type(exc).__name__}): {exc}"
            self.error.emit(message)
            self.log_event.emit(f"ERROR {message}")
        finally:
            self.status.emit("UART disconnected")
            self.log_event.emit("CLOSED")
