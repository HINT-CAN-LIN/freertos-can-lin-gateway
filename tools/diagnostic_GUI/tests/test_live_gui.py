"""Fake Live TEST ONLY의 GUI 파이프라인/오류/해제 검증. 실제 CANable 시험이 아니다."""
from threading import Event
import pytest
pytest.importorskip("PySide6", reason="install .[gui]")
from PySide6.QtCore import Qt, QThread
from PySide6.QtTest import QTest
from pc_diagnostic.interfaces import CanInterfaceError, MockCanInterface
from pc_diagnostic.gui.connection import ConnectionSettings
from pc_diagnostic.gui.ecu_observation import MessageMapping
from pc_diagnostic.gui.vehicle_status import SignalMapping
from pc_diagnostic.gui.logging_session import LoggingState
from pc_diagnostic.logger import RawCanLogger, read_jsonl
from test_gui import qt_app, window_factory, wait_until
from fake_live import FakeLive, FAKE_CHANNEL, fixture_frames


def select_live(window, factory, *, backend="slcan", channel="COM_TEST_ONLY"):
    # Fake factory의 주입은 테스트에서만 수행하며 실제 port를 열지 않는다.
    window._live_interface_factory = factory
    view = window.connection_view
    view.mode_combo.setCurrentText("Live")
    view.backend_combo.setCurrentIndex(view.backend_combo.findData(backend))
    view.channel_edit.setText(channel)
    view.bitrate_edit.setText("500000")
    return view


def bind_test_views(window):
    # Vehicle/ECU/Fault 매핑은 기존 TEST ONLY DBC에 명시적으로 연결한다.
    session = window.decode_session
    window.vehicle_view.model.bind("DBC Observation",
        SignalMapping("TestOnlySample", "Measurement", FAKE_CHANNEL, True, True), session)
    mapping = MessageMapping("TestOnlySample", FAKE_CHANNEL, 1617, False, True, True)
    window.ecu_view.model.bind("VCU", mapping, session)
    window.ecu_view.model.bind_fault(mapping, session)


def stop_and_wait(window):
    # Worker와 file writer가 모두 해제될 때까지 실제 상태를 기다린다.
    window.stop_monitor()
    wait_until(lambda: window.worker is None and not window.logging_session.snapshot().active)
    window.logging_view.refresh()


def test_default_mock_and_no_automatic_device_open(window_factory):
    # 초기 실행은 원래 Mock이며 COM7이나 Connected를 기본 표시하지 않는다.
    window = window_factory()
    view = window.connection_view
    assert view.mode_combo.currentText() == "Mock"
    assert view.backend_combo.currentData() == "" and view.channel_edit.text() == ""
    assert "Disconnected" in view.status_label.text()
    assert not view.channel_edit.isEnabled()
    window.start_monitor()
    # 프레임 표시는 queued opened Slot보다 먼저 끝날 수 있어 연결 상태 갱신도 기다린다.
    wait_until(lambda: window.table.rowCount() > 0
               and view.status_label.text() == "Connection: Mock running")
    assert "Mock running" in view.status_label.text()


@pytest.mark.parametrize("backend,channel,bitrate", [
    ("", "port", "500000"), ("slcan", "", "500000"), ("slcan", "port", "invalid"),
    ("slcan", "port", "-1"), ("gs_usb", "COM_TEST", "500000"),
])
def test_invalid_ui_settings_never_start_transport(window_factory, backend, channel, bitrate):
    # 잘못된 설정은 Worker 생성 전에 원인과 함께 Error로 표시한다.
    window = window_factory()
    view = select_live(window, lambda settings: pytest.fail("transport opened"), backend=backend, channel=channel)
    view.bitrate_edit.setText(bitrate)
    window.start_monitor()
    assert window.worker is None and window.status_label.text() == "Error"
    assert "Error" in view.status_label.text() and window.error_area.toPlainText()
    assert window.table.rowCount() == 0 and view.mode_combo.currentText() == "Live"


def test_live_does_not_generate_mock_and_preserves_raw_fields(window_factory, monkeypatch, qt_app):
    # Worker와 모든 화면이 Live에서 DEMO Generator를 호출하지 않는지 검출한다.
    frames = fixture_frames()
    transport = FakeLive(frames)
    window = window_factory()
    view = select_live(window, lambda settings: transport)
    monkeypatch.setattr("pc_diagnostic.gui.receiver.make_demo_frame", lambda *args: pytest.fail("Live DEMO generated"))
    original_refresh = window.vehicle_view.refresh
    def checked_refresh():
        # Qt UI 수정은 항상 QApplication 메인 스레드에서 수행한다.
        assert QThread.currentThread() == qt_app.thread()
        original_refresh()
    monkeypatch.setattr(window.vehicle_view, "refresh", checked_refresh)
    window.start_monitor()
    # Raw 수신과 queued 연결 알림은 별개이므로 Live 연결 표시까지 함께 기다린다.
    wait_until(lambda: window.table.rowCount() >= 2
               and view.status_label.text() == "Connection: Connected (application RX only)")
    assert "Connected" in view.status_label.text()
    assert window.selected_observation() is None
    assert window.table.item(0, 1).text() == FAKE_CHANNEL
    assert window.table.item(0, 0).data(Qt.ItemDataRole.UserRole).frame is frames[0]
    assert window.table.item(1, 0).data(Qt.ItemDataRole.UserRole).frame is frames[1]
    assert "(STD)" in window.table.item(0, 2).text() and "(EXT)" in window.table.item(1, 2).text()
    stop_and_wait(window)
    assert transport.shutdown_calls == 1 and transport.send_calls == 0


@pytest.mark.parametrize("format", ["jsonl", "csv"])
def test_live_pipeline_decode_cache_views_and_logging(window_factory, synthetic_dbc_path, tmp_path, format):
    # 동일 Raw 객체를 기존 Decode/Cache/Vehicle/ECU/Fault/Logger로 처리한다.
    accepted = []
    bus = FakeLive()
    window = window_factory()
    select_live(window, lambda settings: bus)
    window.load_dbc(synthetic_dbc_path)
    bind_test_views(window)
    original = window.logging_session.accept
    def tracked_accept(frame):
        # 파일 admission 순서를 기록하여 기존 CLI Logger와 byte 비교한다.
        result = original(frame)
        if result:
            accepted.append(frame)
        return result
    window.logging_session.accept = tracked_accept
    window.start_monitor()
    wait_until(lambda: window.receiver_running() and window.table.rowCount() >= 2)
    view = window.logging_view
    path = tmp_path / ("live." + format)
    view.set_output_path(path)
    view.format_combo.setCurrentIndex(view.format_combo.findData(format))
    view.start_recording()
    wait_until(lambda: window.logging_session.snapshot().written >= 4)
    stop_and_wait(window)
    window.vehicle_view.refresh()
    window.ecu_view.refresh()
    assert window.vehicle_view.table.item(5, 3).text() == "-10.0"
    assert window.vehicle_view.table.item(5, 4).text() == "test_unit"
    assert window.ecu_view.cards["VCU"]["state"].text() == "State: Observed"
    assert window.ecu_view.fault_table.rowCount() == 3
    assert "Live" in window.ecu_view.fault_label.text()
    assert window.ecu_view.statistics_table.rowCount() == 2
    cache = window.decode_session.service.cache
    assert cache.get_signal("TestOnlySample", "Measurement", channel=FAKE_CHANNEL) == -10.0
    snap = window.logging_session.snapshot()
    assert snap.closed and snap.received == snap.written == len(accepted)
    baseline = tmp_path / ("cli." + format)
    with RawCanLogger(baseline, format=format) as logger:
        for frame in accepted:
            logger.write(frame)
    assert path.read_bytes() == baseline.read_bytes()
    assert "Live" in view.source_label.text() and "TEST ONLY" in window.vehicle_view.source_label.text()
    if format == "jsonl":
        assert list(read_jsonl(path)) == accepted
    assert bus.send_calls == 0 and bus.shutdown_calls == 1


def test_source_switch_clears_old_data_cache_mappings_and_preserves_dbc(window_factory, synthetic_dbc_path):
    # Stop/Clear는 기존 계약대로 Cache 유지, Source 변경만 관측/매핑을 분리한다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    window.start_monitor()
    wait_until(lambda: window.table.rowCount() >= 2)
    stop_and_wait(window)
    cache = window.decode_session.service.cache
    assert cache.has_received("TestOnlySample", channel="DEMO/TEST ONLY")
    window.clear_monitor()
    assert cache.has_received("TestOnlySample", channel="DEMO/TEST ONLY")
    old_id = window.decode_session.session_id
    select_live(window, lambda settings: FakeLive())
    assert window.decode_session.session_id > old_id and window.decode_session.loader.is_loaded
    assert not cache.snapshot() and window.table.rowCount() == 0
    assert not window.vehicle_view.model.mappings and not window.ecu_view.model.mappings
    assert window.vehicle_view.channel_combo.count() == window.ecu_view.channel_combo.count() == 1
    assert "Live" in window.dbc_label.text()
    window.start_monitor()
    wait_until(lambda: window.table.rowCount() >= 2)
    stop_and_wait(window)
    assert cache.has_received("TestOnlySample", channel=FAKE_CHANNEL)
    window.connection_view.mode_combo.setCurrentText("Mock")
    assert not cache.snapshot() and window.table.rowCount() == 0
    assert "Mock" in window.logging_view.source_label.text()


def test_settings_and_dbc_locked_until_actual_shutdown(window_factory, synthetic_dbc_path):
    # 수신 중 direct 설정 변경도 반영하지 않고 Stop 후 실제 해제까지 잠금을 유지한다.
    window = window_factory()
    bus = FakeLive()
    view = select_live(window, lambda settings: bus)
    window.start_monitor()
    wait_until(lambda: window.receiver_running())
    before = view.raw_values()
    assert not view.mode_combo.isEnabled() and not window.load_dbc(synthetic_dbc_path)
    view.mode_combo.setCurrentText("Mock")
    view.channel_edit.setText("CHANGED")
    assert view.raw_values() == before
    window.stop_monitor()
    assert not view.mode_combo.isEnabled()
    stop_and_wait(window)
    window.refresh_frames()
    assert view.mode_combo.isEnabled() and bus.shutdown_calls == 1


@pytest.mark.parametrize("failure", ["import", "open", "detach"])
def test_live_failure_error_no_fallback_and_retry(window_factory, failure):
    # ImportError/없는 port/장치 분리는 모의하며 실제 환경을 손상시키지 않는다.
    buses = []
    def factory(settings):
        # 초기 연결 실패 또는 연결 후 분리 시나리오를 선택한다.
        if failure == "import":
            raise ImportError("FAKE LIVE TEST ONLY optional package missing")
        if failure == "open":
            raise CanInterfaceError("FAKE LIVE TEST ONLY serial port does not exist")
        bus = FakeLive()
        buses.append(bus)
        return bus
    window = window_factory()
    view = select_live(window, factory)
    window.start_monitor()
    if failure == "detach":
        wait_until(lambda: window.table.rowCount() > 0)
        buses[0].disconnect.set()
    wait_until(lambda: window.worker is None)
    assert window.status_label.text() == "Error" and "Error" in view.status_label.text()
    assert view.mode_combo.currentText() == "Live" and "TEST ONLY" in view.error_label.text()
    if buses:
        assert buses[0].shutdown_calls == 1
    bus = FakeLive()
    window._live_interface_factory = lambda settings: bus
    received = window.buffer.total_received
    window.start_monitor()
    wait_until(lambda: window.buffer.total_received > received and window.receiver_running())
    stop_and_wait(window)
    assert bus.shutdown_calls == 1


def test_stop_during_open_and_close_timeout_keep_window(window_factory, monkeypatch):
    # backend open 자체가 막힌 상황에서도 UI는 유한 Close 대기로 창을 유지한다.
    entered, release = Event(), Event()
    bus = FakeLive()
    def factory(settings):
        # 동기화 Event로 open 대기를 모의하고 종료 후 새 transport를 반드시 해제한다.
        entered.set()
        assert release.wait(3)
        return bus
    window = window_factory()
    view = select_live(window, factory)
    window.start_monitor()
    wait_until(entered.is_set)
    assert "Connecting" in view.status_label.text() and not window.receiver_running()
    monkeypatch.setattr("pc_diagnostic.gui.window.CLOSE_WAIT_MS", 1)
    try:
        assert not window.close() and window.isVisible()
        assert "timed out" in window.error_area.toPlainText()
        assert not view.mode_combo.isEnabled()
    finally:
        release.set()
    wait_until(lambda: window.worker is None)
    assert bus.shutdown_calls == 1 and bus.recv_calls == 0 and bus.send_calls == 0


def test_repeated_live_start_stop_requires_new_reception(window_factory):
    # 기존 행이 남아 있어도 매번 이번 실행의 수신량 증가와 새 transport 해제를 확인한다.
    buses = []
    def factory(settings):
        # 각 Start는 독립 bus를 생성한다.
        bus = FakeLive()
        buses.append(bus)
        return bus
    window = window_factory()
    select_live(window, factory)
    for cycle in range(3):
        before = window.buffer.total_received
        window.start_monitor()
        worker = window.worker
        window.start_monitor()
        assert window.worker is worker
        wait_until(lambda: window.buffer.total_received > before)
        stop_and_wait(window)
        assert len(buses) == cycle + 1 and buses[cycle].shutdown_calls == 1
    assert len({id(bus) for bus in buses}) == 3 and all(bus.send_calls == 0 for bus in buses)


def test_active_live_logging_close_releases_receiver_and_writer(window_factory, tmp_path):
    # GUI Close는 실제 Fake transport와 writer 모두 해제한다.
    bus = FakeLive()
    window = window_factory()
    select_live(window, lambda settings: bus)
    window.start_monitor()
    wait_until(lambda: window.receiver_running())
    window.logging_view.set_output_path(tmp_path / "close.jsonl")
    window.logging_view.start_recording()
    wait_until(lambda: window.logging_session.snapshot().written > 1)
    receiver, writer = window.worker, window.logging_session._thread
    assert window.close()
    assert not receiver.isRunning() and not writer.is_alive()
    assert window.logging_session.snapshot().closed and bus.shutdown_calls == 1 and bus.send_calls == 0


def test_shutdown_failure_blocks_reconnection_and_source_switch(window_factory):
    # 실패한 shutdown을 성공으로 간주하지 않고 다음 연결을 차단한다.
    bus = FakeLive(shutdown_error=True)
    window = window_factory()
    view = select_live(window, lambda settings: bus)
    window.start_monitor()
    wait_until(lambda: window.table.rowCount() > 0)
    stop_and_wait(window)
    assert window._live_release_failed and not window.start_button.isEnabled()
    assert not view.mode_combo.isEnabled()
    assert "shutdown not confirmed" in window.error_area.toPlainText()
    window.start_monitor()
    assert window.worker is None and bus.shutdown_calls == 1


def test_recorded_file_source_is_not_relabelled_after_mode_switch(window_factory, tmp_path):
    # 완료된 Live 파일의 provenance는 Mock 전환 뒤에도 Live로 유지한다.
    window = window_factory()
    select_live(window, lambda settings: FakeLive())
    window.start_monitor()
    wait_until(lambda: window.receiver_running())
    window.logging_view.set_output_path(tmp_path / "history.jsonl")
    window.logging_view.start_recording()
    wait_until(lambda: window.logging_session.snapshot().written > 0)
    stop_and_wait(window)
    window.refresh_frames()
    window.connection_view.mode_combo.setCurrentText("Mock")
    label = window.logging_view.source_label.text()
    assert "Current input: Mock" in label and "File source: Live" in label

@pytest.mark.parametrize("backend,missing", [("slcan", "serial"), ("gs_usb", "gs_usb")])
def test_missing_backend_dependency_has_install_guide_in_gui(window_factory, monkeypatch, backend, missing):
    # 실제 환경 변경 없이 missing-module 검사에서 실패하여 port를 전혀 열지 않는다.
    from pc_diagnostic.gui import connection
    monkeypatch.setattr(connection, "find_spec", lambda name: None if name == missing else object())
    window = window_factory()
    view = select_live(window, connection.open_live_interface, backend=backend,
                       channel="0" if backend == "gs_usb" else "COM_TEST_ONLY")
    window.start_monitor()
    wait_until(lambda: window.worker is None)
    assert "Missing Live dependency" in view.error_label.text()
    assert "pip install" in view.error_label.text() and missing in view.error_label.text()
    assert window.table.rowCount() == 0 and view.mode_combo.currentText() == "Live"


def test_typed_channels_and_formats_are_not_mixed(window_factory, synthetic_dbc_path):
    # 같은 ID라도 Channel 0/'0'과 STD/EXT는 네 가지 독립 관측이다.
    bus = FakeLive((*fixture_frames(0), *fixture_frames("0")), repeat=False)
    window = window_factory()
    select_live(window, lambda settings: bus, backend="gs_usb", channel="0")
    window.load_dbc(synthetic_dbc_path)
    window.start_monitor()
    wait_until(lambda: window.table.rowCount() == 4)
    stop_and_wait(window)
    assert window.ecu_view.statistics_table.rowCount() == 4
    snapshot = window.decode_session.service.cache.snapshot()
    assert len(snapshot) == 4
    assert (0, "TestOnlySample") in snapshot and ("0", "TestOnlySample") in snapshot
    assert bus.send_calls == 0


def test_live_decode_failure_keeps_raw_and_last_good_cache(window_factory, synthetic_dbc_path):
    # 잘못된 길이도 Raw 표에 남기고 기존 Decode 실패/Cache 보존 계약을 따른다.
    from dataclasses import replace
    good = fixture_frames()[0]
    bad = replace(good, data=good.data[:1], dlc=1)
    window = window_factory()
    bus = FakeLive([good, bad], repeat=False)
    select_live(window, lambda settings: bus)
    window.load_dbc(synthetic_dbc_path)
    bind_test_views(window)
    window.start_monitor()
    wait_until(lambda: window.table.rowCount() == 2)
    stop_and_wait(window)
    window.table.selectRow(1)
    assert window.table.item(1, 3).text() == "1"
    assert "invalid" in window.selection_label.text()
    assert window.vehicle_view.table.item(5, 7).text() == "Decode Error"
    assert window.vehicle_view.table.item(5, 3).text() == "-10.0"
    assert window.decode_session.service.cache.get_message("TestOnlySample", channel=FAKE_CHANNEL).raw_frame is good


def test_source_waits_for_writer_drain_even_after_receiver_exit(window_factory, tmp_path):
    # Receiver 종료 뒤에도 느린 writer가 남아 있으면 Source 변경을 차단한다.
    from pc_diagnostic.gui.logging_session import LoggingSession
    entered, release = Event(), Event()
    class SlowLogger(RawCanLogger):
        def write(self, frame):
            # 임의 sleep 대신 실제 writer 진입 Event로 동기화한다.
            entered.set()
            assert release.wait(3)
            super().write(frame)
    window = window_factory()
    select_live(window, lambda settings: FakeLive())
    session = LoggingSession(logger_factory=SlowLogger)
    window.logging_session = window.logging_view.session = session
    window.start_monitor()
    wait_until(lambda: window.receiver_running())
    window.logging_view.set_output_path(tmp_path / "slow-source.jsonl")
    window.logging_view.start_recording()
    wait_until(entered.is_set)
    try:
        window.stop_monitor()
        wait_until(lambda: window.worker is None)
        assert session.snapshot().active
        before = window.connection_view.raw_values()
        window.connection_view.mode_combo.setCurrentText("Mock")
        assert window.connection_view.raw_values() == before
    finally:
        release.set()
    wait_until(lambda: not session.snapshot().active and window.connection_view.mode_combo.isEnabled())
    assert window.can_change_source()


def test_close_shutdown_error_visible_before_window_disappears(window_factory):
    # Close 내부 wait 중 발생한 release 오류도 첫 요청에서 사용자에게 표시한다.
    bus = FakeLive(shutdown_error=True)
    window = window_factory()
    select_live(window, lambda settings: bus)
    window.start_monitor()
    wait_until(lambda: window.table.rowCount() > 0)
    assert not window.close() and window.isVisible()
    assert "shutdown not confirmed" in window.error_area.toPlainText()
    assert window.close() and bus.shutdown_calls == 1


def test_live_disconnect_drains_logging_without_mock_fallback(window_factory, tmp_path):
    # 장치 분리 모의는 file admission을 닫고 writer를 drain/close한다.
    bus = FakeLive()
    window = window_factory()
    select_live(window, lambda settings: bus)
    window.start_monitor()
    wait_until(lambda: window.receiver_running())
    path = tmp_path / "detach.jsonl"
    window.logging_view.set_output_path(path)
    window.logging_view.start_recording()
    wait_until(lambda: window.logging_session.snapshot().written > 1)
    bus.disconnect.set()
    wait_until(lambda: window.worker is None and not window.logging_session.snapshot().active)
    snap = window.logging_session.snapshot()
    assert snap.state is LoggingState.STOPPED and snap.closed and snap.written == snap.received
    assert len(list(read_jsonl(path))) == snap.written
    assert window.connection_view.mode_combo.currentText() == "Live"
    assert window.status_label.text() == "Error" and bus.shutdown_calls == 1


def test_empty_live_bus_never_displays_demo(window_factory):
    # 무수신은 Connected이면서 No Data일 수 있다. Mock으로 자동 대체하면 실패한다.
    bus = FakeLive([])
    window = window_factory()
    view = select_live(window, lambda settings: bus)
    window.start_monitor()
    wait_until(lambda: bus.recv_calls >= 3 and window.receiver_running())
    assert "Connected" in view.status_label.text() and window.table.rowCount() == 0
    assert window.buffer.total_received == 0
    stop_and_wait(window)
    assert bus.shutdown_calls == 1 and bus.send_calls == 0
