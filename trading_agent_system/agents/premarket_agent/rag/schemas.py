from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import Field

from trading_agent_system.schemas import StrictBaseModel, make_id, utc_now


ContentType = Literal[
    "title",
    "event_card",
    "summary",
    "body_chunk",
    "table_chunk",
    "risk_fact",
    "macro_calendar_item",
    "market_signal",
]
SourceType = Literal[
    "official_announcement",
    "official_policy",
    "exchange_notice",
    "authorized_news",
    "market_data",
    "overseas_market",
    "social",
    "internal_review",
    "unknown",
]
RAGSection = Literal[
    "core_conclusion",
    "post_close_events",
    "announcement_events",
    "portfolio_risks",
    "theme_candidates",
    "macro_calendar",
    "overseas_mapping",
    "avoid_list",
    "opening_radar",
    "premarket_instructions",
]
RetrieverName = Literal["structured", "keyword", "vector", "risk_event", "portfolio", "theme", "recency"]


class RAGDocument(StrictBaseModel):
    doc_id: str
    raw_document_id: str | None = None
    event_id: str | None = None
    event_cluster_id: str | None = None
    title: str
    content: str
    content_type: ContentType
    source: str
    source_type: SourceType = "unknown"
    source_rank: float = Field(ge=0, le=1)
    published_at: datetime | None = None
    fetched_at: datetime
    trading_day: date
    premarket_window_id: str
    symbols: list[str] = Field(default_factory=list)
    companies: list[str] = Field(default_factory=list)
    event_type: str | None = None
    themes: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    importance: Literal["S", "A", "B", "C"] | None = None
    bias: Literal["bullish", "bearish", "neutral", "mixed", "unclear"] | None = None
    confidence: float = Field(default=0.5, ge=0, le=1)
    actionability: Literal["watch", "candidate", "block", "watch_only"] | None = None
    risk_flags: list[str] = Field(default_factory=list)
    is_holding_related: bool = False
    is_watchlist_related: bool = False
    is_post_close: bool = True
    is_verified: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    content_hash: str


class RetrievalFilter(StrictBaseModel):
    trading_day: date | None = None
    premarket_window_id: str | None = None
    source_types: list[str] = Field(default_factory=list)
    min_source_rank: float | None = None
    symbols: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    event_types: list[str] = Field(default_factory=list)
    importance: list[str] = Field(default_factory=list)
    risk_flags_include: list[str] = Field(default_factory=list)
    risk_flags_exclude: list[str] = Field(default_factory=list)
    holding_related_only: bool = False
    watchlist_related_only: bool = False
    verified_only: bool = False
    published_after: datetime | None = None
    published_before: datetime | None = None


class RetrievalTask(StrictBaseModel):
    task_id: str = Field(default_factory=lambda: make_id("rtask"))
    section: RAGSection
    query: str
    filters: RetrievalFilter = Field(default_factory=RetrievalFilter)
    retrievers: list[RetrieverName] = Field(default_factory=list)
    top_k_per_retriever: int = 30
    final_top_k: int = 10
    require_evidence: bool = True
    diversity_by_event_cluster: bool = True
    max_tokens: int = 2000


class RetrievalResult(StrictBaseModel):
    result_id: str = Field(default_factory=lambda: make_id("rres"))
    task_id: str
    doc_id: str
    event_id: str | None = None
    event_cluster_id: str | None = None
    content: str
    title: str
    source: str
    source_type: str = "unknown"
    source_rank: float = Field(default=0.0, ge=0, le=1)
    published_at: datetime | None = None
    symbols: list[str] = Field(default_factory=list)
    event_type: str | None = None
    themes: list[str] = Field(default_factory=list)
    importance: str | None = None
    risk_flags: list[str] = Field(default_factory=list)
    retrieval_method: str
    raw_score: float = 0
    fused_score: float | None = None
    rerank_score: float | None = None
    business_score: float | None = None
    final_score: float | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class VectorSearchHit(StrictBaseModel):
    doc_id: str
    score: float
    document: RAGDocument


class EvidenceItem(StrictBaseModel):
    evidence_id: str
    event_id: str | None = None
    event_cluster_id: str | None = None
    source_id: str
    source: str
    source_type: str
    source_rank: float = Field(ge=0, le=1)
    published_at: datetime | None = None
    title: str
    excerpt: str
    symbols: list[str] = Field(default_factory=list)
    event_type: str | None = None
    importance: str | None = None
    confidence: float = Field(default=0.5, ge=0, le=1)
    risk_flags: list[str] = Field(default_factory=list)
    citation_label: str


class EvidencePack(StrictBaseModel):
    pack_id: str = Field(default_factory=lambda: make_id("epack"))
    trading_day: date
    premarket_window_id: str
    section: str
    query: str
    generated_at: datetime = Field(default_factory=utc_now)
    items: list[EvidenceItem] = Field(default_factory=list)
    dropped_duplicates: int = 0
    dropped_low_confidence: int = 0
    token_estimate: int = 0
    coverage: dict[str, Any] = Field(default_factory=dict)


class RAGEvaluationMetrics(StrictBaseModel):
    trading_day: date
    section: str
    recall_at_10: float | None = None
    precision_at_10: float | None = None
    holding_risk_recall: float | None = None
    critical_event_recall: float | None = None
    duplicate_ratio: float = 0
    low_confidence_leakage_ratio: float = 0
    evidence_coverage_ratio: float = 0
    citation_coverage_ratio: float = 0
    avg_source_rank: float = 0
    retrieval_latency_ms: float = 0
    indexing_latency_ms: float | None = None
    token_count: int = 0
    dropped_duplicates: int = 0
    dropped_low_confidence: int = 0
