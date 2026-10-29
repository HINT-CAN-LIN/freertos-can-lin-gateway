"""Qt 독립 Vehicle 모델 검증. 기존 TEST ONLY fixture만 사용한다."""
from dataclasses import replace
from copy import deepcopy

import pytest
from pc_diagnostic.dbc_loader import DbcLoader, DbcLookupError
from pc_diagnostic.gui.decode_session import DecodeSession
from pc_diagnostic.gui.demo import make_demo_frame
from pc_diagnostic.gui.vehicle_status import (DISPLAY_ITEMS, SignalMapping,
                                             VehicleState, VehicleStatusModel)

ITEM = "DBC Observation"


@pytest.fixture
def session(synthetic_dbc_path):
    # 각 테스트는 명시적 TEST ONLY DBC 세션을 사용한다.
    return_session = DecodeSession()
    return_session.load(synthetic_dbc_path)
    return return_session


def binding(message="TestOnlySample", signal="Measurement", channel="DEMO/TEST ONLY", *, confirmed=True, selected=True):
    # 테스트용 정확한 출처를 제공하며 Vehicle 후보와 자동 연결하지 않는다.
    return SignalMapping(message, signal, channel, selected, confirmed)


def test_no_dbc_and_no_default_mapping():
    # DBC 없는 값은 No Data이며 상태는 No DBC로 구분한다.
    model = VehicleStatusModel()
    session = DecodeSession()
    assert not model.mappings
    assert all(model.observe(item, session, now=1).state is VehicleState.NO_DBC for item in DISPLAY_ITEMS)


def test_loader_metadata_snapshot_and_unloaded_contract(session):
    # 새 API는 기존 읽기 전용 Message lookup을 tuple로 열거할 뿐이다.
    messages = session.loader.get_messages()
    assert isinstance(messages, tuple) and len(messages) == session.loader.status.message_count
    assert messages[0] is session.loader.get_message_by_name(messages[0].name)
    with pytest.raises(DbcLookupError):
        DbcLoader().get_messages()


def test_loaded_unmapped_is_ambiguous_and_explicit_unreceived_is_no_data(session):
    # 정의의 존재만으로 후보를 자동 연결하지 않는다.
    model = VehicleStatusModel()
    assert model.observe(ITEM, session, now=1).state is VehicleState.AMBIGUOUS
    model.bind(ITEM, binding(), session)
    result = model.observe(ITEM, session, now=1)
    assert result.state is VehicleState.NO_DATA and result.value is None and result.unit == "test_unit"


@pytest.mark.parametrize("message,signal", [
    ("missing", "Measurement"), ("TestOnlySample", "missing"),
    ("TestOnlySample", "measurement"), ("testonlysample", "Measurement"),
])
def test_missing_or_similar_name_is_not_defined(session, message, signal):
    # 대소문자/유사 이름으로 연결하지 않는다.
    model = VehicleStatusModel()
    model.bind(ITEM, binding(message, signal), session)
    assert model.observe(ITEM, session, now=1).state is VehicleState.NOT_DEFINED


@pytest.mark.parametrize("message,confirmed,selected", [(None, True, True), ("TestOnlySample", False, True), ("TestOnlySample", True, False)])
def test_partial_or_unconfirmed_mapping_is_ambiguous(session, message, confirmed, selected):
    # 이름이 하나뿐이어도 Message/Channel/의미 확인을 생략하지 않는다.
    model = VehicleStatusModel()
    model.bind(ITEM, binding(message, confirmed=confirmed, selected=selected), session)
    assert model.observe(ITEM, session, now=1).state is VehicleState.AMBIGUOUS


def test_duplicate_signal_requires_explicit_message(session, monkeypatch):
    # 메모리의 TEST ONLY metadata 사본으로 중복을 모의하며 파일/원본 정의는 수정하지 않는다.
    original = session.loader.get_messages()
    extended = deepcopy(session.loader.get_message_by_name("TestOnlyExtended"))
    extended.signals[0].name = "Measurement"
    monkeypatch.setattr(session.loader, "get_messages", lambda: (original[0], extended))
    model = VehicleStatusModel()
    model.bind(ITEM, binding(None), session)
    result = model.observe(ITEM, session, now=1)
    assert result.state is VehicleState.AMBIGUOUS and "2 message" in result.detail
    model.bind(ITEM, binding(), session)
    assert model.observe(ITEM, session, now=1).state is VehicleState.NO_DATA


def test_cache_only_value_unit_timestamp_and_repeat(session, dbc_codec, monkeypatch):
    # 모델 조회는 Codec을 호출하지 않으며 새 RX Cache snapshot만 반영한다.
    model = VehicleStatusModel()
    model.bind(ITEM, binding(), session)
    first = replace(make_demo_frame(0), timestamp=10)
    session.process(first)
    result = model.observe(ITEM, session, now=12)
    assert (result.value, result.unit, result.timestamp, result.age) == (-10.0, "test_unit", 10, 2)
    second = replace(dbc_codec.encode("TestOnlySample", {"Measurement": 0, "Mode": 1, "Counter": 7}),
                     timestamp=20, channel=first.channel, is_rx=True)
    session.process(second)
    def unexpected_decode(frame):
        # 기존 Cache 읽기에 Decode가 발생하면 테스트가 실패한다.
        pytest.fail("Vehicle view must not decode")
    monkeypatch.setattr(session.service.codec, "decode", unexpected_decode)
    result = model.observe(ITEM, session, now=22)
    assert result.state is VehicleState.VALID and result.value == 0.0 and result.timestamp == 20


@pytest.mark.parametrize("channel", [None, 0, "0", "A"])
def test_channel_identity_is_preserved(session, channel):
    # 같은 신호도 channel 타입/값별로 분리하며 None은 명시적 unknown channel이다.
    model = VehicleStatusModel()
    session.process(replace(make_demo_frame(0), timestamp=10, channel=channel))
    model.bind(ITEM, binding(channel=channel), session)
    assert model.observe(ITEM, session, now=11).state is VehicleState.VALID
    other = "0" if channel == 0 and type(channel) is int else "other"
    model.bind(ITEM, binding(channel=other), session)
    assert model.observe(ITEM, session, now=11).state is VehicleState.NO_DATA


def test_same_name_messages_remain_separate(session):
    # 기존 TEST ONLY 객체를 테스트 내부에서만 바꿔 같은 이름의 두 Message를 검증한다.
    definition = session.loader.get_message_by_name("TestOnlyExtended")
    definition.signals[0].name = "Measurement"
    definition.refresh()
    session.process(replace(make_demo_frame(0), timestamp=10))
    session.process(replace(make_demo_frame(1), timestamp=20))
    model = VehicleStatusModel()
    model.bind(ITEM, binding(), session)
    assert model.observe(ITEM, session, now=21).value == -10.0
    model.bind(ITEM, binding("TestOnlyExtended"), session)
    assert model.observe(ITEM, session, now=21).value == 515


@pytest.mark.parametrize("failure", ["length", "codec", "application"])
def test_latest_decode_failure_preserves_last_success(session, monkeypatch, failure):
    # 실패 상태와 정상 Cache 값/시각을 동시에 보여준다.
    model = VehicleStatusModel()
    model.bind(ITEM, binding(), session)
    frame = replace(make_demo_frame(0), timestamp=10)
    session.process(frame)
    bad = replace(frame, timestamp=20)
    if failure == "length":
        bad = replace(bad, data=bytes(3), dlc=3)
    else:
        def fail(*args, **kwargs):
            # 숨김/가짜 값 대신 오류 관찰을 만들도록 실제 실패 경로에 주입한다.
            raise RuntimeError("TEST ONLY failure")
        target = session.service if failure == "application" else session.loader.get_message_by_name("TestOnlySample")
        monkeypatch.setattr(target, "process" if failure == "application" else "decode", fail)
    session.process(bad)
    result = model.observe(ITEM, session, now=22)
    assert result.state is VehicleState.DECODE_ERROR and result.detail
    assert (result.value, result.timestamp, result.age) == (-10.0, 10, 12)


@pytest.mark.parametrize("timestamp,now,age", [(10, 12, 2), (None, 12, None), (14, 12, None), (10, 1000000, 999990)])
def test_age_without_timeout_or_value_deletion(session, timestamp, now, age):
    # 오래된 값/미제공/역행 시각을 ECU Health로 변환하지 않는다.
    model = VehicleStatusModel()
    model.bind(ITEM, binding(), session)
    session.process(replace(make_demo_frame(0), timestamp=timestamp))
    result = model.observe(ITEM, session, now=now)
    assert result.state is VehicleState.VALID and result.value == -10.0 and result.age == age


def test_reload_failure_and_success_clear_mapping(session, synthetic_dbc_path, tmp_path):
    # 새 DBC 세션에서 이전 데이터/연결을 현재 차량 상태로 오인하지 않는다.
    model = VehicleStatusModel()
    model.bind(ITEM, binding(), session)
    session.process(make_demo_frame(0))
    session.load(synthetic_dbc_path)
    assert model.observe(ITEM, session, now=1).state is VehicleState.AMBIGUOUS
    assert not model.mappings and not session.service.cache.snapshot()
    model.bind(ITEM, binding(), session)
    with pytest.raises(ValueError):
        session.load(tmp_path / "missing.dbc")
    assert model.observe(ITEM, session, now=1).state is VehicleState.NO_DBC
    assert not model.mappings


def test_tx_does_not_supply_a_vehicle_rx_value(session):
    # 해석 가능한 TX라도 Vehicle 수신값을 새로 만들지 않는다.
    model = VehicleStatusModel()
    model.bind(ITEM, binding(), session)
    session.process(replace(make_demo_frame(0), is_rx=False))
    result = model.observe(ITEM, session, now=1)
    assert result.state is VehicleState.NO_DATA and "TX" in result.detail
