"""Qt 독립 Logging Session 검증. 파일은 pytest 전용 tmp 경로만 사용한다."""
import csv
from dataclasses import replace
from threading import Event, get_ident
import pytest
from pc_diagnostic.gui.demo import make_demo_frame
from pc_diagnostic.gui.logging_session import LoggingSession, LoggingState
from pc_diagnostic.logger import RawCanLogger, read_jsonl

TEST_WAIT_SECONDS = 3


@pytest.fixture
def session_factory():
    # assertion 실패 후에도 생성한 파일 worker를 유한 시간 내 종료한다.
    sessions = []
    def create(**kwargs):
        # 각 테스트는 독립 session과 writer를 사용한다.
        session = LoggingSession(**kwargs)
        sessions.append(session)
        return session
    yield create
    for session in sessions:
        session.stop()
        assert session.wait(TEST_WAIT_SECONDS)


def finish(session):
    # stop 이후에는 admission을 닫고 이미 받은 대상을 모두 drain한다.
    session.stop()
    assert session.wait(TEST_WAIT_SECONDS)
    return session.snapshot()


def test_initial_idle_and_idempotent_stop(session_factory):
    # Receiver가 없어도 빈 session 객체는 생성되지만 자동 파일 기록은 없다.
    session = session_factory()
    snap = session.snapshot()
    assert snap.state is LoggingState.IDLE and not snap.active and snap.path is None
    assert not session.accept(make_demo_frame(0))
    session.stop()
    session.stop()
    assert session.wait(0) and session.snapshot().state is LoggingState.IDLE


@pytest.mark.parametrize("format", ["csv", "jsonl"])
def test_exact_existing_cli_bytes_fifo_and_raw_fields(session_factory, tmp_path, format):
    # 직렬화 bytes를 CLI Logger와 직접 비교해 필드/Timestamp/순서를 검증한다.
    frames = [replace(make_demo_frame(i), timestamp=stamp, channel=channel, is_rx=rx)
              for i, stamp, channel, rx in ((0, 0, "test,channel", True),
                                           (1, None, None, False), (0, 1.25, 0, True))]
    frames.append(replace(make_demo_frame(0), data=b"", dlc=4, is_remote_frame=True))
    frames.append(replace(make_demo_frame(0), is_error_frame=True))
    dest = tmp_path / ("gui." + format)
    baseline = tmp_path / ("cli." + format)
    session = session_factory()
    assert session.start(dest, format=format)
    for frame in frames:
        assert session.accept(frame)
    snap = finish(session)
    with RawCanLogger(baseline, format=format) as logger:
        for frame in frames:
            logger.write(frame)
    assert dest.read_bytes() == baseline.read_bytes()
    assert snap.state is LoggingState.STOPPED and snap.closed and snap.opened
    assert snap.written == snap.received == len(frames)
    assert snap.pending == snap.in_flight == snap.queue_dropped == snap.unconfirmed == 0
    if format == "jsonl":
        assert list(read_jsonl(dest)) == frames
    else:
        with dest.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            assert reader.fieldnames == list(frames[0].to_record())
            rows = list(reader)
        assert rows[1]["timestamp"] == "" and rows[1]["is_rx"] == "False"
        assert rows[0]["arbitration_id"] == str(frames[0].arbitration_id)


def test_duplicate_start_stop_and_new_session_count_reset(session_factory, tmp_path):
    # 중복 Start는 이전 파일/계수를 변경하지 않으며 새 이름으로만 재시작한다.
    session = session_factory()
    one, two = tmp_path / "one.jsonl", tmp_path / "two.csv"
    assert session.start(one)
    assert not session.start(two, format="csv")
    assert session.accept(make_demo_frame(0))
    session.stop()
    assert not session.accept(make_demo_frame(1))
    session.stop()
    assert session.wait(TEST_WAIT_SECONDS)
    assert len(list(read_jsonl(one))) == 1 and not two.exists()
    assert session.start(two, format="csv")
    assert session.accept(make_demo_frame(1))
    snap = finish(session)
    assert snap.written == snap.received == 1 and snap.format == "csv"


@pytest.mark.parametrize("path,format", [(None, "jsonl"), ("", "jsonl"), (" ", "csv"), ("unused", "bad")])
def test_missing_path_invalid_format(session_factory, path, format):
    # 설정이 없으면 자동 저장 경로 없이 명확한 Error를 반환한다.
    session = session_factory()
    assert not session.start(path, format=format)
    snap = session.snapshot()
    assert snap.state is LoggingState.ERROR and not snap.active and snap.received == 0


def test_missing_parent_existing_file_and_no_automatic_delete(session_factory, tmp_path):
    # 상위 폴더 생성/덮어쓰기/Append/실패 파일 자동 삭제를 하지 않는다.
    session = session_factory()
    missing = tmp_path / "missing" / "out.jsonl"
    assert session.start(missing)
    assert session.wait(TEST_WAIT_SECONDS)
    assert session.snapshot().state is LoggingState.ERROR and "Open failed" in session.snapshot().error
    assert not missing.parent.exists()
    existing = tmp_path / "existing.csv"
    existing.write_bytes(b"preserve existing bytes")
    assert session.start(existing, format="csv")
    assert session.wait(TEST_WAIT_SECONDS)
    assert "FileExistsError" in session.snapshot().error
    assert existing.read_bytes() == b"preserve existing bytes"
    assert session.start(tmp_path / "recovery.jsonl")
    assert session.accept(make_demo_frame(0))
    assert finish(session).state is LoggingState.STOPPED


def test_permission_and_file_lock_errors_are_reported_without_retry(session_factory, tmp_path):
    # Windows ACL/공유 위반을 factory 예외로 모의하며 실제 환경 권한은 변경하지 않는다.
    calls = []
    def denied(path, *, format):
        # 모의 factory가 명시적 PermissionError를 반환한다.
        calls.append(path)
        raise PermissionError("TEST ONLY access denied or file locked")
    session = session_factory(logger_factory=denied)
    assert session.start(tmp_path / "denied.jsonl")
    assert session.wait(TEST_WAIT_SECONDS)
    snap = session.snapshot()
    assert snap.state is LoggingState.ERROR and "PermissionError" in snap.error
    assert len(calls) == 1 and not snap.opened and not snap.closed


@pytest.mark.parametrize("error", [OSError("TEST ONLY disk full"), ValueError("TEST ONLY serialization failure")])
def test_write_failure_retains_partial_file_and_marks_unconfirmed(session_factory, tmp_path, error):
    # write 실패는 성공 Count로 세지 않고 잔여 대상을 unconfirmed로 표시하고 handle을 닫는다.
    entered, release = Event(), Event()
    loggers = []
    class Failing(RawCanLogger):
        def write(self, frame):
            # in-flight 중 Queue를 추가해 미확인 대상 수를 검사한다.
            entered.set()
            assert release.wait(TEST_WAIT_SECONDS)
            raise error
    def factory(path, *, format):
        # 실제 독점 생성과 close 계약을 그대로 사용한다.
        logger = Failing(path, format=format)
        loggers.append(logger)
        return logger
    session = session_factory(logger_factory=factory)
    path = tmp_path / "partial.jsonl"
    assert session.start(path)
    assert session.accept(make_demo_frame(0))
    assert entered.wait(TEST_WAIT_SECONDS)
    try:
        assert session.accept(make_demo_frame(1))
        assert session.accept(make_demo_frame(0))
    finally:
        release.set()
    assert session.wait(TEST_WAIT_SECONDS)
    snap = session.snapshot()
    assert snap.state is LoggingState.ERROR and snap.written == 0
    assert snap.unconfirmed == snap.received == 3 and snap.closed
    assert path.exists() and loggers[0]._file.closed


def test_bounded_queue_newest_drop_and_nonblocking_receiver(session_factory, tmp_path):
    # 느린 I/O는 Queue lock을 점유하지 않고 상한 초과는 새 프레임만 제외한다.
    entered, release = Event(), Event()
    writes = []
    class Slow:
        def __init__(self, path, *, format):
            # 파일 I/O 대기만 모의하며 GUI/Hardware에 접근하지 않는다.
            self.closed = False
        def write(self, frame):
            # 동기 Event로 실제 in-flight를 검출한다.
            entered.set()
            assert release.wait(TEST_WAIT_SECONDS)
            writes.append(frame)
        def close(self):
            # 모의 handle의 정상 종료를 기록한다.
            self.closed = True
    session = session_factory(capacity=2, logger_factory=Slow)
    frames = [replace(make_demo_frame(i), timestamp=i) for i in range(5)]
    assert session.start(tmp_path / "slow.jsonl")
    assert session.accept(frames[0]) and entered.wait(TEST_WAIT_SECONDS)
    try:
        assert session.accept(frames[1]) and session.accept(frames[2])
        assert not session.accept(frames[3]) and not session.accept(frames[4])
        snap = session.snapshot()
        assert (snap.received, snap.pending, snap.in_flight, snap.queue_dropped) == (5, 2, 1, 2)
        session.stop()
        assert not session.wait(0) and session.snapshot().state is LoggingState.STOPPING
        assert not session.start(tmp_path / "another.jsonl")
    finally:
        release.set()
    snap = finish(session)
    assert writes == frames[:3] and snap.written == 3
    assert snap.received == snap.written + snap.queue_dropped + snap.unconfirmed


def test_writer_file_io_is_off_calling_thread(session_factory, tmp_path):
    # 생성/write/close는 같은 writer, 호출 GUI/Receiver thread와 구분한다.
    identities = []
    class Spy(RawCanLogger):
        def __init__(self, path, *, format):
            # 기존 파일 생성은 writer 안에서 수행한다.
            identities.append(get_ident())
            super().__init__(path, format=format)
        def write(self, frame):
            # 파일 쓰기 thread를 실제로 기록한다.
            identities.append(get_ident())
            super().write(frame)
        def close(self):
            # 파일 해제 thread도 같은 소유자를 사용한다.
            identities.append(get_ident())
            super().close()
    session = session_factory(logger_factory=Spy)
    caller = get_ident()
    assert session.start(tmp_path / "thread.jsonl") and session.accept(make_demo_frame(0))
    finish(session)
    assert len(identities) == 3 and len(set(identities)) == 1 and identities[0] != caller


def test_close_error_not_reported_as_stopped(session_factory, tmp_path):
    # close 실패는 정상 종료로 표시하지 않으며 오류 원인을 보존한다.
    class CloseError(RawCanLogger):
        def close(self):
            # 실제 handle은 닫은 후 close 실패 상황을 모의한다.
            super().close()
            raise OSError("TEST ONLY close error")
    session = session_factory(logger_factory=CloseError)
    assert session.start(tmp_path / "close.jsonl") and session.accept(make_demo_frame(0))
    snap = finish(session)
    assert snap.state is LoggingState.ERROR and "Close failed" in snap.error
    assert snap.written == 1 and not snap.closed


@pytest.mark.parametrize("capacity", [0, -1, True, 1.5])
def test_logging_capacity_validation(capacity):
    # 자원 설정 오류는 생성 시점에 거부한다.
    with pytest.raises(ValueError):
        LoggingSession(capacity=capacity)

def test_open_failure_during_stop_accounts_for_queued_frames(session_factory, tmp_path):
    # Open 처리와 Stop 경합을 실제 Condition 이벤트로 동기화한다.
    entered = Event()
    session = None
    def delayed_failure(path, *, format):
        # Stop이 admission을 닫은 뒤 Open 실패를 반환하며 실제 ACL은 변경하지 않는다.
        entered.set()
        with session._condition:
            assert session._condition.wait_for(
                lambda: session.snapshot().state is LoggingState.STOPPING, timeout=TEST_WAIT_SECONDS)
        raise PermissionError("TEST ONLY delayed open failure")
    session = session_factory(logger_factory=delayed_failure)
    assert session.start(tmp_path / "delayed.jsonl") and entered.wait(TEST_WAIT_SECONDS)
    assert session.accept(make_demo_frame(0)) and session.accept(make_demo_frame(1))
    session.stop()
    assert not session.accept(make_demo_frame(0))
    assert session.wait(TEST_WAIT_SECONDS)
    snap = session.snapshot()
    assert snap.state is LoggingState.ERROR and snap.received == snap.unconfirmed == 2
    assert snap.written == snap.pending == snap.in_flight == snap.queue_dropped == 0
    assert "Open failed" in snap.error


def test_flush_failure_does_not_overcount_even_if_bytes_exist(session_factory, tmp_path):
    # write 후 flush가 실패한 프레임은 파일에 일부/전부 남을 수 있어 성공 Count로 세지 않는다.
    class FlushErrorFile:
        def __init__(self, stream):
            # 실 파일의 소유권은 기존 Logger가 유지한다.
            self.stream = stream
        def write(self, text):
            # 실제 파일 write는 수행하고 flush만 실패시키는 모의이다.
            return self.stream.write(text)
        def flush(self):
            # 디스크 공간 부족 등 flush 실패를 재현한다.
            raise OSError("TEST ONLY flush failure")
        def close(self):
            # 실제 handle은 정상 정리하여 테스트 환경을 보존한다.
            self.stream.close()
    def factory(path, *, format):
        # JSONL Logger를 그대로 사용하며 쓰기 API나 schema는 수정하지 않는다.
        logger = RawCanLogger(path, format=format)
        logger._file = FlushErrorFile(logger._file)
        return logger
    session = session_factory(logger_factory=factory)
    path = tmp_path / "flush.jsonl"
    frame = make_demo_frame(0)
    assert session.start(path) and session.accept(frame)
    assert session.wait(TEST_WAIT_SECONDS)
    snap = session.snapshot()
    assert snap.state is LoggingState.ERROR and snap.written == 0
    assert snap.received == snap.unconfirmed == 1 and snap.closed
    assert "flush failure" in snap.error and list(read_jsonl(path)) == [frame]
