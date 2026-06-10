from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import Field

from trading_agent_system.schemas import StrictBaseModel, make_id, utc_now


class KnowledgeRecord(StrictBaseModel):
    record_id: str = Field(default_factory=lambda: make_id("know"))
    record_type: Literal[
        "raw_document",
        "event",
        "event_cluster",
        "theme",
        "risk",
        "decision",
        "report",
    ]
    trading_day: date | None = None
    source: str = ""
    source_rank: str = "internal"
    title: str
    summary: str = ""
    content: str = ""
    url: str | None = None
    symbols: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    event_ids: list[str] = Field(default_factory=list)
    cluster_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)
    importance: str = "C"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class KnowledgeSearchResult(StrictBaseModel):
    record: KnowledgeRecord
    score: float
    matched_terms: list[str] = Field(default_factory=list)
