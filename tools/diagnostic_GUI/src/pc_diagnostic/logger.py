"""PC-only raw capture files. This schema is not a Gateway logger protocol."""

import csv
import json
from pathlib import Path

from .frame import RawCanFrame


class RawCanLogger:
    def __init__(self, path: str | Path, *, format: str = "jsonl"):
        if format not in ("jsonl", "csv"):
            raise ValueError("log format must be jsonl or csv")
        self._format = format
        # Never truncate an existing capture, even an empty one.
        self._file = open(path, "x", encoding="utf-8", newline="")
        try:
            if format == "csv":
                fields = list(RawCanFrame.__dataclass_fields__)
                self._writer = csv.DictWriter(self._file, fieldnames=fields)
                self._writer.writeheader()
                self._file.flush()
        except BaseException:
            self._file.close()
            raise

    def write(self, frame: RawCanFrame) -> None:
        record = frame.to_record()
        if self._format == "jsonl":
            self._file.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
        else:
            self._writer.writerow(record)
        self._file.flush()

    def close(self) -> None:
        self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def read_jsonl(path: str | Path):
    """Read mock fixtures/captures, preserving all raw fields and reporting line errors."""
    with open(path, encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            try:
                yield RawCanFrame.from_record(json.loads(line))
            except ValueError as exc:
                raise ValueError(f"{path}:{number}: {exc}") from exc
