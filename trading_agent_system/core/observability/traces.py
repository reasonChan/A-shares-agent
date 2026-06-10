from __future__ import annotations

import json
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from pydantic import Field

from trading_agent_system.schemas import StrictBaseModel, make_id, utc_now


class TraceEvent(StrictBaseModel):
    trace_id: str = Field(default_factory=lambda: make_id("trace"))
    run_id: str
    parent_id: str | None = None
    agent: str
    step: str
    status: str
    started_at: datetime
    ended_at: datetime
    duration_ms: int
    input_refs: list[str] = Field(default_factory=list)
    output_refs: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    model: str | None = None
    prompt_version: str | None = None
    token_usage: dict[str, int] = Field(default_factory=dict)
    decision_summary: str = ""
    error: str | None = None


class TraceSpan:
    def __init__(
        self,
        *,
        trace_id: str,
        run_id: str,
        parent_id: str | None,
        agent: str,
        step: str,
        input_refs: list[str],
        evidence_ids: list[str],
        model: str | None,
        prompt_version: str | None,
    ) -> None:
        self.trace_id = trace_id
        self.run_id = run_id
        self.parent_id = parent_id
        self.agent = agent
        self.step = step
        self.input_refs = input_refs
        self.output_refs: list[str] = []
        self.evidence_ids = evidence_ids
        self.model = model
        self.prompt_version = prompt_version
        self.token_usage: dict[str, int] = {}
        self.decision_summary = ""

    def set_output_refs(self, output_refs: list[str]) -> None:
        self.output_refs = output_refs

    def set_summary(self, summary: str) -> None:
        self.decision_summary = summary

    def set_token_usage(self, token_usage: dict[str, int]) -> None:
        self.token_usage = token_usage


class TraceLogger:
    def __init__(self, base_dir: str | Path = "data/traces") -> None:
        self.base_dir = Path(base_dir)

    @contextmanager
    def step(
        self,
        *,
        agent: str,
        step: str,
        run_id: str,
        parent_id: str | None = None,
        input_refs: list[str] | None = None,
        evidence_ids: list[str] | None = None,
        model: str | None = None,
        prompt_version: str | None = None,
    ) -> Iterator[TraceSpan]:
        started_at = utc_now()
        started_monotonic = time.perf_counter()
        span = TraceSpan(
            trace_id=make_id("trace"),
            run_id=run_id,
            parent_id=parent_id,
            agent=agent,
            step=step,
            input_refs=input_refs or [],
            evidence_ids=evidence_ids or [],
            model=model,
            prompt_version=prompt_version,
        )
        try:
            yield span
        except Exception as exc:
            self._append(self._event(span, started_at, started_monotonic, "failed", str(exc)))
            raise
        else:
            self._append(self._event(span, started_at, started_monotonic, "success", None))

    def record(
        self,
        *,
        agent: str,
        step: str,
        run_id: str,
        status: str,
        input_refs: list[str] | None = None,
        output_refs: list[str] | None = None,
        evidence_ids: list[str] | None = None,
        decision_summary: str = "",
        error: str | None = None,
    ) -> TraceEvent:
        now = utc_now()
        event = TraceEvent(
            run_id=run_id,
            agent=agent,
            step=step,
            status=status,
            started_at=now,
            ended_at=now,
            duration_ms=0,
            input_refs=input_refs or [],
            output_refs=output_refs or [],
            evidence_ids=evidence_ids or [],
            decision_summary=decision_summary,
            error=error,
        )
        self._append(event)
        return event

    def load(self, *, run_id: str | None = None, agent: str | None = None, limit: int | None = None) -> list[TraceEvent]:
        if not self.base_dir.exists():
            return []
        traces: list[TraceEvent] = []
        for path in sorted(self.base_dir.glob("*.jsonl")):
            with path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    event = TraceEvent.model_validate(json.loads(line))
                    if run_id is not None and event.run_id != run_id:
                        continue
                    if agent is not None and event.agent != agent:
                        continue
                    traces.append(event)
        traces.sort(key=lambda item: item.started_at)
        if limit is not None and limit >= 0:
            return traces[-limit:]
        return traces

    def _event(
        self,
        span: TraceSpan,
        started_at: datetime,
        started_monotonic: float,
        status: str,
        error: str | None,
    ) -> TraceEvent:
        ended_at = utc_now()
        return TraceEvent(
            trace_id=span.trace_id,
            run_id=span.run_id,
            parent_id=span.parent_id,
            agent=span.agent,
            step=span.step,
            status=status,
            started_at=started_at,
            ended_at=ended_at,
            duration_ms=max(0, int((time.perf_counter() - started_monotonic) * 1000)),
            input_refs=span.input_refs,
            output_refs=span.output_refs,
            evidence_ids=span.evidence_ids,
            model=span.model,
            prompt_version=span.prompt_version,
            token_usage=span.token_usage,
            decision_summary=span.decision_summary,
            error=error,
        )

    def _append(self, event: TraceEvent) -> None:
        path = self.base_dir / f"{event.run_id}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.model_dump(mode="json"), ensure_ascii=False, default=str) + "\n")
