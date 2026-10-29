"""Fault 이력 모델 검증. TEST ONLY 수신 및 기존 DBC를 명시적으로 읽는 계약 시험."""
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType
import pytest
from pc_diagnostic import DbcCodec
from pc_diagnostic.decoded_message import DecodeStatus, DecodedMessage
from pc_diagnostic.gui.decode_session import DecodeSession
from pc_diagnostic.gui.demo import make_demo_frame
from pc_diagnostic.gui.ecu_observation import MessageMapping
from pc_diagnostic.gui.fault_history import (FAULT_HISTORY_CAPACITY, MAX_FAULT_SOURCES,
                                            FaultHistoryModel, channel_key, mapping_key)

SOURCE = "Mock / TEST ONLY"
CHANNEL = "FAULT_CONTRACT_TEST_ONLY"
REPOSITORY_DBC = Path(__file__).resolve().parents[3] / "network/can/CAN__DB_펌웨어 전 최종본_v0.1.dbc"


@pytest.fixture
def fault_session():
    # 제품의 기본 DBC 설정이 아니다. 저장소 기존 산출물을 읽기 전용으로 검증한다.
    session = DecodeSession()
    session.load(REPOSITORY_DBC)
    return session


@pytest.fixture
def synthetic_session(synthetic_dbc_path):
    # 기존 TEST ONLY fixture를 변경 없이 재사용한다.
    session = DecodeSession()
    session.load(synthetic_dbc_path)
    return session


def mapping_for(session, *, channel=CHANNEL, name="Fault_Status"):
    # CAN ID/IDE는 실제 로드한 정의에서만 가져온다.
    message = session.loader.get_message_by_name(name)
    return MessageMapping(name, channel, message.frame_id, message.is_extended_frame, True, True)


def fault_frame(session, *, code=1, node=1, recovery=0, system=3, timestamp=10, channel=CHANNEL):
    # 기존 DBC Encoder로 시험 프레임을 생성한다. 새로운 Layout/Enum/ID를 정의하지 않는다.
    frame = DbcCodec(session.loader).encode("Fault_Status", {
        "FaultCode": code, "ECUOffline": node, "RecoveryState": recovery, "SystemState": system})
    return replace(frame, timestamp=timestamp, channel=channel, is_rx=True)


def configured(session, *, capacity=FAULT_HISTORY_CAPACITY):
    # 매핑은 시험자가 명시적으로 선택한 source이며 공식 Interface 승인을 의미하지 않는다.
    model = FaultHistoryModel(capacity)
    model.add_source(mapping_for(session), session, SOURCE)
    model.begin_receiver()
    return model


def test_empty_no_dbc_or_mapping_never_infers_no_fault(fault_session):
    # DBC 없는 상태에 ID를 임의로 연결하지 않는다.
    model = FaultHistoryModel()
    empty = DecodeSession()
    model.sync_session(empty, SOURCE)
    assert not model.entries and not model.sources
    with pytest.raises(ValueError, match="No DBC"):
        model.add_source(mapping_for(fault_session), empty, SOURCE)
    assert not model.record(fault_session.process(fault_frame(fault_session)), fault_session, SOURCE)
    assert not model.entries


def test_raw_decode_metadata_and_status_levels_are_preserved(fault_session):
    # 실제 per-frame 값/시각/DLC/Payload와 Choice를 각각 보존한다.
    model = configured(fault_session)
    frame = fault_frame(fault_session, timestamp=12.25)
    observation = fault_session.process(frame)
    assert model.record(observation, fault_session, SOURCE)
    entry = model.entries[-1]
    assert entry.frame is frame and entry.frame.dlc == 8 and entry.frame.timestamp == 12.25
    assert entry.frame.data == frame.data and dict(entry.signals) == dict(observation.decoded.signals)
    assert entry.units["FaultCode"] == "code" and entry.choices["FaultCode"] == "VCU_TIMEOUT"
    assert entry.choices["RecoveryState"] == "ACTIVE" and entry.fault_status == "Status Unknown"
    assert entry.decode_state == "Observed" and entry.source == SOURCE and entry.receiver_run == 1


@pytest.mark.parametrize("kind", ["TX", "error-mask", "other-channel", "EXT", "other-message"])
def test_non_selected_frames_are_excluded(fault_session, kind):
    # 동일 숫자 ID, 다른 Format/Channel 및 비-Fault 메시지를 혼합하지 않는다.
    model = configured(fault_session)
    frame = fault_frame(fault_session)
    if kind == "TX":
        frame = replace(frame, is_rx=False)
    elif kind == "error-mask":
        frame = replace(frame, is_error_frame=True)
    elif kind == "other-channel":
        frame = replace(frame, channel="other")
    elif kind == "EXT":
        frame = replace(frame, is_extended_id=True)
    else:
        frame = replace(frame, arbitration_id=fault_session.loader.get_message_by_name("Gateway_Status").frame_id)
    assert not model.record(fault_session.process(frame), fault_session, SOURCE)
    assert not model.entries


@pytest.mark.parametrize("fault", ["dlc", "rtr", "processing", "missing-result"])
def test_decode_failures_keep_raw_without_cache_backfill(fault_session, fault):
    # 실패 프레임에 이전 정상 Signal을 붙이지 않고 원본 Raw를 그대로 남긴다.
    model = configured(fault_session)
    model.record(fault_session.process(fault_frame(fault_session)), fault_session, SOURCE)
    frame = fault_frame(fault_session, timestamp=11)
    if fault == "dlc":
        frame = replace(frame, data=frame.data[:2], dlc=2)
    if fault == "rtr":
        frame = replace(frame, data=b"", is_remote_frame=True)
    observation = fault_session.process(frame)
    if fault == "processing":
        observation = replace(observation, decoded=None, processing_error="TEST ONLY processing error")
    if fault == "missing-result":
        observation = replace(observation, decoded=None)
    assert model.record(observation, fault_session, SOURCE)
    entry = model.entries[-1]
    assert entry.frame is frame and entry.decode_state == "Decode Error" and entry.error
    assert not entry.signals and entry.fault_status == "Status Unknown"
    assert model.entries[0].signals["FaultCode"] == 1


def test_repeated_observations_are_not_fault_events_or_deduplicated(fault_session):
    # 동일 Frame 수신을 각각 보존하며 Fault 발생 건수를 만들지 않는다.
    model = configured(fault_session)
    observation = fault_session.process(fault_frame(fault_session))
    for _ in range(3):
        assert model.record(observation, fault_session, SOURCE)
    assert model.observed == 3 and [e.sequence for e in model.entries] == [1, 2, 3]
    assert all(e.frame is observation.frame for e in model.entries)


@pytest.mark.parametrize("stamp,note", [(None, "Missing"), (8, "Reversed"), (10, "Provided")])
def test_timestamp_quality_keeps_arrival_order_and_values(fault_session, stamp, note):
    # 누락/역전을 보존하며 PC 시각으로 대체하거나 Timestamp 정렬하지 않는다.
    model = configured(fault_session)
    model.record(fault_session.process(fault_frame(fault_session, timestamp=10)), fault_session, SOURCE)
    model.record(fault_session.process(fault_frame(fault_session, timestamp=stamp)), fault_session, SOURCE)
    assert model.entries[-1].frame.timestamp == stamp and note in model.entries[-1].timestamp_note
    assert [e.sequence for e in model.entries] == [1, 2] and model.entries[-1].signals["FaultCode"] == 1


def test_filters_code_channel_message_errors_are_exact_and_non_mutating(fault_session):
    # 다중 명시 source의 필터는 이력 원본 및 관측 순서를 변경하지 않는다.
    model = configured(fault_session)
    other = mapping_for(fault_session, channel=0)
    model.add_source(other, fault_session, SOURCE)
    for code, channel in [(0, CHANNEL), (1, CHANNEL), (2, 0)]:
        model.record(fault_session.process(fault_frame(fault_session, code=code, channel=channel)), fault_session, SOURCE)
    frame = fault_frame(fault_session, channel=0)
    model.record(replace(fault_session.process(frame), decoded=None, processing_error="error"), fault_session, SOURCE)
    before = tuple(model.entries)
    assert [e.signals["FaultCode"] for e in model.filtered(fault_code=0)] == [0]
    assert len(model.filtered(channel=channel_key(0))) == 2 and not model.filtered(channel=channel_key("0"))
    assert len(model.filtered(message=("Fault_Status", other.arbitration_id, False))) == 4
    assert not model.filtered(message=("fault_status", other.arbitration_id, False))
    assert len(model.filtered(errors_only=True)) == 1 and tuple(model.entries) == before


@pytest.mark.parametrize("channel,other", [(0, "0"), (None, CHANNEL), ("0", 0)])
def test_typed_source_channels_do_not_become_wildcards(fault_session, channel, other):
    # 타입을 포함한 exact 채널 구분은 filter와 수집 모두에 적용한다.
    model = FaultHistoryModel()
    model.add_source(mapping_for(fault_session, channel=channel), fault_session, SOURCE)
    assert model.record(fault_session.process(fault_frame(fault_session, channel=channel)), fault_session, SOURCE)
    assert not model.record(fault_session.process(fault_frame(fault_session, channel=other)), fault_session, SOURCE)


def test_bounded_oldest_eviction_reports_incomplete_history(fault_session):
    # 상한 초과는 oldest observation만 제거하며 Fault 현재 상태를 복원하지 않는다.
    model = configured(fault_session, capacity=3)
    for index in range(5):
        model.record(fault_session.process(fault_frame(fault_session, timestamp=index)), fault_session, SOURCE)
    assert len(model.entries) == 3 and model.history_omitted == 2 and model.observed == 5
    assert [e.sequence for e in model.entries] == [3, 4, 5]
    assert all(e.fault_status == "Status Unknown" for e in model.entries)


def test_clear_preserves_sources_and_monotonic_sequence(fault_session):
    # Clear는 ECU 해제도 Cache 삭제도 아니며 순서 번호를 재사용하지 않는다.
    model = configured(fault_session)
    model.record(fault_session.process(fault_frame(fault_session)), fault_session, SOURCE)
    cache = fault_session.service.cache.snapshot()
    sources = dict(model.sources)
    model.clear()
    assert not model.entries and model.observed == model.history_omitted == 0
    assert model.sources == sources and fault_session.service.cache.snapshot() == cache
    model.record(fault_session.process(fault_frame(fault_session)), fault_session, SOURCE)
    assert model.entries[-1].sequence == 2


@pytest.mark.parametrize("change", ["source", "dbc", "failed-dbc"])
def test_session_changes_clear_history_mapping_and_reject_old_results(fault_session, change, tmp_path):
    # 과거 DBC 결과는 새 session으로 재해석하지 않는다.
    model = configured(fault_session)
    old = fault_session.process(fault_frame(fault_session))
    model.record(old, fault_session, SOURCE)
    source = SOURCE
    if change == "source":
        source = "Fake Live / TEST ONLY"
        fault_session.reset_observations()
    elif change == "dbc":
        fault_session.load(REPOSITORY_DBC)
    else:
        with pytest.raises(Exception):
            fault_session.load(tmp_path/"absent.dbc")
    assert model.sync_session(fault_session, source)
    assert not model.entries and not model.sources
    assert not model.record(old, fault_session, source)


def test_stop_restart_tags_runs_but_pending_backlog_is_unknown(fault_session):
    # Stop 이력은 유지하되 새 Start를 구분하고 backlog가 있으면 정확한 run을 주장하지 않는다.
    model = configured(fault_session)
    for pending in (False, True):
        model.record(fault_session.process(fault_frame(fault_session)), fault_session, SOURCE)
        model.begin_receiver(pending_prior=pending)
    model.record(fault_session.process(fault_frame(fault_session)), fault_session, SOURCE)
    assert [e.receiver_run for e in model.entries] == [1, 2, None]


def test_buffer_drop_is_separate_from_history_eviction(fault_session):
    # UI 처리 전 제외와 Fault history 제거를 서로 다른 계수로 보관한다.
    model = configured(fault_session, capacity=1)
    model.note_buffer_drop(17)
    for _ in range(2):
        model.record(fault_session.process(fault_frame(fault_session)), fault_session, SOURCE)
    assert model.buffer_dropped == 17 and model.history_omitted == 1 and model.observed == 2


def test_zero_recovery_and_reserved_values_never_infer_fault_clear(fault_session):
    # NONE/INVALID/CLEARED metadata 값도 실제 시스템 Fault 해제/정상으로 추론하지 않는다.
    model = configured(fault_session)
    for code, recovery in [(0, 1), (1, 0), (1, 1)]:
        model.record(fault_session.process(fault_frame(fault_session, code=code, recovery=recovery)), fault_session, SOURCE)
    frame = fault_frame(fault_session)
    # 기존 정의의 Invalid raw 0xFF를 수신한 시험. 제품에서 bit layout을 구현하지 않는다.
    frame = replace(frame, data=bytes([255])+frame.data[1:])
    model.record(fault_session.process(frame), fault_session, SOURCE)
    assert model.entries[-1].signals["FaultCode"] == 255
    assert model.entries[-1].choices["FaultCode"] == "INVALID"
    assert all(e.fault_status == "Status Unknown" for e in model.entries)


def test_entry_signal_and_metadata_snapshots_are_immutable(fault_session):
    # 후속 수신/사용자 코드가 과거 decode evidence를 변경할 수 없다.
    model = configured(fault_session)
    model.record(fault_session.process(fault_frame(fault_session)), fault_session, SOURCE)
    for values in (model.entries[-1].signals, model.entries[-1].units, model.entries[-1].choices):
        with pytest.raises(TypeError):
            values["FaultCode"] = 99


def test_source_capacity_and_remove_source_preserve_history(fault_session):
    # Source 목록도 유한하며 제거는 새 수집만 중지한다.
    model = configured(fault_session)
    model.record(fault_session.process(fault_frame(fault_session)), fault_session, SOURCE)
    for index in range(MAX_FAULT_SOURCES-1):
        model.add_source(mapping_for(fault_session, channel=f"TEST_ONLY_{index}"), fault_session, SOURCE)
    with pytest.raises(ValueError, match="capacity"):
        model.add_source(mapping_for(fault_session, channel="extra"), fault_session, SOURCE)
    model.remove_source(mapping_key(mapping_for(fault_session)))
    assert len(model.entries) == 1 and not model.record(fault_session.process(fault_frame(fault_session)), fault_session, SOURCE)


@pytest.mark.parametrize("capacity", [0, -1, True, 1.5])
def test_invalid_capacity_fails_early(capacity):
    # 리소스 정책 오류를 무한/잘못된 deque 동작으로 숨기지 않는다.
    with pytest.raises(ValueError):
        FaultHistoryModel(capacity)


@pytest.mark.parametrize("wrong", ["unconfirmed", "channel-unselected", "id-mismatch", "format-mismatch"])
def test_unapproved_display_mapping_is_not_accepted(fault_session, wrong):
    # 표시 확인도 Source/ID/Format exact 계약을 완화하지 않는다.
    model = FaultHistoryModel()
    mapping = mapping_for(fault_session)
    updates = {"unconfirmed":{"source_confirmed":False}, "channel-unselected":{"channel_selected":False},
               "id-mismatch":{"arbitration_id":0}, "format-mismatch":{"is_extended_id":True}}
    with pytest.raises(ValueError, match="Ambiguous"):
        model.add_source(replace(mapping, **updates[wrong]), fault_session, SOURCE)


def test_test_only_signal_message_reuses_existing_fixture_without_fault_code(synthetic_session):
    # 기존 DEMO frame을 명시적 관측 출처로 사용할 수 있고 FaultCode를 합성하지 않는다.
    model = FaultHistoryModel()
    mapping = mapping_for(synthetic_session, channel="DEMO/TEST ONLY", name="TestOnlySample")
    model.add_source(mapping, synthetic_session, SOURCE)
    assert model.record(synthetic_session.process(make_demo_frame(0)), synthetic_session, SOURCE)
    entry = model.entries[-1]
    assert entry.signals["Measurement"] == -10.0 and "FaultCode" not in entry.signals
    assert not model.filtered(fault_code=0) and entry.fault_status == "Status Unknown"


def test_duplicate_metadata_is_ambiguous_not_first_match(fault_session, monkeypatch):
    # 실제 metadata 목록에 같은 후보가 둘이면 임의 선택하지 않는다.
    message = fault_session.loader.get_message_by_name("Fault_Status")
    monkeypatch.setattr(fault_session.loader, "get_messages", lambda: (message, message))
    with pytest.raises(ValueError, match="Ambiguous"):
        FaultHistoryModel().add_source(mapping_for(fault_session), fault_session, SOURCE)


def test_removed_sources_do_not_leave_unbounded_timestamp_keys(fault_session):
    # 반복 source 추가/제거 후 내부 timestamp 보관도 현재 source 수로 제한된다.
    model = FaultHistoryModel()
    for index in range(MAX_FAULT_SOURCES+5):
        mapping = mapping_for(fault_session, channel=str(index))
        model.add_source(mapping, fault_session, SOURCE)
        model.record(fault_session.process(fault_frame(fault_session, channel=str(index))), fault_session, SOURCE)
        model.remove_source(mapping_key(mapping))
    assert not model.sources and not model._timestamps
    assert len(model.entries) == MAX_FAULT_SOURCES+5
