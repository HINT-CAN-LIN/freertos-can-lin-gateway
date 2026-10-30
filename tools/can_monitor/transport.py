"""Single CAN bus owner: RX/logging and optional PC input transmission."""
import csv
from datetime import datetime, timezone
from pathlib import Path
import queue
import threading
import time
from protocol import demo_frames


def prepare_usb():
    # Optional bundled 64-bit libusb runtime; do not modify OS device drivers.
    import os
    folder = Path(__file__).parent / 'usb'
    if folder.exists():
        os.environ['PATH'] = str(folder) + os.pathsep + os.environ.get('PATH', '')


def open_bus(backend, channel):
    import can
    if backend == 'gs_usb':
        prepare_usb()
        return can.Bus(interface='gs_usb', channel=int(channel), index=int(channel),
                       bitrate=500000, ignore_config=True)
    if backend == 'slcan':
        if not channel.strip():
            raise ValueError('SLCAN COM port is required (for example COM5).')
        return can.Bus(interface='slcan', channel=channel.strip(), bitrate=500000,
                       ignore_config=True)
    raise ValueError('Unsupported CAN backend')


class Receiver:
    def __init__(self, backend, channel, log_dir):
        self.backend, self.channel = backend, channel
        self.log_dir = Path(log_dir)
        self.frames = queue.Queue(maxsize=4096)
        self.events = queue.SimpleQueue()
        self.stop_event = threading.Event()
        self.drops = 0
        self.control = None
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self.stop_event.set()

    def publish(self, identifier, data, now, flags):
        try:
            self.frames.put_nowait((identifier, bytes(data), now, flags))
        except queue.Full:
            self.drops += 1

    def run(self):
        bus = None
        try:
            if self.backend == 'demo':
                self.events.put(('connected', 'DEMO / synthetic data — no CAN device'))
                step = 0
                while not self.stop_event.is_set():
                    now = time.monotonic()
                    for identifier, data in demo_frames(step):
                        self.publish(identifier, data, now, {})
                    step += 1
                    self.stop_event.wait(0.010)
                return
            bus = open_bus(self.backend, self.channel)
            self.log_dir.mkdir(parents=True, exist_ok=True)
            path = self.log_dir / (datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.csv')
            with path.open('x', newline='', encoding='utf-8') as stream:
                writer = csv.writer(stream)
                writer.writerow(['utc', 'bus_timestamp', 'id_hex', 'extended', 'remote', 'error', 'fd', 'dlc', 'data_hex', 'direction'])
                def log_tx(data,now):
                    writer.writerow([datetime.now(timezone.utc).isoformat(), '', '200', 0,0,0,0,8,data.hex(' ').upper(),'TX'])
                    self.publish(0x200,data,now,{})
                if self.control: self.control.on_tx=log_tx
                self.events.put(('connected', f'LIVE CAN / {self.backend} / {self.channel} / 500 kbps'))
                self.events.put(('log', str(path)))
                last_flush = time.monotonic()
                while not self.stop_event.is_set():
                    if self.control: self.control.service(bus,time.monotonic())
                    message = bus.recv(timeout=0.010)
                    now = time.monotonic()
                    if message is not None:
                        if self.control: self.control.receive(message)
                        flags = dict(extended=message.is_extended_id, remote=message.is_remote_frame,
                                     error=message.is_error_frame, fd=message.is_fd)
                        writer.writerow([datetime.now(timezone.utc).isoformat(), message.timestamp,
                                         f'{message.arbitration_id:X}', *map(int, flags.values()),
                                         message.dlc, bytes(message.data).hex(' ').upper(),'RX'])
                        self.publish(message.arbitration_id, message.data, now, flags)
                    if now-last_flush >= 0.25:
                        stream.flush()
                        last_flush = now
        except Exception as exc:
            self.events.put(('error', f'{type(exc).__name__}: {exc}'))
        finally:
            if bus is not None:
                if self.control:
                    self.control.on_tx=None
                    try: self.control.shutdown(bus)
                    except Exception as exc: self.events.put(('error', f'CAN stop unconfirmed: {exc}'))
                try:
                    bus.shutdown()
                except Exception as exc:
                    self.events.put(('error', f'CAN close: {exc}'))
            self.events.put(('stopped', 'Receiver stopped'))
