from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from pydantic import Field

from trading_agent_system.schemas import StrictBaseModel, make_id, utc_now


class MetricEvent(StrictBaseModel):
    metric_id: str = Field(default_factory=lambda: make_id("metric"))
    name: str
    value: float
    tags: dict[str, str] = Field(default_factory=dict)
    run_id: str | None = None
    recorded_at: datetime = Field(default_factory=utc_now)


class MetricsRecorder:
    def __init__(self, base_dir: str | Path = "data/metrics") -> None:
        self.base_dir = Path(base_dir)

    def record(
        self,
        name: str,
        value: float,
        *,
        tags: dict[str, str] | None = None,
        run_id: str | None = None,
    ) -> MetricEvent:
        event = MetricEvent(name=name, value=value, tags=tags or {}, run_id=run_id)
        path = self.base_dir / f"{name}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.model_dump(mode="json"), ensure_ascii=False, default=str) + "\n")
        return event

    def load(self, *, name: str | None = None, run_id: str | None = None, limit: int | None = None) -> list[MetricEvent]:
        if not self.base_dir.exists():
            return []
        paths = [self.base_dir / f"{name}.jsonl"] if name else sorted(self.base_dir.glob("*.jsonl"))
        metrics: list[MetricEvent] = []
        for path in paths:
            if not path.exists():
                continue
            with path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    event = MetricEvent.model_validate(json.loads(line))
                    if run_id is not None and event.run_id != run_id:
                        continue
                    metrics.append(event)
        metrics.sort(key=lambda item: item.recorded_at)
        if limit is not None and limit >= 0:
            return metrics[-limit:]
        return metrics
