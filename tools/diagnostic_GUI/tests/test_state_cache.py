from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest

from pc_diagnostic import DecodedMessage, DecodeStatus, RawCanFrame, SignalStateCache


def observation(timestamp=1.0, value=0, channel=None, name="TestOnlySample", is_rx=True):
    return DecodedMessage(RawCanFrame(1617, timestamp=timestamp, channel=channel, is_rx=is_rx),
                          name, DecodeStatus.DECODED, {"TestOnlyValue": value})


def test_latest_signal_message_timestamp_and_age():
    cache = SignalStateCache()
    assert not cache.has_received("TestOnlySample")
    assert cache.get_signal("TestOnlySample", "TestOnlyValue") is None
    assert cache.age("TestOnlySample", now=10) is None
    first = observation(1, 0)
    assert cache.update(first)
    old_snapshot = cache.snapshot()
    assert cache.has_received("TestOnlySample")
    assert cache.get_signal("TestOnlySample", "TestOnlyValue") == 0
    latest = observation(5, 42)
    cache.update(latest)
    assert cache.get_message("TestOnlySample") is latest
    assert cache.last_timestamp("TestOnlySample") == 5
    assert cache.age("TestOnlySample", now=7) == 2
    assert old_snapshot[(None, "TestOnlySample")] is first
    with pytest.raises(TypeError):
        old_snapshot[(None, "TestOnlySample")] = latest
    state = cache.get_signal_state("TestOnlySample", "TestOnlyValue")
    assert state.value == 42 and state.timestamp == 5 and state.arbitration_id == 1617


def test_message_and_channel_isolation():
    cache = SignalStateCache()
    for name, channel, value in [("TestOnlySample", "A", 1), ("TestOnlySample", "B", 2),
                                  ("TestOnlyOther", "A", 3)]:
        cache.update(observation(value=value, channel=channel, name=name))
    assert cache.get_signal("TestOnlySample", "TestOnlyValue", channel="A") == 1
    assert cache.get_signal("TestOnlySample", "TestOnlyValue", channel="B") == 2
    assert cache.get_signal("TestOnlyOther", "TestOnlyValue", channel="A") == 3
    assert cache.get_message("TestOnlySample") is None


@pytest.mark.parametrize("status", [DecodeStatus.UNKNOWN, DecodeStatus.INVALID])
def test_failed_decode_does_not_overwrite_value_or_time(status):
    cache = SignalStateCache()
    valid = observation(1, 42)
    cache.update(valid)
    failure = DecodedMessage(RawCanFrame(1617, timestamp=5), "TestOnlySample", status, error="test-only")
    assert not cache.update(failure)
    assert cache.get_message("TestOnlySample") is valid
    assert cache.last_timestamp("TestOnlySample") == 1


def test_tx_does_not_claim_received():
    cache = SignalStateCache()
    assert not cache.update(observation(is_rx=False))
    assert not cache.has_received("TestOnlySample")


def test_missing_timestamp_and_backwards_clock_are_not_health_verdicts():
    cache = SignalStateCache()
    cache.update(observation(timestamp=None))
    assert cache.has_received("TestOnlySample")
    assert cache.age("TestOnlySample", now=10) is None
    cache.update(observation(timestamp=10))
    assert cache.age("TestOnlySample", now=5) is None
    assert cache.age("TestOnlySample", now=10) == 0


@pytest.mark.parametrize("now", [-1, float("nan"), float("inf"), True])
def test_invalid_age_input(now):
    with pytest.raises(ValueError):
        SignalStateCache().age("TestOnlySample", now=now)


def test_clear_and_no_stale_mux_signals(dbc_codec):
    cache = SignalStateCache()
    for values in [{"Selector": 0, "BranchZero": 5}, {"Selector": 1, "BranchOne": 8}]:
        tx = dbc_codec.encode("TestOnlyMux", values)
        cache.update(dbc_codec.decode(replace(tx, is_rx=True)))
    assert cache.get_signal("TestOnlyMux", "BranchZero") is None
    assert cache.get_signal("TestOnlyMux", "BranchOne") == 8
    cache.clear()
    assert not cache.has_received("TestOnlyMux") and not cache.snapshot()


def test_model_copies_caller_signal_dictionary():
    values = {"TestOnlyValue": 5}
    result = DecodedMessage(RawCanFrame(1617), "TestOnlySample", DecodeStatus.DECODED, values)
    values["TestOnlyValue"] = 8
    assert result.signals["TestOnlyValue"] == 5


def test_latest_is_arrival_order_not_clock_sorting():
    cache = SignalStateCache()
    cache.update(observation(10, 1))
    cache.update(observation(5, 2))
    assert cache.last_timestamp("TestOnlySample") == 5
    assert cache.get_signal("TestOnlySample", "TestOnlyValue") == 2


def test_concurrent_snapshots_keep_values_and_timestamp_together():
    cache = SignalStateCache()

    def writer():
        for n in range(300):
            cache.update(observation(timestamp=n, value=n))

    def reader():
        for _ in range(300):
            for message in cache.snapshot().values():
                assert message.signals["TestOnlyValue"] == message.timestamp

    with ThreadPoolExecutor(max_workers=3) as executor:
        jobs = [executor.submit(writer), executor.submit(reader), executor.submit(reader)]
        for job in jobs:
            job.result(timeout=5)
