"""Qt 독립 관측/통계 검증. 기존 TEST ONLY fixture/vector만 사용한다."""
from dataclasses import replace
from copy import deepcopy
import pytest
from pc_diagnostic.frame import RawCanFrame
from pc_diagnostic.gui.decode_session import DecodeSession
from pc_diagnostic.gui.demo import make_demo_frame
from pc_diagnostic.gui.ecu_observation import ECU_NAMES, EcuObservationModel, MessageMapping
from pc_diagnostic.gui.message_statistics import MessageKey, MessageStatisticsStore, observation_age


@pytest.fixture
def session(synthetic_dbc_path):
    # 각 사례의 DBC/Cache는 독립이다.
    value = DecodeSession()
    value.load(synthetic_dbc_path)
    return value


def mapping(session, *, message="TestOnlySample", channel="DEMO/TEST ONLY", signal=None):
    # 실제 fixture Message metadata에서 ID/format을 얻으며 새 Interface를 정의하지 않는다.
    definition = session.loader.get_message_by_name(message)
    return MessageMapping(message, channel, definition.frame_id, definition.is_extended_frame, True, True, signal)


def receive(model, session, frame=None):
    # 실제 기존 DecodeSession 결과를 전달하며 GUI 모델의 decode 중복을 방지한다.
    frame = make_demo_frame(0) if frame is None else frame
    observation = session.process(frame)
    model.record(observation, session)
    return observation


def test_no_default_mapping_for_all_seven_and_raw_without_dbc():
    # DBC 없이 Raw 통계만 제공하며 ECU/송신자 연결을 추론하지 않는다.
    session = DecodeSession()
    model = EcuObservationModel()
    assert len(ECU_NAMES) == 7
    assert all(model.observe(ecu, session, now=1).state == "Not Configured" for ecu in ECU_NAMES)
    receive(model, session)
    assert model.statistics.processed_rx == 1 and not model.mappings
    assert model.statistics.snapshot()[0].latest.decoded is None


def test_explicit_unreceived_and_repeated_rx_counts_time_age(session):
    # 같은 ID 반복 수신은 Count를 올리고 최신 도착 순서의 시각을 사용한다.
    model = EcuObservationModel()
    model.bind("VCU", mapping(session), session)
    assert model.observe("VCU", session, now=10).state == "No Data"
    for stamp in (10, 20, 15):
        receive(model, session, replace(make_demo_frame(0), timestamp=stamp))
    result = model.observe("VCU", session, now=18)
    assert (result.state, result.count, result.timestamp, result.age) == ("Observed", 3, 15, 3)
    stat = model.statistics.snapshot()[0]
    assert (stat.first_seen, stat.last_seen, stat.dlc) == (10, 15, 4)
    assert "Health" in result.detail


@pytest.mark.parametrize("channel", [None, 0, "0", "A", "B"])
def test_channel_and_frame_format_exact_separation(session, channel):
    # 타입까지 다른 Channel/STD/EXT를 독립 통계와 매핑으로 조회한다.
    model = EcuObservationModel()
    receive(model, session, replace(make_demo_frame(0), channel=channel, timestamp=10))
    receive(model, session, replace(make_demo_frame(1), channel=channel, timestamp=20))
    receive(model, session, replace(make_demo_frame(0), channel="other", timestamp=30))
    assert len(model.statistics.entries) == 3
    model.bind("Motor", mapping(session, channel=channel), session)
    assert model.observe("Motor", session, now=31).timestamp == 10
    model.bind("Motor", mapping(session, message="TestOnlyExtended", channel=channel), session)
    assert model.observe("Motor", session, now=31).timestamp == 20


def test_error_rtr_tx_not_mixed_with_data_rx(session):
    # Backend 오류 mask/RTR/송신을 정상 data RX 또는 ECU 근거로 섞지 않는다.
    model = EcuObservationModel()
    good = replace(make_demo_frame(0), timestamp=10)
    receive(model, session, good)
    receive(model, session, replace(good, data=b"", dlc=4, is_remote_frame=True))
    receive(model, session, replace(good, is_error_frame=True))
    receive(model, session, replace(good, timestamp=20, is_rx=False))
    assert len(model.statistics.entries) == 3
    assert model.statistics.processed_rx == 3 and model.statistics.ignored_tx == 1
    model.bind("Gateway", mapping(session), session)
    assert model.observe("Gateway", session, now=30).count == 1
    assert model.observe("Gateway", session, now=30).timestamp == 10


@pytest.mark.parametrize("change,state", [
    ({"source_confirmed": False}, "Ambiguous"), ({"channel_selected": False}, "Ambiguous"),
    ({"message_name": None}, "Ambiguous"), ({"message_name": "missing"}, "Not Defined"),
    ({"arbitration_id": 0x7FE}, "Ambiguous"), ({"is_extended_id": True}, "Ambiguous"),
    ({"signal_name": "missing"}, "Not Defined"),
])
def test_invalid_mapping_never_infers_source(session, change, state):
    # 불완전하거나 DBC와 다른 식별자는 수신 여부와 무관하게 거부한다.
    model = EcuObservationModel()
    receive(model, session)
    model.bind("Gateway", replace(mapping(session), **change), session)
    assert model.observe("Gateway", session, now=10).state == state


def test_duplicate_mapping_is_visible_on_both_ecus_and_removal_recovers(session):
    # 같은 출처를 서로 다른 ECU의 독립 증거로 사용하지 않는다.
    model = EcuObservationModel()
    receive(model, session)
    for ecu in ("Gateway", "VCU"):
        model.bind(ecu, mapping(session), session)
    for ecu in ("Gateway", "VCU"):
        result = model.observe(ecu, session, now=10)
        assert result.state == "Ambiguous" and "Same source" in result.detail
    model.mappings.pop("VCU")
    assert model.observe("Gateway", session, now=10).state == "Observed"


@pytest.mark.parametrize("ecu", ["Door", "Light", "Window"])
def test_lin_requires_individual_signal_not_whole_can_message(session, ecu):
    # LIN 경유 표시는 TEST ONLY에서도 개별 Signal 출처 확인을 요구한다.
    model = EcuObservationModel()
    receive(model, session)
    model.bind(ecu, mapping(session), session)
    assert model.observe(ecu, session, now=10).state == "Not Available"
    model.bind(ecu, mapping(session, signal="Measurement"), session)
    result = model.observe(ecu, session, now=10)
    assert result.state == "Observed" and result.signal_value == -10
    assert "LIN reception" in result.detail


def test_individual_mux_absence_is_no_data(session):
    # 같은 Message 수신만으로 비활성 mux의 개별 Signal을 수신했다고 표시하지 않는다.
    model = EcuObservationModel()
    bind = mapping(session, message="TestOnlyMux", signal="BranchOne")
    model.bind("Door", bind, session)
    frame = session.service.codec.encode("TestOnlyMux", {"Selector": 0, "BranchZero": 7})
    receive(model, session, replace(frame, is_rx=True, channel=bind.channel, timestamp=10))
    assert model.observe("Door", session, now=11).state == "No Data"


def test_decode_failure_and_recovery_preserve_fault_last_good(session):
    # Fault 표시용 선택도 일반 TEST ONLY Message이며 고장 Code/의미를 새로 만들지 않는다.
    model = EcuObservationModel()
    model.bind_fault(mapping(session), session)
    assert model.fault_observation(session, now=1)[0].state == "No Data"
    good = replace(make_demo_frame(0), timestamp=10)
    receive(model, session, good)
    receive(model, session, replace(good, timestamp=20, data=bytes(3), dlc=3))
    result, definition, last_good = model.fault_observation(session, now=21)
    assert result.state == "Decode Error" and result.timestamp == 20 and result.count == 2
    assert last_good.frame.timestamp == 10 and last_good.decoded.signals["Measurement"] == -10
    assert definition.name == "TestOnlySample"
    receive(model, session, replace(good, timestamp=30))
    assert model.fault_observation(session, now=31)[0].state == "Observed"


def test_processing_error_remains_visible(session, monkeypatch):
    # 서비스 예외도 Raw 통계 보존 및 Decode Error의 근거이다.
    model = EcuObservationModel()
    model.bind("VCU", mapping(session), session)
    def fail(frame):
        # 모의 application 실패이며 Hardware Fault 정책과 무관하다.
        raise RuntimeError("test-only processing failure")
    monkeypatch.setattr(session.service, "process", fail)
    receive(model, session)
    result = model.observe("VCU", session, now=1)
    assert result.state == "Decode Error" and "RuntimeError" in result.detail


def test_clear_and_reload_success_failure_and_old_session(session, synthetic_dbc_path, tmp_path):
    # Clear는 사용자 연결만 보존, Reload는 실패를 포함해 새 관측 구간이다.
    model = EcuObservationModel()
    model.bind("VCU", mapping(session), session)
    old = receive(model, session)
    cached = session.service.cache.snapshot()
    model.statistics.clear()
    assert model.observe("VCU", session, now=1).state == "No Data"
    assert model.mappings and session.service.cache.snapshot() == cached
    session.load(synthetic_dbc_path)
    model.sync_session(session)
    assert not model.mappings and not model.statistics.entries
    model.record(old, session)
    assert not model.statistics.entries
    model.bind_fault(mapping(session), session)
    with pytest.raises(Exception):
        session.load(tmp_path / "missing.dbc")
    model.sync_session(session)
    assert not model.mappings and model.fault_mapping is None


@pytest.mark.parametrize("stamp,now,age", [(None, 10, None), (20, 10, None), (0, 5, 5), (1, 1e6, 999999)])
def test_age_not_health_or_clock_substitution(session, stamp, now, age):
    # 미시각/역행/오래된 수신은 Offline 기준이 아니다.
    model = EcuObservationModel()
    model.bind("VCU", mapping(session), session)
    receive(model, session, replace(make_demo_frame(0), timestamp=stamp))
    result = model.observe("VCU", session, now=now)
    assert result.state == "Observed" and result.age == age
    assert observation_age(stamp, now) == age


def test_unknown_id_without_fake_dbc_name(session):
    # 기존 Phase 3C unknown vector만 재사용한다.
    model = EcuObservationModel()
    receive(model, session, RawCanFrame(0x7FE, b"\xA5", timestamp=42))
    entry = model.statistics.snapshot()[0]
    assert entry.latest.message_name is None and entry.count == 1
    assert entry.latest.decoded.decode_status.value == "unknown"


def test_finite_statistics_preserve_existing_counts_and_report_exclusions(session):
    # ID를 늘리지 않고 TEST ONLY Channel만 바꾸어 저장 상한을 검증한다.
    model = EcuObservationModel(capacity=2)
    for channel in ("A", "B", "C", "C", "A"):
        receive(model, session, replace(make_demo_frame(0), channel=channel))
    stats = model.statistics
    assert len(stats.entries) == 2 and stats.processed_rx == 5 and stats.capacity_excluded == 2
    assert stats.get(MessageKey.from_frame(replace(make_demo_frame(0), channel="A"))).count == 2
    model.bind("VCU", mapping(session, channel="C"), session)
    assert "exclusions" in model.observe("VCU", session, now=1).detail


@pytest.mark.parametrize("capacity", [0, -1, 1.5, True])
def test_capacity_validation(capacity):
    # 통계 설정 오류는 생성 시점에 검출한다.
    with pytest.raises(ValueError):
        MessageStatisticsStore(capacity)


def test_duplicate_signal_definition_is_ambiguous(session, monkeypatch):
    # metadata 사본의 모호성을 검사하며 공식 DBC나 fixture를 수정하지 않는다.
    message = deepcopy(session.loader.get_message_by_name("TestOnlySample"))
    message.signals.append(deepcopy(message.signals[0]))
    monkeypatch.setattr(session.loader, "get_message_by_name", lambda name: message)
    model = EcuObservationModel()
    model.bind("Door", mapping(session, signal="Measurement"), session)
    assert model.observe("Door", session, now=1).state == "Ambiguous"
