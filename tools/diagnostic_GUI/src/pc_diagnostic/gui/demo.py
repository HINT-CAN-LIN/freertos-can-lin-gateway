"""기존 합성 test_only.dbc/test_dbc_codec.py 예제만 재사용한다."""
from time import time
from ..frame import RawCanFrame

# 기존 TEST ONLY fixture ID이며 공식 ECU ID 또는 Signal 정의가 아니다.
TEST_ONLY_ID = 1617
TEST_ONLY_PAYLOADS = (bytes.fromhex("28 00 01 07"), bytes.fromhex("01 01"))


def make_demo_frame(index):
    # STD/EXT 구분과 payload는 기존 codec 회귀 테스트 예제를 그대로 사용한다.
    extended = bool(index % len(TEST_ONLY_PAYLOADS))
    return RawCanFrame(TEST_ONLY_ID, TEST_ONLY_PAYLOADS[int(extended)],
                       is_extended_id=extended, timestamp=time(), channel="DEMO/TEST ONLY")
