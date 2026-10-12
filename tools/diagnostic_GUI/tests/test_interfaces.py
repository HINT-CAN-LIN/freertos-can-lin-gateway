from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from unittest.mock import Mock
from uuid import uuid4

import can
import pytest

from pc_diagnostic import CanInterfaceError, MockCanInterface, PythonCanInterface, RawCanFrame, RawCanSender


def test_mock_fifo_timeout_and_tx_separation():
    frames = [RawCanFrame(0, bytes([n])) for n in range(3)]
    with MockCanInterface(frames) as interface:
        assert [interface.recv(0) for _ in frames] == frames
        assert interface.recv(0.001) is None
        RawCanSender(interface).send(frames[0])
        assert interface.sent_frames == (replace(frames[0], is_rx=False),)
        assert interface.recv(0) is None
    interface.shutdown()
    for operation in (lambda: interface.recv(0), lambda: interface.send(frames[0]),
                      lambda: interface.inject(frames[0])):
        with pytest.raises(CanInterfaceError, match="closed"):
            operation()


def test_mock_loopback_and_wakeup():
    frame = RawCanFrame(0)
    with MockCanInterface(loopback=True) as interface:
        interface.send(frame)
        assert interface.recv(0) == replace(frame, is_rx=False)
        with ThreadPoolExecutor(max_workers=1) as executor:
            pending = executor.submit(interface.recv)
            interface.inject(frame)
            assert pending.result(timeout=1) == frame
            pending = executor.submit(interface.recv)
            interface.shutdown()
            with pytest.raises(CanInterfaceError, match="closed"):
                pending.result(timeout=1)


@pytest.mark.parametrize("timeout", [-1, float("nan"), float("inf"), True])
def test_invalid_timeout(timeout):
    with MockCanInterface() as interface:
        with pytest.raises(ValueError):
            interface.recv(timeout)
        with pytest.raises(ValueError):
            interface.send(RawCanFrame(0), timeout)


@pytest.mark.parametrize("extended,remote,length", [(False, False, 0), (False, False, 8),
                                                   (True, False, 3), (True, True, 8)])
def test_python_can_virtual_roundtrip(extended, remote, length):
    channel = "phase1-test-" + uuid4().hex
    with PythonCanInterface(interface="virtual", channel=channel) as tx:
        with PythonCanInterface(interface="virtual", channel=channel) as rx:
            frame = RawCanFrame(0x1FFFFFFF if extended else 0x7FF,
                                b"" if remote else bytes(range(length)), dlc=length,
                                is_extended_id=extended, is_remote_frame=remote)
            RawCanSender(tx).send(frame, timeout=0.1)
            actual = rx.recv(0.5)
            assert actual is not None
            assert actual.arbitration_id == frame.arbitration_id
            assert actual.data == frame.data
            assert actual.dlc == frame.dlc
            assert actual.is_extended_id == extended
            assert actual.is_remote_frame == remote
            assert actual.timestamp > 0
            assert actual.channel == channel
            assert actual.is_rx
            assert rx.recv(0) is None


def test_adapter_preserves_error_timestamp_channel():
    bus = Mock()
    bus.recv.return_value = can.Message(arbitration_id=0, data=[1, 2],
                                        is_error_frame=True, timestamp=42.125,
                                        channel=1, is_rx=False)
    with PythonCanInterface(bus=bus) as interface:
        frame = interface.recv(0)
        assert frame.is_error_frame and not frame.is_rx
        assert frame.timestamp == 42.125 and frame.channel == 1
        assert frame.data == b"\x01\x02"
    bus.shutdown.assert_called_once()


def test_adapter_failures_and_shutdown():
    bus = Mock()
    bus.recv.side_effect = can.CanOperationError("disconnected")
    bus.send.side_effect = can.CanOperationError("bus off")
    interface = PythonCanInterface(bus=bus)
    with pytest.raises(CanInterfaceError, match="receive failed"):
        interface.recv(0)
    with pytest.raises(CanInterfaceError, match="send failed"):
        interface.send(RawCanFrame(0))
    interface.shutdown()
    interface.shutdown()
    bus.shutdown.assert_called_once()
    with pytest.raises(CanInterfaceError, match="closed"):
        interface.recv(0)


@pytest.mark.parametrize("message", [
    can.Message(is_fd=True),
    can.Message(arbitration_id=0, data=[1], dlc=8),
])
def test_adapter_rejects_unsupported_received_frame(message):
    bus = Mock()
    bus.recv.return_value = message
    with PythonCanInterface(bus=bus) as interface:
        with pytest.raises(CanInterfaceError):
            interface.recv(0)


def test_no_implicit_hardware_configuration(monkeypatch):
    factory = Mock()
    monkeypatch.setattr(can, "Bus", factory)
    with pytest.raises(ValueError):
        PythonCanInterface(interface="pcan", channel="unused")
    factory.assert_not_called()
    factory.side_effect = can.CanInitializationError("missing device")
    with pytest.raises(CanInterfaceError, match="open failed"):
        PythonCanInterface(interface="virtual", channel="test-only")
    assert factory.call_args.kwargs["ignore_config"] is True


def test_sender_rejects_error_frame():
    with MockCanInterface() as interface:
        with pytest.raises(ValueError, match="capture-only"):
            RawCanSender(interface).send(RawCanFrame(0, is_error_frame=True))
        assert not interface.sent_frames
