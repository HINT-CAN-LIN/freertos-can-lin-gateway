"""Qt 없이 검증하는 GUI 조합 계층. 데이터는 기존 TEST ONLY fixture 전용."""
from dataclasses import replace

import pytest
from pc_diagnostic.dbc_loader import DbcLoadError
from pc_diagnostic.gui.decode_session import DecodeSession, MAX_LATEST_ATTEMPTS
from pc_diagnostic.gui.demo import make_demo_frame


def test_frame_result_and_units_are_immutable(synthetic_dbc_path):
    # 과거 프레임의 Raw 참조와 Unit 사본은 후속 세션에 영향받지 않는다.
    session = DecodeSession()
    session.load(synthetic_dbc_path)
    frame = make_demo_frame(0)
    observation = session.process(frame)
    assert observation.frame is frame and observation.decoded.raw_frame is frame
    with pytest.raises(TypeError):
        observation.units["Measurement"] = "wrong"
    with pytest.raises(AttributeError):
        observation.session_id = 9


def test_latest_metadata_is_bounded(synthetic_dbc_path):
    # GUI 최신 시도 메타데이터는 유한하고 기존 Cache 저장 계약은 바꾸지 않는다.
    session = DecodeSession()
    session.load(synthetic_dbc_path)
    for channel in range(MAX_LATEST_ATTEMPTS + 1):
        session.process(replace(make_demo_frame(0), channel=channel))
    assert len(session.latest_attempts) == MAX_LATEST_ATTEMPTS
    assert (0, "TestOnlySample") not in session.latest_attempts
    assert session.service.cache.has_received("TestOnlySample", channel=0)


def test_unexpected_processing_error_retains_raw(synthetic_dbc_path, monkeypatch):
    # 서비스 자체 오류도 행을 잃거나 정상 값으로 위장하지 않는다.
    session = DecodeSession()
    session.load(synthetic_dbc_path)
    def fail(frame):
        # transport/DBC 수치를 바꾸지 않는 application 장애 주입이다.
        raise RuntimeError("TEST ONLY application failure")
    monkeypatch.setattr(session.service, "process", fail)
    frame = make_demo_frame(0)
    observation = session.process(frame)
    assert observation.frame is frame and observation.decoded is None
    assert "application failure" in observation.processing_error


def test_missing_optional_dbc_dependency_safe(synthetic_dbc_path, monkeypatch):
    # 설치된 cantools를 삭제하지 않고 ImportError 경로만 모의한다.
    import builtins
    original = builtins.__import__
    def block(name, *args, **kwargs):
        # GUI Raw 사용에는 cantools가 필요하지 않다.
        if name == "cantools":
            raise ImportError("TEST ONLY")
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", block)
    session = DecodeSession()
    with pytest.raises(DbcLoadError, match="cantools"):
        session.load(synthetic_dbc_path)
    assert not session.loader.is_loaded
    assert session.process(make_demo_frame(0)).decoded is None


def test_same_signal_different_messages_and_channels(synthetic_dbc_path):
    # TEST ONLY 객체의 Signal 이름만 기존 이름으로 바꿔 같은 이름의 실제 Decode를 검증한다.
    session = DecodeSession()
    session.load(synthetic_dbc_path)
    definition = session.loader.get_message_by_name("TestOnlyExtended")
    definition.signals[0].name = "Measurement"
    definition.refresh()
    standard = session.process(replace(make_demo_frame(0), channel="A"))
    extended = session.process(replace(make_demo_frame(1), channel="A"))
    other_channel = session.process(replace(make_demo_frame(0), channel="B"))
    assert session.cached_message(standard).signals["Measurement"] == -10.0
    assert session.cached_message(extended).signals["Measurement"] == 515
    assert session.cached_message(other_channel).raw_frame.channel == "B"
    assert set(session.service.cache.snapshot()) == {
        ("A", "TestOnlySample"), ("A", "TestOnlyExtended"), ("B", "TestOnlySample")}
