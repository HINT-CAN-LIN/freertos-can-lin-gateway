"""Mock/Fake Live TEST ONLY Graph UI 검증. 실제 장치·차량 측정 시험이 아니다."""
from dataclasses import replace
import pytest
pytest.importorskip("PySide6", reason="install .[gui]")
from PySide6.QtCore import QThread
from pc_diagnostic.gui.graph_view import GRAPH_REFRESH_MS
from pc_diagnostic.gui.demo import make_demo_frame
from pc_diagnostic.gui.signal_graph import GraphSelection
from pc_diagnostic.gui.buffer import FrameBuffer
from pc_diagnostic.logger import read_jsonl
from test_gui import qt_app, window_factory, wait_until
from test_live_gui import select_live, stop_and_wait
from fake_live import FakeLive, FAKE_CHANNEL


def select_graph(window, channel="DEMO/TEST ONLY", message="TestOnlySample", signal="Measurement"):
    # UI에서 Channel/Message ID/Format/Signal을 직접 선택하고 Apply한다.
    view = window.graph_view
    view.observe_channel(channel)
    index = next(i for i in range(1, view.channel_combo.count())
                 if type(view.channel_combo.itemData(i)) is type(channel) and view.channel_combo.itemData(i) == channel)
    view.channel_combo.setCurrentIndex(index)
    message_index = next(i for i in range(1, view.message_combo.count())
                         if view.message_combo.itemData(i)[0] == message)
    view.message_combo.setCurrentIndex(message_index)
    view.signal_combo.setCurrentIndex(view.signal_combo.findData(signal))
    view.apply_signal()
    return view


def test_graph_no_dbc_then_explicit_selection_and_unit(window_factory, synthetic_dbc_path):
    # 기존 탭 index를 유지하고 Graph를 마지막에 추가한다.
    window = window_factory()
    graph = window.graph_view
    assert window.tabs.tabText(4) == "Signal Graph"
    assert graph.model.state == "No DBC" and not graph.apply_button.isEnabled()
    window.load_dbc(synthetic_dbc_path)
    assert graph.model.state == "No Data" and graph.model.selection is None
    graph.message_combo.setCurrentIndex(1)
    assert graph.signal_combo.currentIndex() == 0 and graph.model.selection is None
    select_graph(window)
    assert graph.unit_label.text() == "Unit: test_unit"
    assert not graph.model.samples


def test_graph_reuses_per_frame_decode_without_extra_codec_calls(window_factory, synthetic_dbc_path, monkeypatch):
    # MainWindow가 처리한 프레임 수만큼만 decode하며 Graph 자체 재디코딩은 없어야 한다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    graph = select_graph(window)
    calls = []
    codec = window.decode_session.service.codec
    original = codec.decode
    def tracked(frame):
        # 기존 codec 호출의 근거만 기록한다.
        calls.append(frame)
        return original(frame)
    monkeypatch.setattr(codec, "decode", tracked)
    for index in range(4):
        window.buffer.append(replace(make_demo_frame(index), timestamp=index))
    window.refresh_frames()
    graph.refresh()
    assert len(calls) == 4 and graph.model.accepted == 2
    assert graph.canvas.samples[0].value == -10.0
    assert "Unit: test_unit" in graph.value_label.text()
    before = graph.model.accepted
    graph.refresh(); graph.refresh()
    assert graph.model.accepted == before


def test_pause_freezes_curve_only_and_clear_is_graph_only(window_factory, synthetic_dbc_path):
    # Pause 중 수집/Cache/통계는 계속하며 Clear Graph는 공용 데이터를 변경하지 않는다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    graph = select_graph(window)
    window.start_monitor()
    wait_until(lambda: graph.model.accepted >= 2 and len(graph.canvas.samples) >= 2)
    graph.toggle_pause()
    snapshot = graph.canvas.samples
    before = graph.model.accepted
    wait_until(lambda: graph.model.accepted >= before + 2)
    assert graph.canvas.samples == snapshot and graph.paused
    graph.toggle_pause()
    assert len(graph.canvas.samples) > len(snapshot)
    stop_and_wait(window)
    graph.refresh()
    raw_rows = window.table.rowCount()
    cache = window.decode_session.service.cache.snapshot()
    stats = window.ecu_view.model.statistics.processed_rx
    graph.clear_graph()
    assert not graph.model.samples and not graph.canvas.samples
    assert window.table.rowCount() == raw_rows and window.decode_session.service.cache.snapshot() == cache
    assert window.ecu_view.model.statistics.processed_rx == stats


def test_pause_buffer_stays_bounded_and_counts_omitted_history(window_factory, synthetic_dbc_path):
    # 렌더 정지 동안에도 model 상한을 넘는 sample 이력을 무제한 쌓지 않는다.
    from pc_diagnostic.gui.signal_graph import SignalGraphModel
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    graph = window.graph_view
    graph.model = SignalGraphModel(capacity=3)
    graph.refresh()
    select_graph(window)
    graph.toggle_pause()
    for i in range(20):
        window.buffer.append(replace(make_demo_frame(0), timestamp=i))
    window.refresh_frames()
    graph.refresh()
    assert len(graph.model.samples) == 3 and graph.model.history_omitted == 17
    assert not graph.canvas.samples and graph.paused
    graph.toggle_pause()
    assert len(graph.canvas.samples) == 3


def test_graph_reload_and_source_switch_clear_paused_history(window_factory, synthetic_dbc_path):
    # DBC/Source generation이 바뀌면 이전 곡선/선택을 새 출처로 표시하지 않는다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    graph = select_graph(window)
    window.buffer.append(replace(make_demo_frame(0), timestamp=1))
    window.refresh_frames(); graph.refresh(); graph.toggle_pause()
    assert graph.canvas.samples
    window.load_dbc(synthetic_dbc_path)
    assert not graph.model.samples and graph.model.selection is None and not graph.paused and not graph.canvas.samples
    select_graph(window)
    window.buffer.append(replace(make_demo_frame(0), timestamp=2))
    window.refresh_frames(); graph.refresh()
    select_live(window, lambda settings: FakeLive())
    assert not graph.model.samples and graph.model.selection is None and not graph.canvas.samples
    assert "Live" in graph.source_label.text() and "TEST ONLY" in graph.source_label.text()
    assert graph.channel_combo.count() == 1


def test_graph_fake_live_logging_and_close(window_factory, synthetic_dbc_path, tmp_path):
    # Live Graph와 기존 Logger가 함께 동작하고 Pause가 기록을 중지시키지 않는다.
    window = window_factory()
    bus = FakeLive()
    select_live(window, lambda settings: bus)
    window.load_dbc(synthetic_dbc_path)
    graph = select_graph(window, FAKE_CHANNEL)
    window.start_monitor()
    wait_until(lambda: graph.model.accepted >= 2 and window.receiver_running())
    path = tmp_path / "graph-live.jsonl"
    window.logging_view.set_output_path(path)
    window.logging_view.start_recording()
    wait_until(lambda: window.logging_session.snapshot().written >= 2)
    graph.refresh(); graph.toggle_pause()
    before = window.logging_session.snapshot().written
    graph.clear_graph()
    wait_until(lambda: window.logging_session.snapshot().written > before and graph.model.accepted >= 2)
    assert window.close() and not graph.timer.isActive()
    snap = window.logging_session.snapshot()
    assert snap.closed and snap.written == len(list(read_jsonl(path))) and bus.shutdown_calls == 1 and bus.send_calls == 0


def test_graph_repeated_start_stop_preserves_same_source_history(window_factory, synthetic_dbc_path):
    # 이전 sample이 있어도 매 실행 새 수신과 새 Graph sample 증가를 확인한다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    graph = select_graph(window)
    for cycle in range(3):
        before = graph.model.accepted
        window.start_monitor()
        wait_until(lambda: graph.model.accepted > before)
        stop_and_wait(window)
    assert graph.model.accepted >= 3


def test_graph_render_main_thread_and_no_update_after_close(window_factory, qt_app, synthetic_dbc_path, monkeypatch):
    # QWidget rendering과 timer cleanup을 검증한다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    graph = select_graph(window)
    thread_checks = []
    original = graph.canvas.set_samples
    def checked(samples):
        # Worker에서 UI를 건드리면 즉시 실패한다.
        assert QThread.currentThread() == qt_app.thread()
        thread_checks.append(True)
        original(samples)
    monkeypatch.setattr(graph.canvas, "set_samples", checked)
    window.start_monitor()
    wait_until(lambda: bool(graph.canvas.samples))
    assert graph.timer.interval() == GRAPH_REFRESH_MS and thread_checks
    assert window.close() and not graph.timer.isActive()
    before = len(thread_checks)
    graph.refresh(); graph.clear_graph(); graph.toggle_pause()
    assert len(thread_checks) == before


def test_graph_raw_buffer_drop_and_clear_monitor_independent(window_factory, synthetic_dbc_path):
    # 표시 전 유실과 graph history 제한을 따로 보여주고 Raw Clear로 Graph를 비우지 않는다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    graph = select_graph(window)
    window.buffer = FrameBuffer(capacity=2)
    for i in range(8):
        window.buffer.append(replace(make_demo_frame(0), timestamp=i))
    window.refresh_frames(); graph.refresh()
    assert graph.model.buffer_dropped == 6 and graph.model.history_omitted == 0 and graph.model.accepted == 2
    window.clear_monitor()
    assert len(graph.model.samples) == 2


def test_signal_name_duplicates_do_not_auto_map(window_factory, synthetic_dbc_path):
    # 기존 TEST ONLY metadata의 Signal 이름만 메모리에서 중복시킨다. DBC 파일은 변경하지 않는다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    loader = window.decode_session.loader
    loader.get_message_by_name("TestOnlyExtended").signals[0].name = "Measurement"
    graph = window.graph_view
    graph.sync_session()
    assert graph.model.selection is None
    graph.message_combo.setCurrentIndex(2)
    assert graph.signal_combo.currentIndex() == 0 and graph.model.selection is None
    select_graph(window, message="TestOnlyExtended", signal="Measurement")
    assert graph.model.selection.is_extended_id and graph.model.selection.message_name == "TestOnlyExtended"


def test_large_values_canvas_renders_without_overflow(window_factory, synthetic_dbc_path):
    # 좌표 정규화는 화면 처리만 담당하며 실제 값을 clamp하지 않는다.
    from dataclasses import replace as dc_replace
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    graph = select_graph(window)
    graph.model.record(window.decode_session.process(replace(make_demo_frame(0), timestamp=1)),
                       window.decode_session, graph.source)
    sample = graph.model.samples[0]
    graph.canvas.set_samples((dc_replace(sample, value=-1e308), dc_replace(sample, value=1e308, timestamp=2)))
    image = graph.canvas.grab()
    assert not image.isNull() and graph.canvas.samples[1].value == 1e308


def test_clear_retains_selected_dbc_unit_and_no_dbc_state(window_factory, synthetic_dbc_path):
    # Clear 이후 미수신이어도 선택된 Unit 정의를 잘못 미정으로 표시하지 않는다.
    window = window_factory()
    graph = window.graph_view
    graph.clear_graph()
    assert graph.model.state == "No DBC"
    window.load_dbc(synthetic_dbc_path)
    select_graph(window)
    graph.clear_graph()
    assert graph.model.state == "No Data" and graph.model.unit == "test_unit"
    assert "Unit: test_unit" in graph.value_label.text()


def test_missing_timestamp_display_keeps_raw_unknown_and_no_plot(window_factory, synthetic_dbc_path):
    # 화면에서 timestamp 미제공을 수신 PC 시각으로 대체하지 않는다.
    window = window_factory()
    window.load_dbc(synthetic_dbc_path)
    graph = select_graph(window)
    window.buffer.append(replace(make_demo_frame(0), timestamp=None))
    window.refresh_frames(); graph.refresh()
    assert graph.model.latest_value == -10.0 and graph.model.latest_timestamp is None
    assert "Unsupported Timestamp" in graph.state_label.text()
    assert "unknown" in graph.value_label.text() and not graph.canvas.samples
    assert window.table.item(0, 0).text() == "unknown"
