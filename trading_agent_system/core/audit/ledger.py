from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class AuditLedger:
    def __init__(self, path: str | Path = "data/audit/audit.jsonl") -> None:
        self.path = Path(path)
        self.records: list[dict[str, Any]] = []

    def write(self, event_type: str, payload: dict[str, Any] | BaseModel) -> None:
        if isinstance(payload, BaseModel):
            payload_data = payload.model_dump(mode="json")
        else:
            payload_data = payload
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "payload": payload_data,
        }
        self.records.append(record)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

    def warn(self, event_type: str, payload: dict[str, Any] | BaseModel) -> None:
        self.write(f"warn.{event_type}", payload)
