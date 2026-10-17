"""PC 로컬 관측 snapshot Export. CAN/ECU Event 또는 Fault 상태를 생성하지 않는다."""
import csv
import json
from dataclasses import dataclass
from .logging_session import LoggingSession
from ..decoded_message import DecodeStatus

SCHEMA_VERSION = "pc-observation-v1"
RAW_FIELDS = ("timestamp", "arbitration_id", "is_extended_id", "is_remote_frame",
              "is_error_frame", "dlc", "data", "channel", "is_rx")
COMMON_FIELDS = ("schema_version", "record_type", "source", "session_id", "observation_sequence",
                 *RAW_FIELDS, "channel_type", "message_name", "decode_status", "error")
DECODED_FIELDS = (*COMMON_FIELDS, "source_mode", "signal_name", "decoded_value", "unit")
FAULT_FIELDS = (*COMMON_FIELDS, "receiver_run", "signals", "units", "dbc_choices",
                "timestamp_note", "fault_status")


@dataclass(frozen=True, slots=True)
class ExportSnapshot:
    kind: str
    records: tuple

    @property
    def row_count(self):
        # Signal 수만 세며 직렬화/파일 I/O는 Writer에 맡긴다.
        if self.kind == "fault":
            return len(self.records)
        return sum(max(1, len(decoded_signals(record.observation))) for record in self.records)


def decoded_signals(observation):
    # application 오류/실패 Decode에 정상 Signal을 표시하지 않는다.
    result = observation.decoded
    return result.signals if (not observation.processing_error and result is not None
                              and result.decode_status is DecodeStatus.DECODED) else {}


def decoded_snapshot(history, session):
    # Source는 새 GUI envelope에 수신 처리 때 저장한 값이다. 전역 현재값을 과거에 붙이지 않는다.
    if not session.loader.is_loaded:
        raise ValueError("No DBC: explicitly load a DBC before decoded export.")
    records = tuple(record for record in history.snapshot(session_id=session.session_id)
                    if record.observation.frame.is_rx)
    if not records:
        raise ValueError("No Data: no retained RX observations in the current DBC session.")
    return ExportSnapshot("decoded", records)


def fault_snapshot(model):
    # 화면 필터와 별개로 저장된 실제 유한 Fault 관측 이력만 고정한다.
    records = tuple(model.entries)
    if not records:
        raise ValueError("No Data: no retained Fault observations. No Event store is implemented.")
    return ExportSnapshot("fault", records)


def base_record(frame, *, kind, source, session_id, sequence, message_name, status, error):
    # RawCanFrame의 기존 직렬화를 재사용하고 Channel 타입도 명시한다.
    return {"schema_version": SCHEMA_VERSION, "record_type": kind, "source": source,
            "session_id": session_id, "observation_sequence": sequence,
            **frame.to_record(), "channel_type": type(frame.channel).__name__,
            "message_name": message_name, "decode_status": status, "error": error}


def export_rows(snapshot):
    # Worker에서 한 행씩 생성한다. 대량 Signal을 GUI에서 JSON/CSV로 펼치지 않는다.
    if snapshot.kind == "decoded":
        for record in snapshot.records:
            observation = record.observation
            result = observation.decoded
            base = base_record(observation.frame, kind="decoded_observation", source=record.source,
                               session_id=observation.session_id, sequence=record.sequence,
                               message_name=observation.message_name,
                               status=None if result is None else result.decode_status.value,
                               error=observation.processing_error or (None if result is None else result.error))
            signals = decoded_signals(observation)
            # 실패/빈 Signal은 이전 정상 Cache를 붙이지 않고 null 값 한 행으로 남긴다.
            for name, value in signals.items() if signals else ((None, None),):
                yield {**base, "source_mode": record.source_mode, "signal_name": name,
                       "decoded_value": value, "unit": observation.units.get(name)}
    elif snapshot.kind == "fault":
        for entry in snapshot.records:
            base = base_record(entry.frame, kind="fault_observation", source=entry.source,
                               session_id=entry.session_id, sequence=entry.sequence,
                               message_name=entry.message_name, status=entry.decode_state, error=entry.error)
            yield {**base, "receiver_run": entry.receiver_run, "signals": dict(entry.signals),
                   "units": dict(entry.units), "dbc_choices": dict(entry.choices),
                   "timestamp_note": entry.timestamp_note, "fault_status": entry.fault_status}
    else:
        raise ValueError("unsupported export snapshot kind")


class SnapshotFileWriter:
    def __init__(self, path, *, format="jsonl"):
        # RawCanLogger와 동일한 exclusive-create/UTF-8/newline 관례. 덮어쓰기/Append 없음.
        if format not in ("csv", "jsonl"):
            raise ValueError("export format must be csv or jsonl")
        self.format = format
        self.stream = open(path, "x", encoding="utf-8", newline="")

    def write(self, snapshot):
        # 기존 LoggingSession writer에서만 실행한다. 부분 실패는 정상 완료로 계수하지 않는다.
        if self.format == "csv":
            fields = DECODED_FIELDS if snapshot.kind == "decoded" else FAULT_FIELDS
            writer = csv.DictWriter(self.stream, fieldnames=fields)
            writer.writeheader()
        for row in export_rows(snapshot):
            if self.format == "jsonl":
                self.stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
            else:
                # CSV에서도 null/중첩 metadata를 구분한다. 값 문자열의 Python repr은 쓰지 않는다.
                cells = {key: json.dumps(value, ensure_ascii=False, allow_nan=False)
                         if value is None or isinstance(value, (dict, list)) else value
                         for key, value in row.items()}
                writer.writerow(cells)
        self.stream.flush()

    def close(self):
        # Close 실패는 기존 Session의 Error 경로로 전파한다.
        self.stream.close()


class ObservationExport:
    def __init__(self, *, writer_factory=SnapshotFileWriter):
        # 새 Thread/Timer 구현 대신 검증된 기존 파일 Session 한 개를 재사용한다.
        self.writer = LoggingSession(capacity=1, logger_factory=writer_factory)
        self.snapshot = None

    def start(self, snapshot, path, *, format="jsonl"):
        # 이미 진행 중이면 불변 snapshot을 바꾸지 않고 중복 Export를 거부한다.
        if self.writer.snapshot().active:
            return False
        if snapshot.kind not in ("decoded", "fault") or not snapshot.records:
            raise ValueError("No Data: export snapshot is empty or unsupported.")
        self.snapshot = snapshot
        if not self.writer.start(path, format=format):
            return False
        accepted = self.writer.accept(snapshot)
        self.writer.stop()  # 한 snapshot만 admission 후 drain한다.
        return accepted

    def wait(self, timeout):
        # 강제 취소/파일 삭제 없이 기존 Writer 종료 계약을 따른다.
        return self.writer.wait(timeout)
