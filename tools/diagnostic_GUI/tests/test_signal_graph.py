"""Qt 독립 Graph sample/품질 정책. 기존 TEST ONLY DBC만 사용한다."""
from dataclasses import replace
from types import SimpleNamespace
import pytest
from pc_diagnostic.decoded_message import DecodeStatus
from pc_diagnostic.gui.decode_session import DecodeSession
from pc_diagnostic.gui.demo import make_demo_frame
from pc_diagnostic.gui.signal_graph import GraphSelection, SignalGraphModel, finite_number

SOURCE = "Mock / DEMO / TEST ONLY"


@pytest.fixture
def session(synthetic_dbc_path):
    # 생산 DBC를 기본으로 로드하지 않는 독립 시험 session이다.
    value = DecodeSession()
    value.load(synthetic_dbc_path)
    return value


def choose(session, model, *, channel="DEMO/TEST ONLY", name="Measurement", message="TestOnlySample", ext=False, can_id=1617):
    # 이름/ID/format/channel을 명시적으로 선택한다.
    selection = GraphSelection(channel, message, can_id, ext, name)
    assert model.bind(selection, session, SOURCE)
    return selection


def observe(session, stamp, *, index=0, channel="DEMO/TEST ONLY"):
    # timestamp는 시험자가 지정하며 제품에서 timestamp를 합성하지 않는다.
    return session.process(replace(make_demo_frame(index), timestamp=stamp, channel=channel))


def test_no_dbc_and_no_selection_have_no_samples(session):
    # 빈 session과 로드 후 미선택은 별도 상태이다.
    model = SignalGraphModel()
    empty = DecodeSession()
    model.sync_session(empty, SOURCE)
    assert model.state == "No DBC" and not model.samples
    assert not model.record(observe(session, 1), session, SOURCE)
    assert model.state == "No Data" and not model.samples


def test_numeric_value_unit_timestamp_and_provenance(session):
    # scale/unit은 기존 Decode 결과 그대로이며 sample에 Source/식별자를 보존한다.
    model = SignalGraphModel()
    choose(session, model)
    observation = observe(session, 10.5)
    assert model.record(observation, session, SOURCE)
    sample = model.samples[0]
    assert sample.value == -10.0 and sample.unit == "test_unit" and sample.timestamp == 10.5
    assert sample.source == SOURCE and sample.session_id == session.session_id
    assert sample.channel == "DEMO/TEST ONLY" and sample.arbitration_id == 1617
    assert sample.message_name == "TestOnlySample" and sample.signal_name == "Measurement" and not sample.is_extended_id
    assert model.accepted == 1 and model.state == "Data"


@pytest.mark.parametrize("other", [
    {"channel": "other"}, {"channel": 0}, {"index": 1},
])
def test_other_channel_and_format_do_not_mix(session, other):
    # 같은 숫자 ID의 STD/EXT도 독립 신호이다.
    model = SignalGraphModel()
    choose(session, model)
    assert not model.record(observe(session, 1, **other), session, SOURCE)
    assert not model.samples and model.accepted == 0


def test_typed_channel_none_and_integer_string_are_exact(session):
    # None은 wildcard가 아니며 0/'0'도 분리한다.
    for channel, other in [(0, "0"), (None, "DEMO/TEST ONLY")]:
        model = SignalGraphModel()
        choose(session, model, channel=channel)
        assert model.record(observe(session, 1, channel=channel), session, SOURCE)
        assert not model.record(observe(session, 2, channel=other), session, SOURCE)
        assert len(model.samples) == 1


def test_message_and_signal_selection_are_exact(session):
    # 존재하지 않는 Signal을 유사 이름으로 대체하지 않는다.
    model = SignalGraphModel()
    assert not model.bind(GraphSelection("DEMO/TEST ONLY", "TestOnlySample", 1617, False, "measurement"), session, SOURCE)
    assert model.state == "Not Defined"
    assert not model.bind(GraphSelection("DEMO/TEST ONLY", "TestOnlySample", 1617, True, "Measurement"), session, SOURCE)
    assert model.state == "Not Defined"


def test_numeric_enum_and_missing_unit_are_not_invented(session):
    # 기존 codec은 numeric enum을 반환한다. 문자열로 변환하거나 임의 단위를 넣지 않는다.
    model = SignalGraphModel()
    choose(session, model, name="Mode")
    assert model.record(observe(session, 1), session, SOURCE)
    assert model.samples[0].value == 1 and not model.samples[0].unit


def test_equal_timestamps_and_repeated_receive_preserve_order(session):
    # 동일 시각도 실제 수신건마다 보관하며 cache polling으로 추가하지 않는다.
    model = SignalGraphModel()
    choose(session, model)
    for stamp in (1, 1, 2):
        assert model.record(observe(session, stamp), session, SOURCE)
    assert [s.timestamp for s in model.samples] == [1, 1, 2]
    assert model.accepted == 3


@pytest.mark.parametrize("capacity", [0, -1, True, 1.5])
def test_invalid_capacity_rejected(capacity):
    # memory limit의 잘못된 설정을 생성 시 거부한다.
    with pytest.raises(ValueError):
        SignalGraphModel(capacity)


def test_bounded_history_omission_is_not_can_loss(session):
    # 가장 오래된 graph history만 제외하며 수신/Decode 손실이라고 주장하지 않는다.
    model = SignalGraphModel(capacity=3)
    choose(session, model)
    for stamp in range(10):
        assert model.record(observe(session, stamp), session, SOURCE)
    assert [s.timestamp for s in model.samples] == [7, 8, 9]
    assert model.accepted == 10 and model.history_omitted == 7
    assert model.buffer_dropped == 0 and model.decode_errors == 0


@pytest.mark.parametrize("value", ["ONE", None, True, float("nan"), float("inf"), -float("inf"), 10**1000])
def test_unsupported_values_never_become_samples(session, value):
    # 정상 DecodedMessage 계약 밖 값은 경계 모의로 방어 검증한다. 실제 codec 계약은 변경하지 않는다.
    model = SignalGraphModel()
    choose(session, model)
    obs = observe(session, 1)
    decoded = SimpleNamespace(decode_status=DecodeStatus.DECODED, message_name="TestOnlySample",
                              signals={"Measurement": value})
    injected = replace(obs, decoded=decoded)
    assert not model.record(injected, session, SOURCE)
    assert model.state == "Unsupported Value" and model.value_excluded == 1 and not model.samples


def test_decode_error_preserves_last_value_and_breaks_curve(session):
    # 실패 후 cache의 정상값을 새 sample로 복사하거나 오류 구간을 연결하지 않는다.
    model = SignalGraphModel()
    choose(session, model)
    assert model.record(observe(session, 1), session, SOURCE)
    bad = replace(make_demo_frame(0), data=b"\x28", dlc=1, timestamp=2)
    assert not model.record(session.process(bad), session, SOURCE)
    assert model.state == "Decode Error" and len(model.samples) == 1 and model.latest_value == -10.0
    assert model.record(observe(session, 3), session, SOURCE)
    assert model.samples[-1].segment != model.samples[0].segment


@pytest.mark.parametrize("stamp", [None, 0.5])
def test_missing_or_backward_timestamp_excluded_without_synthetic_time(session, stamp):
    # 새 numeric observation은 표시하되 time point는 제외하고 다음 점과 선을 끊는다.
    model = SignalGraphModel()
    choose(session, model)
    assert model.record(observe(session, 1), session, SOURCE)
    assert not model.record(observe(session, stamp), session, SOURCE)
    assert model.state == "Unsupported Timestamp" and model.timestamp_excluded == 1
    assert model.latest_timestamp == stamp and len(model.samples) == 1
    assert model.record(observe(session, 2), session, SOURCE)
    assert model.samples[0].segment != model.samples[1].segment


def test_raw_buffer_drop_separate_counter_and_gap(session):
    # GUI buffer가 제외한 프레임과 graph history 제한을 구분한다.
    model = SignalGraphModel()
    choose(session, model)
    model.record(observe(session, 1), session, SOURCE)
    model.note_buffer_drop(4)
    model.record(observe(session, 2), session, SOURCE)
    assert model.buffer_dropped == 4 and model.history_omitted == 0
    assert model.samples[0].segment != model.samples[1].segment
    model.note_buffer_drop(0)
    assert model.buffer_dropped == 0


def test_clear_graph_does_not_change_cache_or_selection(session):
    # Graph Clear는 공용 Cache를 비우지 않는다.
    model = SignalGraphModel()
    selected = choose(session, model)
    model.record(observe(session, 1), session, SOURCE)
    before = session.service.cache.snapshot()
    model.clear()
    assert model.selection == selected and not model.samples and model.accepted == 0
    assert session.service.cache.snapshot() == before


def test_reload_source_and_past_observation_isolated(session, synthetic_dbc_path):
    # generation 변경마다 과거 mapping/data를 버리고 명시적 DBC만 현재 session을 따른다.
    model = SignalGraphModel()
    choose(session, model)
    old = observe(session, 1)
    model.record(old, session, SOURCE)
    session.load(synthetic_dbc_path)
    assert model.sync_session(session, SOURCE) and model.selection is None and not model.samples
    choose(session, model)
    assert not model.record(old, session, SOURCE)
    assert model.sync_session(session, "Live / FAKE TEST ONLY") and not model.samples and model.selection is None


def test_tx_and_error_mask_not_graphed(session):
    # 제출/echo/오류 ID는 정상 signal RX sample로 사용하지 않는다.
    model = SignalGraphModel()
    choose(session, model)
    for frame in [replace(make_demo_frame(0), is_rx=False), replace(make_demo_frame(0), is_error_frame=True)]:
        assert not model.record(session.process(frame), session, SOURCE)
    assert not model.samples


def test_inactive_mux_branch_is_no_data(session):
    # 최신 mux frame에 없는 신호는 과거 cache에서 복원하지 않는다.
    from pc_diagnostic import DbcCodec
    codec = DbcCodec(session.loader)
    model = SignalGraphModel()
    choose(session, model, message="TestOnlyMux", can_id=1618, name="BranchZero")
    for stamp, values in [(1, {"Selector":0,"BranchZero":7}), (2, {"Selector":1,"BranchOne":9})]:
        frame = replace(codec.encode("TestOnlyMux", values), timestamp=stamp, channel="DEMO/TEST ONLY", is_rx=True)
        model.record(session.process(frame), session, SOURCE)
    assert model.state == "No Data" and len(model.samples) == 1


def test_finite_large_values_supported_without_health_policy():
    # 유한 큰 값의 표시 여부는 ECU 값 범위/유효성 승인과 별개이다.
    assert finite_number(1e308) and finite_number(-1e308)
