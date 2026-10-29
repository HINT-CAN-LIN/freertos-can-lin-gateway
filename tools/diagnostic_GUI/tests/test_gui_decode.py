"""Phase 3C Mock/TEST ONLY 통합 검증. 기존 GUI 테스트는 그대로 유지한다."""
from dataclasses import replace
from pathlib import Path
import subprocess
import sys

import pytest

pytest.importorskip("PySide6", reason="install .[gui] for GUI tests")
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from pc_diagnostic.frame import RawCanFrame
from pc_diagnostic.gui.demo import make_demo_frame
from pc_diagnostic.gui.window import MAX_TABLE_ROWS
from test_gui import qt_app, window_factory, wait_until


def present(window, frame):
    # 기존 수신 버퍼 경계를 통해 Raw/Decode/Cache/UI를 함께 검증한다.
    window.buffer.append(frame)
    window.refresh_frames()
    window.table.selectRow(window.table.rowCount() - 1)
    return window.selected_observation()


def values(table):
    # 표시 순서 대신 실제 Signal 이름으로 결과를 비교한다.
    return {table.item(row, 1).text(): [table.item(row, col).text()
            for col in range(table.columnCount())] for row in range(table.rowCount())}


def test_no_dbc_raw_receives_without_decode(window_factory):
    # 자동 로드가 없고 사용자 선택 전에도 실제 Mock 수신이 계속된다.
    window = window_factory()
    assert not window.decode_session.loader.is_loaded
    window.start_monitor()
    wait_until(lambda: window.table.rowCount() >= 2)
    window.table.selectRow(0)
    assert window.selected_observation().decoded is None
    assert "Decode disabled" in window.selection_label.text()
    assert window.signal_table.rowCount() == window.cache_table.rowCount() == 0


def test_explicit_file_selection_load_and_cancel(window_factory, synthetic_dbc_path, monkeypatch):
    # 파일 선택 버튼 동작과 취소 시 기존 DBC 세션 보존을 확인한다.
    from pc_diagnostic.gui import window as module
    window = window_factory()
    monkeypatch.setattr(module.QFileDialog, "getOpenFileName", lambda *a: (str(synthetic_dbc_path), "DBC"))
    QTest.mouseClick(window.dbc_button, Qt.MouseButton.LeftButton)
    assert window.decode_session.loader.is_loaded
    assert "test_only.dbc" in window.dbc_label.text()
    assert "Decode enabled" in window.dbc_label.text()
    assert "Mock / DEMO ONLY" in window.dbc_label.text()
    session = window.decode_session.service
    monkeypatch.setattr(module.QFileDialog, "getOpenFileName", lambda *a: ("", ""))
    window.select_dbc()
    assert window.decode_session.service is session


@pytest.mark.parametrize("kind", ["missing", "malformed"])
def test_load_failure_preserves_raw_and_recovers(window_factory, synthetic_dbc_path, tmp_path, kind):
    # 실패한 DBC에 대해 Decode만 비활성화하며 Raw 수신/재시도는 유지한다.
    window = window_factory()
    target = tmp_path / "bad.dbc"
    if kind == "malformed":
        target.write_text("TEST ONLY malformed DBC", encoding="utf-8")
    assert not window.load_dbc(target)
    assert "Load failed" in window.dbc_label.text()
    window.start_monitor()
    wait_until(lambda: window.table.rowCount() > 0)
    assert window.status_label.text() == "Running"
    window.stop_monitor()
    wait_until(lambda: window.worker is None and window.buffer.pending_count == 0)
    assert window.load_dbc(synthetic_dbc_path)


def test_decode_selected_frame_values_units_and_identity(window_factory, synthetic_dbc_path):
    # 기존 fixture의 값/Unit/STD-EXT 구분을 그대로 표시하고 Raw 객체를 보존한다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    frame = replace(make_demo_frame(0), timestamp=12.5, channel=0)
    window._clock = lambda: 14.5
    observation = present(window, frame)
    assert observation.frame is frame and observation.decoded.raw_frame is frame
    selected = values(window.signal_table)
    assert selected["Measurement"][:4] == ["TestOnlySample", "Measurement", "-10.0", "test_unit"]
    assert selected["Mode"][2:4] == ["1", ""]
    assert selected["Counter"][2] == "7"
    cached = values(window.cache_table)
    assert cached["Measurement"][4] == "12.500000 / 2.000"
    assert "Channel=0" in window.cache_label.text()
    extended = present(window, make_demo_frame(1))
    assert extended.decoded.message_name == "TestOnlyExtended"
    assert values(window.signal_table)["Reading"][2:4] == ["515", "test_unit"]


def test_unknown_id_keeps_raw_and_no_fake_signals(window_factory, synthetic_dbc_path):
    # 기존 Codec unknown 테스트 벡터만 재사용한다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    frame = RawCanFrame(0x7FE, b"\xA5", timestamp=42)
    observation = present(window, frame)
    assert observation.decoded.raw_frame is frame
    assert observation.decoded.decode_status.value == "unknown"
    assert "Unknown / Undefined" in window.selection_label.text()
    assert window.table.item(0, 4).text() == "A5"
    assert window.signal_table.rowCount() == window.cache_table.rowCount() == 0


def test_repeated_message_updates_cache_not_historical_result(window_factory, synthetic_dbc_path, dbc_codec):
    # 후속 수신이 선택한 과거 프레임의 해석을 덮어쓰지 않아야 한다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    first = replace(make_demo_frame(0), timestamp=10, channel="test-only")
    present(window, first)
    second = replace(dbc_codec.encode("TestOnlySample", {"Measurement": 0, "Mode": 2, "Counter": 8}),
                     is_rx=True, timestamp=20, channel="test-only")
    present(window, second)
    window.table.selectRow(0)
    assert values(window.signal_table)["Measurement"][2] == "-10.0"
    assert values(window.cache_table)["Measurement"][2] == "0.0"
    assert window.decode_session.service.cache.last_timestamp("TestOnlySample", channel="test-only") == 20


def test_channels_and_same_signal_names_are_isolated(window_factory, synthetic_dbc_path, dbc_codec):
    # 동일 Message의 Signal 이름을 채널별로 구분한다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    for channel, measurement in (("A", -10), ("B", 0)):
        frame = replace(dbc_codec.encode("TestOnlySample", {"Measurement": measurement, "Mode": 1, "Counter": 7}),
                        is_rx=True, timestamp=12, channel=channel)
        present(window, frame)
    window.table.selectRow(0)
    assert values(window.cache_table)["Measurement"][2] == "-10.0"
    window.table.selectRow(1)
    assert values(window.cache_table)["Measurement"][2] == "0.0"
    assert len(window.decode_session.service.cache.snapshot()) == 2


@pytest.mark.parametrize("failure", ["length", "exception"])
def test_failure_keeps_good_cache_and_latest_error(window_factory, synthetic_dbc_path, monkeypatch, failure):
    # 실패 프레임과 마지막 정상 RX의 값/시각/상태를 구분한다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    frame = replace(make_demo_frame(0), timestamp=12.5, channel="A")
    present(window, frame)
    bad = replace(frame, timestamp=14, data=bytes(3), dlc=3) if failure == "length" else replace(frame, timestamp=14)
    if failure == "exception":
        definition = window.decode_session.loader.get_message_by_name("TestOnlySample")
        def fail(*args, **kwargs):
            # 실제 Codec의 예외→invalid 경로에 장애를 주입한다.
            raise RuntimeError("TEST ONLY decode failure")
        monkeypatch.setattr(definition, "decode", fail)
    observation = present(window, bad)
    assert observation.decoded.decode_status.value == "invalid"
    assert window.signal_table.rowCount() == 0
    assert values(window.cache_table)["Measurement"][2] == "-10.0"
    assert "12.500000" in values(window.cache_table)["Measurement"][4]
    assert "latest invalid" in values(window.cache_table)["Measurement"][5]
    assert "Latest error:" in window.cache_label.text()
    assert window.decode_session.service.cache.last_timestamp("TestOnlySample", channel="A") == 12.5
    assert window.table.item(1, 3).text() == str(bad.dlc)


@pytest.mark.parametrize("stamp,now,expected", [(10, 12, "2.000"), (None, 12, "unknown"), (14, 12, "unknown")])
def test_age_uses_original_clock_without_health(window_factory, synthetic_dbc_path, stamp, now, expected):
    # 미제공/역행 시각은 unknown이며 Fault/Offline 값을 만들지 않는다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    window._clock = lambda: now
    present(window, replace(make_demo_frame(0), timestamp=stamp))
    assert values(window.cache_table)["Measurement"][4].endswith(" / " + expected)
    window._clock = lambda: now + 3
    window.refresh_cache()
    assert "offline" not in window.cache_label.text().lower()


@pytest.mark.parametrize("failure", [False, True])
def test_reload_new_cache_keeps_historical_frame_units(window_factory, synthetic_dbc_path, tmp_path, failure):
    # Loader 계약에 따라 교체 시 새 Cache. 이전 Raw 행은 원래 세션의 해석을 보존한다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    observation = present(window, make_demo_frame(0))
    old = window.decode_session.service
    assert window.load_dbc(tmp_path / "missing.dbc" if failure else synthetic_dbc_path) is (not failure)
    assert window.decode_session.service is not old
    assert not window.decode_session.service.cache.snapshot()
    window.table.selectRow(0)
    window.show_selection()
    assert window.selected_observation() is observation
    assert values(window.signal_table)["Measurement"][3] == "test_unit"
    assert window.cache_table.rowCount() == 0
    assert "historical DBC session" in window.cache_label.text()


def test_dbc_change_blocked_while_running_stopping_and_pending(window_factory, synthetic_dbc_path, monkeypatch):
    # Running/Stop 요청 중/잔여 버퍼에서 교체를 거부하고 기존 세션을 유지한다.
    from pc_diagnostic.gui import window as module
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    old = window.decode_session.service
    window.start_monitor()
    wait_until(lambda: window.table.rowCount() > 0)
    def unexpected_dialog(*args):
        # 차단 시 파일 선택 UI도 열지 않아야 한다.
        pytest.fail("dialog opened during reception")
    monkeypatch.setattr(module.QFileDialog, "getOpenFileName", unexpected_dialog)
    assert not window.dbc_button.isEnabled()
    window.select_dbc()
    assert not window.load_dbc(synthetic_dbc_path)
    window.stop_monitor()
    assert window.worker is not None
    assert not window.load_dbc(synthetic_dbc_path)
    wait_until(lambda: window.worker is None and window.buffer.pending_count == 0)
    window.buffer.append(make_demo_frame(0))
    assert not window.load_dbc(synthetic_dbc_path)
    window.refresh_frames()
    assert window.decode_session.service is old
    assert window.load_dbc(synthetic_dbc_path)


def test_selection_nested_loop_and_close_requests_guarded(window_factory, synthetic_dbc_path, monkeypatch):
    # 파일 선택 중 재진입과 창 종료 후 로드/수신 요청을 차단한다.
    from pc_diagnostic.gui import window as module
    window = window_factory()
    def choose(*args):
        # modal dialog의 nested loop 중 재진입 요청을 모의한다.
        window.start_monitor()
        assert window.worker is None
        window.select_dbc()
        assert window.close()
        return str(synthetic_dbc_path), "DBC"
    monkeypatch.setattr(module.QFileDialog, "getOpenFileName", choose)
    window.select_dbc()
    assert not window.decode_session.loader.is_loaded
    window.start_monitor()
    assert window.worker is None
    assert not window.load_dbc(synthetic_dbc_path)
    assert not window.age_timer.isActive()


def test_clear_keeps_session_cache_and_repeat_start_stop(window_factory, synthetic_dbc_path):
    # 기존 Clear 의미는 표시 초기화이며, 같은 DBC 세션의 정상 Cache는 보존된다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    for _ in range(3):
        before = window.buffer.total_received
        window.start_monitor()
        wait_until(lambda: window.buffer.total_received > before and window.table.rowCount() > 0)
        window.stop_monitor()
        wait_until(lambda: window.worker is None and window.buffer.pending_count == 0)
    window.table.selectRow(0)
    assert window.cache_table.rowCount() > 0
    cache = window.decode_session.service.cache.snapshot()
    window.clear_monitor()
    assert window.decode_session.service.cache.snapshot() == cache
    assert window.signal_table.rowCount() == window.cache_table.rowCount() == 0


def test_decode_buffer_drop_and_table_are_bounded(window_factory, synthetic_dbc_path):
    # 처리 전에 제외된 프레임은 Decode/Cache에 전달되지 않는다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    count = MAX_TABLE_ROWS * 4
    for index in range(count):
        window.buffer.append(replace(make_demo_frame(0), timestamp=index))
    for _ in range(6):
        window.refresh_frames()
    assert window.table.rowCount() == MAX_TABLE_ROWS
    assert window._processed == 512
    assert window.buffer.dropped == count - 512
    assert window.processed_label.text() == "Raw/Decode processed: 512"
    assert window.decode_session.service.cache.last_timestamp("TestOnlySample", channel="DEMO/TEST ONLY") == count - 1


def test_new_decode_keeps_cli_optional_dependencies(tmp_path):
    # Qt와 cantools를 차단해도 기존 Raw CLI 및 GUI help 계약은 유지된다.
    script = """import importlib.abc,sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(('cantools','PySide6')):
            raise ImportError('TEST ONLY optional dependency unavailable')
sys.meta_path.insert(0,Block())
from pc_diagnostic.gui.decode_session import DecodeSession
from pc_diagnostic.gui.demo import make_demo_frame
assert DecodeSession().process(make_demo_frame(0)).decoded is None
from pc_diagnostic.cli import main
assert main(['monitor','--backend','mock','--duration','0.01']) == 0
"""
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=5)
    assert result.returncode == 0, result.stderr


def test_tx_decode_does_not_replace_rx_cache(window_factory, synthetic_dbc_path, dbc_codec):
    # UI 값 해석 성공도 송신 제출/TX를 실제 수신 Cache로 바꾸지 않는다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    present(window, replace(make_demo_frame(0), timestamp=10))
    tx = replace(dbc_codec.encode("TestOnlySample", {"Measurement": 0, "Mode": 2, "Counter": 8}),
                 channel="DEMO/TEST ONLY", timestamp=20)
    present(window, tx)
    assert values(window.signal_table)["Measurement"][2] == "0.0"
    assert values(window.cache_table)["Measurement"][2] == "-10.0"
    assert "10.000000" in values(window.cache_table)["Measurement"][4]

def test_age_timer_updates_while_stopped(window_factory, synthetic_dbc_path):
    # 수신 없이도 Qt 타이머가 동일 clock의 Age를 갱신하며 Cache 시각은 보존한다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    now = [12.0]
    window._clock = lambda: now[0]
    present(window, replace(make_demo_frame(0), timestamp=10))
    assert values(window.cache_table)["Measurement"][4] == "10.000000 / 2.000"
    now[0] = 15
    wait_until(lambda: values(window.cache_table)["Measurement"][4] == "10.000000 / 5.000")
    assert window.decode_session.service.cache.last_timestamp("TestOnlySample", channel="DEMO/TEST ONLY") == 10


def test_loaded_dbc_close_releases_worker(window_factory, synthetic_dbc_path):
    # DBC 사용 중에도 기존 Worker의 transport 해제와 close 후 요청 차단을 검증한다.
    from pc_diagnostic.interfaces import MockCanInterface
    created = []
    class Tracked(MockCanInterface):
        def shutdown(self):
            # 생성/해제 증거는 테스트에만 보관한다.
            self.released = True
            super().shutdown()
    def factory():
        # 매 실행 독립 Mock을 사용한다.
        transport = Tracked()
        transport.released = False
        created.append(transport)
        return transport
    window = window_factory(factory)
    window.load_dbc(synthetic_dbc_path)
    window.start_monitor()
    wait_until(lambda: window.table.rowCount() >= 2)
    worker = window.worker
    assert window.close()
    assert not worker.isRunning() and created[0].released and not created[0].sent_frames
    assert window.worker is None and not window.age_timer.isActive()
    assert not window.load_dbc(synthetic_dbc_path)


def test_mux_branch_cache_does_not_show_stale_signals(window_factory, synthetic_dbc_path, dbc_codec):
    # 기존 TEST ONLY mux 정의에서 최신 branch snapshot만 Cache 화면에 남긴다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    for signals in ({"Selector": 0, "BranchZero": 7}, {"Selector": 1, "BranchOne": 9}):
        present(window, replace(dbc_codec.encode("TestOnlyMux", signals), is_rx=True, channel="test-only"))
    assert set(values(window.cache_table)) == {"Selector", "BranchOne"}
    window.table.selectRow(0)
    assert set(values(window.signal_table)) == {"Selector", "BranchZero"}
    assert set(values(window.cache_table)) == {"Selector", "BranchOne"}


def test_application_failure_keeps_raw_and_labels_cache_failure(window_factory, synthetic_dbc_path, monkeypatch):
    # 예상 밖 service 오류도 최신 실패를 이전 정상 Cache의 성공 상태로 숨기지 않는다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    present(window, replace(make_demo_frame(0), timestamp=10))
    def fail(frame):
        # DecodeStatus를 합성하지 않고 실제 application 오류를 주입한다.
        raise RuntimeError("TEST ONLY application failure")
    monkeypatch.setattr(window.decode_session.service, "process", fail)
    observation = present(window, make_demo_frame(0))
    assert observation.processing_error and observation.decoded is None
    assert window.table.rowCount() == 2 and window.signal_table.rowCount() == 0
    assert values(window.cache_table)["Measurement"][2] == "-10.0"
    assert "latest processing error" in values(window.cache_table)["Measurement"][5]
    assert "application failure" in window.cache_label.text()

def test_error_mask_is_not_resolved_as_can_message(window_factory, synthetic_dbc_path):
    # Error frame ID는 backend 오류 mask일 수 있어 같은 숫자의 DBC Message로 연결하지 않는다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    present(window, make_demo_frame(0))
    error_frame = RawCanFrame(1617, is_error_frame=True, channel="DEMO/TEST ONLY")
    observation = present(window, error_frame)
    assert observation.decoded.decode_status.value == "invalid"
    assert observation.message_name is None
    assert window.cache_table.rowCount() == 0
    assert window.table.item(1, 2).text() == "0x00000651 (ERROR)"
    assert window.decode_session.service.cache.has_received("TestOnlySample", channel="DEMO/TEST ONLY")
