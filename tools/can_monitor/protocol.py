"""Three-ECU base CAN layout; independent of GUI and transport."""
from dataclasses import dataclass
import math

NAMES = {0x200: 'PC_Input [TX]', 0x201: 'VCU_ACK [RX]', 0x100: 'VCU_Command', 0x110: 'Motor_Status', 0x120: 'Vehicle_Status',
         0x200: 'Body_Status', 0x300: 'Gateway_Status', 0x310: 'Fault_Status'}
GEARS = ('P', 'N', 'D', 'R')
STATES = ('OFF', 'READY', 'RUN', 'FAIL_SAFE')


def decode(identifier, data, *, extended=False, remote=False, error=False, fd=False):
    if extended or remote or error or fd or len(data) != 8:
        return None
    u16 = lambda offset: int.from_bytes(data[offset:offset+2], 'little')
    if identifier == 0x100:
        torque, gear = u16(0), data[2] & 7
        return dict(torque=torque/10 if torque <= 40000 else None,
                    gear=GEARS[gear] if gear < 4 else 'INVALID',
                    brake=bool(data[2] & 8), alive=data[2] >> 4)
    if identifier == 0x110:
        rpm, torque = u16(0), u16(2)
        return dict(rpm=rpm if rpm <= 12000 else None,
                    torque=torque/10 if torque <= 40000 else None,
                    state=STATES[data[4] & 3], alive=(data[4] >> 2) & 15)
    if identifier == 0x120:
        speed, rpm, gear = u16(0), u16(2), data[4] & 7
        return dict(speed=speed/10 if speed <= 2500 else None,
                    rpm=rpm if rpm <= 12000 else None,
                    gear=GEARS[gear] if gear < 4 else 'INVALID')
    return None


@dataclass
class Sample:
    timestamp: float
    data: bytes
    values: dict | None
    count: int = 1
    period_ms: float | None = None
    alive_gaps: int = 0


class Monitor:
    def __init__(self):
        self.samples = {}
        self.total = 0
        self.rejected = 0

    def accept(self, identifier, data, now, **flags):
        self.total += 1
        key = (identifier, bool(flags.get('extended')), bool(flags.get('remote')),
               bool(flags.get('error')), bool(flags.get('fd')))
        values = decode(identifier, data, **flags)
        old = self.samples.get(key)
        sample = Sample(now, bytes(data), values)
        if old:
            sample.count = old.count + 1
            sample.period_ms = max(0, (now-old.timestamp)*1000)
            sample.alive_gaps = old.alive_gaps
            if values and old.values and 'alive' in values and 'alive' in old.values:
                if now-old.timestamp <= 0.030 and values['alive'] != (old.values['alive']+1)%16:
                    sample.alive_gaps += 1
        if identifier in (0x100, 0x110, 0x120) and values is None:
            self.rejected += 1
        # Keep the UI cache bounded even under arbitrary extended-ID traffic.
        if key not in self.samples and len(self.samples) >= 512:
            del self.samples[min(self.samples, key=lambda k: self.samples[k].timestamp)]
        self.samples[key] = sample

    def sample(self, identifier):
        return self.samples.get((identifier, False, False, False, False))

    def fresh(self, identifier, now, limit=0.100):
        sample = self.sample(identifier)
        return sample.values if sample and now-sample.timestamp <= limit else None


def demo_frames(step):
    """Synthetic data for display testing only. Never sent to a CAN bus."""
    alive = step % 16
    torque = round((math.sin(step/160)+1)*4000)
    rpm = round(torque*0.3)
    command = torque.to_bytes(2, 'little') + bytes([(alive << 4) | 2]) + bytes(5)
    status = rpm.to_bytes(2, 'little') + torque.to_bytes(2, 'little') + bytes([(alive << 2) | 2]) + bytes(3)
    return ((0x100, command), (0x110, status))
