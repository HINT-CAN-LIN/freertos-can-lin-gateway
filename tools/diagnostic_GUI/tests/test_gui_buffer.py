"""Qt 설치 없이 검증하는 GUI 표시 버퍼 테스트."""
import pytest
from pc_diagnostic.gui.buffer import FrameBuffer
from pc_diagnostic.gui.demo import make_demo_frame


def test_buffer_overflow_is_bounded_and_counted():
    # 버퍼 용량을 넘겨도 가장 최근 프레임만 보존하고 제외 수를 알린다.
    buffer = FrameBuffer(capacity=3)
    frames = [make_demo_frame(i) for i in range(10)]
    for frame in frames:
        buffer.append(frame)
    first, total, dropped = buffer.drain(2)
    assert first == frames[-3:-1]
    assert (total, dropped) == (10, 7)
    assert buffer.drain(2)[0] == frames[-1:]
    assert buffer.drain(2)[0] == []
    buffer.clear()
    assert buffer.drain() == ([], 0, 0)


@pytest.mark.parametrize("capacity", [0, -1, True, 1.5])
def test_invalid_capacity_is_rejected(capacity):
    # 무한/빈 버퍼로 잘못 설정되는 것을 방지한다.
    with pytest.raises(ValueError):
        FrameBuffer(capacity)


@pytest.mark.parametrize("limit", [0, -1, True, 1.5])
def test_invalid_drain_limit_is_rejected(limit):
    # 표시 batch 설정 오류를 조기에 보고한다.
    with pytest.raises(ValueError):
        FrameBuffer().drain(limit)


def test_demo_uses_existing_test_only_raw_examples():
    # 기존 합성 fixture 값만 사용하며 실제 ECU 의미를 부여하지 않는다.
    standard, extended = make_demo_frame(0), make_demo_frame(1)
    assert standard.arbitration_id == extended.arbitration_id == 1617
    assert standard.data == bytes.fromhex("28 00 01 07")
    assert extended.data == bytes.fromhex("01 01")
    assert not standard.is_extended_id and extended.is_extended_id
    assert standard.channel == extended.channel == "DEMO/TEST ONLY"
