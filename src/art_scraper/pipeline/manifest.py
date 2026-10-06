from __future__ import annotations

import json
from pathlib import Path

from art_scraper.models import ManifestRecord


class Manifest:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.records: dict[tuple[str, str], ManifestRecord] = {}
        if self.path.exists():
            self.load()

    def load(self) -> None:
        self.records.clear()
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                record = ManifestRecord.from_json_dict(json.loads(line))
                self.records[record.key] = record

    def append(self, record: ManifestRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_json_dict(), ensure_ascii=False) + "\n")
        self.records[record.key] = record

    def latest(self, source: str, source_id: str) -> ManifestRecord | None:
        return self.records.get((source, source_id))
