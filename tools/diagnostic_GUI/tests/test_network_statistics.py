"""Network 통계 단위 시험. 기존 TEST ONLY Raw/DBC; 실제 Hardware KPI가 아니다."""
from dataclasses import replace
import csv
import json
import math
import pytest
from pc_diagnostic import DbcCodec, DbcLoader
from pc_diagnostic.gui.demo import make_demo_frame
from pc_diagnostic.gui.network_statistics import NetworkStatisticsModel, expected_metadata
from pc_diagnostic.gui.observation_export import ExportSnapshot, ObservationExport, SnapshotFileWriter
from test_fault_history import REPOSITORY_DBC


def model_for(capacity=512):
    # 원래 Raw Timestamp와 시험 Source를 명시하고 실제 Bus를 열지 않는다.
    model = NetworkStatisticsModel(capacity)
    model.clear(source="Mock / TEST ONLY", source_kind="Mock / TEST ONLY", timestamp_source="TEST ONLY seconds")
    return model


def receive(model, *stamps, frame=None):
    # 기존 fixture Frame의 Timestamp만 합성하고 같은 Raw 속성을 유지한다.
    for stamp in stamps:
        model.record(replace(frame or make_demo_frame(0), timestamp=stamp))


def only_row(model, loader=None):
    # 직렬화 전 불변 모델 결과를 읽는다.
    return model.snapshot_records(loader or DbcLoader())[0]


@pytest.mark.parametrize("capacity", [0, -1, True, 1.5])
def test_invalid_capacity(capacity):
    # 저장 상한은 유효한 양수 정수만 허용한다.
    with pytest.raises(ValueError):
        model_for(capacity)


def test_first_and_consecutive_statistics():
    # N-1 간격/관측 span, 평균·최소·최대·Rate를 독립 계산값과 비교한다.
    model = model_for()
    receive(model, 10)
    first = only_row(model)
    assert first["frame_count"] == 1 and first["mean_period_s"] is None
    assert first["observed_duration_s"] is None and first["first_timestamp"] == 10
    receive(model, 10.01, 10.03)
    row = only_row(model)
    assert row["frame_count"] == 3 and row["interval_count"] == 2
    assert row["mean_period_s"] == pytest.approx(.015)
    assert row["min_period_s"] == pytest.approx(.01) and row["max_period_s"] == pytest.approx(.02)
    assert row["observed_duration_s"] == pytest.approx(.03)
    assert row["observed_frame_rate_hz"] == pytest.approx(2/.03)
    assert row["jitter"] is row["bus_load_percent"] is None
    assert row["clock_accuracy"] == row["hardware_verification"] == "NOT VERIFIED"


@pytest.mark.parametrize("kind,stamps,field", [
    ("missing", (10, None, 11), "timestamp_missing"),
    ("duplicate", (10, 10, 11), "timestamp_duplicate"),
    ("reversed", (10, 9, 11), "timestamp_reversed"),
    ("overflow", (0, 1e308, 0, 1e308), "timestamp_overflow"),
])
def test_anomalies_preserve_counts_and_raw_timestamps(kind, stamps, field):
    # 이상값을 정렬/삭제/PC 시각 대체하지 않고 해당 구간 timing은 N/A로 보인다.
    model = model_for()
    receive(model, *stamps)
    row = only_row(model)
    assert row["frame_count"] == len(stamps) and row[field] == 1
    assert row["first_timestamp"] == stamps[0] and row["last_timestamp"] == stamps[-1]
    assert row["mean_period_s"] is row["observed_frame_rate_hz"] is row["observed_duration_s"] is None
    assert "N/A: timestamp" in row["timing_status"]


@pytest.mark.parametrize("channel", [None, 0, "0"])
def test_identity_std_ext_rtr_error_and_tx(channel):
    # Channel 타입/STD·EXT/RTR/Error mask를 섞지 않고 TX는 제외한다.
    model = model_for()
    base = replace(make_demo_frame(0), channel=channel)
    for frame in (base, replace(make_demo_frame(1), channel=channel),
                  replace(base, is_remote_frame=True, data=b""),
                  replace(base, is_error_frame=True)):
        receive(model, 1, 2, frame=frame)
    model.record(replace(base, is_rx=False))
    rows = model.snapshot_records(DbcLoader())
    assert len(rows) == 4 and model.processed_rx == 8 and model.ignored_tx == 1
    assert model.observed_id_count == 2 and model.error_frames == 2
    assert {r["channel_type"] for r in rows} == {type(channel).__name__}
    assert all(r["frame_count"] == 2 for r in rows)
    assert all(r["mean_period_s"] is None for r in rows if r["is_remote_frame"] or r["is_error_frame"])


def test_mixed_channels_not_combined():
    # 같은 ID라도 독립 수신 clock domain이며 서로의 간격을 계산하지 않는다.
    model = model_for()
    for channel, times in [(None, (1, 2)), (0, (10, 10.01)), ("0", (100, 100.1))]:
        receive(model, *times, frame=replace(make_demo_frame(0), channel=channel))
    assert len(model.entries) == model.observed_id_count == 3
    assert sorted(r["mean_period_s"] for r in model.snapshot_records(DbcLoader())) == pytest.approx([.01,.1,1])


def test_capacity_and_drop_suppress_timing():
    # 이미 보관한 키 count는 유지하고 새 키 제외 및 GUI Drop을 구분한다.
    model = model_for(1)
    receive(model, 1, 2)
    receive(model, 1, frame=make_demo_frame(1))
    assert model.processed_rx == 3 and model.capacity_excluded == 1 and len(model.entries) == 1
    assert only_row(model)["mean_period_s"] is None
    model = model_for()
    receive(model, 1, 2)
    model.note_buffer_drop(4)
    assert only_row(model)["buffer_dropped"] == 4 and only_row(model)["mean_period_s"] is None
    model.clear(source="new", source_kind="Live", timestamp_source="unknown", dropped_baseline=4)
    receive(model, 3, 4);model.note_buffer_drop(4)
    assert only_row(model)["mean_period_s"] == 1 and only_row(model)["buffer_dropped"] == 0


@pytest.mark.parametrize("pending", [False, True])
def test_run_boundaries_do_not_measure_stop_gap(pending):
    # Stop 대기시간은 interval에서 제외하고 pending 이전 run이 섞이면 N/A로 한다.
    model = model_for();model.begin_receiver()
    receive(model, 1, 1.01)
    model.begin_receiver(pending_prior=pending)
    receive(model, 100, 100.01)
    row = only_row(model)
    assert row["frame_count"] == 4 and row["interval_count"] == 2 and row["interval_segments"] == 2
    if pending:
        assert row["observed_duration_s"] is None
    else:
        assert row["observed_duration_s"] == pytest.approx(.02)
        assert row["mean_period_s"] == pytest.approx(.01)
    assert row["receiver_runs"] == 2


@pytest.mark.parametrize("name,expected", [
    ("VCU_Command",10),("Motor_Status",10),("Vehicle_Status",20),
    ("Body_Status",100),("Gateway_Status",100),("Fault_Status",None)])
def test_actual_dbc_period_or_event(name, expected):
    # 명시적으로 로드한 Repository DBC의 실제 metadata만 사용한다.
    loader = DbcLoader().load(REPOSITORY_DBC)
    message = loader.get_message_by_name(name)
    frame = DbcCodec(loader).encode(name, {s.name:0 for s in message.signals})
    frame = replace(frame, is_rx=True)
    model = model_for();receive(model, 1, 1.02, frame=frame)
    row = only_row(model, loader)
    assert row["message_name"] == name and row["expected_period_ms"] == expected
    assert "Explicit DBC:" in row["expected_source"]
    assert "PASS" not in row["comparison_status"]
    if expected is None:
        assert row["tx_type"] == "Event" and row["mean_minus_expected_ms"] is None
    else:
        assert row["mean_minus_expected_ms"] == pytest.approx(20-expected)
    assert row["jitter_status"] == "Definition Pending"


def test_dbc_missing_metadata_and_reload(synthetic_dbc_path):
    # TEST ONLY fixture에 없는 주기/Tx type은 프로젝트 값으로 추정하지 않는다.
    loader=DbcLoader().load(synthetic_dbc_path);model=model_for()
    receive(model,1,2)
    row=only_row(model,loader)
    assert row["message_name"]=="TestOnlySample" and row["expected_period_ms"] is None
    assert "Definition Pending" in row["comparison_status"]
    old=model.snapshot_records(loader)
    loader.load(REPOSITORY_DBC)
    assert only_row(model,loader)["message_name"] is None
    assert old[0]["message_name"]=="TestOnlySample"


@pytest.mark.parametrize("format",["csv","jsonl"])
def test_network_export_snapshot_values_and_protection(tmp_path,format):
    # 기존 exclusive Writer/CSV null·JSONL map 관례를 재사용한다.
    model=model_for();receive(model,1,2)
    rows=model.snapshot_records(DbcLoader())
    snapshot=ExportSnapshot("network",rows)
    path=tmp_path/("network."+format)
    export=ObservationExport();assert export.start(snapshot,path,format=format)
    assert export.wait(2) and not export.writer.snapshot().error
    assert snapshot.row_count==1
    if format=="jsonl":
        row=json.loads(path.read_text(encoding="utf-8"))
        assert row["frame_count"]==2 and row["mean_period_s"]==1
        assert row["jitter"] is None and row["bus_load_percent"] is None
    else:
        with path.open(encoding="utf-8",newline="") as stream:row=next(csv.DictReader(stream))
        assert row["frame_count"]=="2" and row["jitter"]=="null"
        assert b"\r\r\n" not in path.read_bytes()
    before=path.read_bytes()
    assert export.start(snapshot,path,format=format)
    assert export.wait(2) and export.writer.snapshot().error
    assert path.read_bytes()==before
    model.clear(source="Live",source_kind="Live",timestamp_source="unknown")
    assert rows[0]["source"]=="Mock / TEST ONLY"
    with pytest.raises(TypeError):rows[0]["source"]="changed"


def test_empty_and_write_error(tmp_path):
    # 빈 집계는 파일이 없고 부분 쓰기 오류는 성공으로 계수하지 않는다.
    with pytest.raises(ValueError,match="No Data"):
        ObservationExport().start(ExportSnapshot("network",()),tmp_path/"none")
    class Broken(SnapshotFileWriter):
        def write(self,snapshot):
            # 파일 시스템 손상 없이 기존 Session 실패 경로를 주입한다.
            self.stream.write("partial");self.stream.flush()
            raise OSError("TEST ONLY network write")
    model=model_for();receive(model,1,2)
    export=ObservationExport(writer_factory=Broken)
    export.start(ExportSnapshot("network",model.snapshot_records(DbcLoader())),tmp_path/"partial")
    assert export.wait(2)
    assert export.writer.snapshot().error and export.writer.snapshot().written==0
    assert (tmp_path/"partial").read_text()=="partial"


def test_tiny_interval_never_exports_infinite_rate():
    # 양수 간격이라도 reciprocal이 표현 범위를 벗어나면 Rate는 N/A다.
    model=model_for();receive(model,0,5e-324)
    row=only_row(model)
    assert row["mean_period_s"]==5e-324 and row["observed_frame_rate_hz"] is None
    json.dumps(dict(row),allow_nan=False)
