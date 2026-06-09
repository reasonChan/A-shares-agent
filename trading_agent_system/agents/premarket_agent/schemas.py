from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class SourceRank(str, Enum):
    OFFICIAL = "official"
    AUTHORIZED_NEWS = "authorized_news"
    MARKET_DATA = "market_data"
    OVERSEAS = "overseas"
    SOCIAL = "social"
    INTERNAL = "internal"


class Importance(str, Enum):
    S = "S"
    A = "A"
    B = "B"
    C = "C"


class Bias(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    MIXED = "mixed"
    UNCLEAR = "unclear"


class Actionability(str, Enum):
    WATCH = "watch"
    CANDIDATE = "candidate"
    BLOCK = "block"
    WATCH_ONLY = "watch_only"


class InstructionType(str, Enum):
    INCREASE_ATTENTION = "increase_attention"
    DECREASE_ATTENTION = "decrease_attention"
    AVOID_NEW_ENTRY = "avoid_new_entry"
    REDUCE_ONLY = "reduce_only"
    REQUIRE_CONFIRMATION = "require_confirmation"
    BLOCK_UNTIL_OFFICIAL_CONFIRMATION = "block_until_official_confirmation"
    WATCH_OPENING_AUCTION = "watch_opening_auction"


class PreMarketWindow(StrictModel):
    trading_day: date
    previous_trading_day: date
    timezone: str = "Asia/Shanghai"
    window_start: datetime
    morning_cutoff: datetime
    auction_start: datetime
    auction_observation_end: datetime
    auction_confirm_start: datetime
    auction_end: datetime
    continuous_open: datetime


class CollectorState(StrictModel):
    source_name: str
    last_seen_id: str | None = None
    last_seen_time: datetime | None = None
    last_success_at: datetime | None = None
    last_error: str | None = None
    etag: str | None = None
    last_modified: str | None = None
    fetch_count: int = 0
    error_count: int = 0


class RawDocument(StrictModel):
    source_id: str
    source_name: str
    source_rank: SourceRank
    title: str
    url: str | None = None
    external_id: str | None = None
    published_at: datetime | None = None
    fetched_at: datetime
    content_hash: str
    raw_text: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    format: Literal["html", "pdf", "json", "text", "csv", "market_data"]
    symbols: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class PreMarketEvent(StrictModel):
    event_id: str
    source_ids: list[str]
    source_rank: SourceRank
    title: str
    summary: str
    published_at: datetime | None = None
    first_seen_at: datetime
    last_updated_at: datetime
    symbols: list[str] = Field(default_factory=list)
    companies: list[str] = Field(default_factory=list)
    event_type: str
    related_themes: list[str] = Field(default_factory=list)
    importance: Importance
    bias: Bias
    confidence: float = Field(ge=0, le=1)
    actionability: Actionability
    is_post_close: bool = True
    is_holding_related: bool = False
    is_watchlist_related: bool = False
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)

    @field_validator("source_ids")
    @classmethod
    def require_sources(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("source_ids are required for every premarket event")
        return value


class EventCluster(StrictModel):
    cluster_id: str
    primary_event_id: str
    supporting_event_ids: list[str] = Field(default_factory=list)
    first_seen_at: datetime
    last_updated_at: datetime
    symbols: list[str] = Field(default_factory=list)
    companies: list[str] = Field(default_factory=list)
    event_type: str
    title: str
    summary: str
    primary_source_rank: SourceRank
    evidence_count: int
    importance: Importance
    bias: Bias
    confidence: float = Field(ge=0, le=1)
    actionability: Actionability
    is_post_close: bool = True
    carried_to_morning: bool = True
    risk_flags: list[str] = Field(default_factory=list)


class PostCloseDigest(StrictModel):
    digest_id: str
    trading_day: date | None = None
    previous_trading_day: date | None = None
    window: PreMarketWindow
    generated_at: datetime
    events: list[PreMarketEvent] = Field(default_factory=list)
    clusters: list[EventCluster] = Field(default_factory=list)
    event_clusters: list[EventCluster] = Field(default_factory=list)
    official_announcements: list[PreMarketEvent] = Field(default_factory=list)
    regulatory_events: list[PreMarketEvent] = Field(default_factory=list)
    policy_events: list[PreMarketEvent] = Field(default_factory=list)
    post_close_news: list[PreMarketEvent] = Field(default_factory=list)
    overseas_events: list[PreMarketEvent] = Field(default_factory=list)
    portfolio_impacts: list["PortfolioImpact"] = Field(default_factory=list)
    watch_candidates: list[dict[str, Any]] = Field(default_factory=list)
    avoid_candidates: list["AvoidItem"] = Field(default_factory=list)
    theme_seeds: list["ThemeCandidate"] = Field(default_factory=list)
    data_quality: dict[str, Any] = Field(default_factory=dict)
    risk_event_ids: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    summary: str


class MorningBrief(StrictModel):
    brief_id: str
    trading_day: date
    window: PreMarketWindow
    generated_at: datetime
    version: str = "1.0"
    market_view: Literal["positive", "neutral", "cautious"]
    market_mode: Literal[
        "normal",
        "risk_on",
        "risk_off",
        "news_driven",
        "macro_sensitive",
        "earnings_sensitive",
        "policy_sensitive",
        "unclear",
    ] = "normal"
    headline: str
    summary: str = ""
    post_close_digest: dict[str, Any] = Field(default_factory=dict)
    key_post_close_events: list[EventCluster] = Field(default_factory=list)
    announcement_events: list[PreMarketEvent] = Field(default_factory=list)
    policy_events: list[PreMarketEvent] = Field(default_factory=list)
    overnight_summary: list[PreMarketEvent] = Field(default_factory=list)
    macro_calendar: list["MacroCalendarItem"] = Field(default_factory=list)
    portfolio_impacts: list["PortfolioImpact"] = Field(default_factory=list)
    top_themes: list["ThemeCandidate"] = Field(default_factory=list)
    watchlist: list[dict[str, Any]] = Field(default_factory=list)
    avoid_list: list["AvoidItem"] = Field(default_factory=list)
    scenarios: list["ScenarioPlan"] = Field(default_factory=list)
    instructions_preview: list[dict[str, Any]] = Field(default_factory=list)
    data_quality: dict[str, Any] = Field(default_factory=dict)
    markdown_report: str = ""
    top_event_ids: list[str] = Field(default_factory=list)
    key_themes: list[str] = Field(default_factory=list)
    risk_event_ids: list[str] = Field(default_factory=list)
    watch_symbols: list[str] = Field(default_factory=list)
    avoid_symbols: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AuctionSignal(StrictModel):
    symbol: str
    observed_at: datetime
    phase: Literal["observation", "confirmation"]
    signal_type: Literal["watch_only", "confirmed_strength", "confirmed_weakness", "no_confirmation"]
    evidence_event_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    reason: str


class OpeningRadar(StrictModel):
    radar_id: str
    trading_day: date
    generated_at: datetime
    auction_window: str = "09:20-09:25"
    confirm_window_start: datetime
    confirm_window_end: datetime
    confirmed_themes: list[str] = Field(default_factory=list)
    failed_themes: list[str] = Field(default_factory=list)
    signals: list[AuctionSignal] = Field(default_factory=list)
    risk_alerts: list["OpeningRadarItem"] = Field(default_factory=list)
    watch_items: list["OpeningRadarItem"] = Field(default_factory=list)
    avoid_items: list["OpeningRadarItem"] = Field(default_factory=list)
    intraday_instructions: list[dict[str, Any]] = Field(default_factory=list)
    markdown_report: str = ""
    rejected_theme_event_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PositionItem(StrictModel):
    symbol: str
    quantity: int
    market_value: float
    avg_cost: float | None = None
    previous_close: float | None = None
    strategy_id: str | None = None


class PortfolioSnapshot(StrictModel):
    snapshot_id: str
    as_of: datetime
    cash: float | None = None
    nav: float | None = None
    positions: list[PositionItem] = Field(default_factory=list)


class WatchlistItem(StrictModel):
    symbol: str
    name: str | None = None
    themes: list[str] = Field(default_factory=list)
    strategy_ids: list[str] = Field(default_factory=list)
    priority: int = 0


class PortfolioImpact(StrictModel):
    symbol: str
    related_event_ids: list[str] = Field(default_factory=list)
    related_cluster_ids: list[str] = Field(default_factory=list)
    position_qty: int = 0
    position_value: float = 0.0
    avg_cost: float | None = None
    previous_close: float | None = None
    risk_level: Literal["none", "low", "medium", "high", "critical"]
    expected_bias: Bias
    suggested_action_type: Literal["watch", "avoid_new_entry", "reduce_only", "needs_manual_review", "normal"]
    reason: str
    confidence: float = Field(ge=0, le=1)


class MacroCalendarItem(StrictModel):
    item_id: str
    name: str
    source: str
    scheduled_at: datetime
    region: Literal["CN", "US", "EU", "JP", "HK", "GLOBAL"]
    importance: Importance
    affected_themes: list[str] = Field(default_factory=list)
    affected_symbols: list[str] = Field(default_factory=list)
    risk_window_start: datetime
    risk_window_end: datetime
    expected_market_impact: Literal["high_volatility", "sector_specific", "low", "unclear"]


class ThemeCandidate(StrictModel):
    theme_id: str
    theme_name: str
    rank: int
    score: float
    evidence_event_ids: list[str] = Field(default_factory=list)
    evidence_cluster_ids: list[str] = Field(default_factory=list)
    related_symbols: list[str] = Field(default_factory=list)
    catalyst_type: Literal["policy", "earnings", "overseas", "commodity", "news", "announcement", "technical", "mixed"]
    confidence: float = Field(ge=0, le=1)
    risk_flags: list[str] = Field(default_factory=list)


class AvoidItem(StrictModel):
    symbol: str
    reason: str
    risk_level: Literal["medium", "high", "critical"]
    related_event_ids: list[str] = Field(default_factory=list)
    related_cluster_ids: list[str] = Field(default_factory=list)
    restriction: Literal["no_new_entry", "reduce_only", "manual_approval_required"]


class ScenarioPlan(StrictModel):
    scenario_id: str
    name: str
    condition: str
    watch_symbols: list[str] = Field(default_factory=list)
    watch_themes: list[str] = Field(default_factory=list)
    valid_until: datetime
    action_for_intraday_agent: Literal[
        "normal_scan",
        "increase_attention",
        "require_confirmation",
        "reduce_size",
        "block_new_entry",
    ]
    evidence_event_ids: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)


class OpeningRadarItem(StrictModel):
    symbol: str
    theme: str | None = None
    auction_price: float | None = None
    auction_change_pct: float | None = None
    auction_amount: float | None = None
    auction_volume_ratio: float | None = None
    rank_in_watchlist: int | None = None
    signal: Literal[
        "confirmed_strength",
        "weak_confirmation",
        "gap_too_high",
        "unexpected_weakness",
        "risk_alert",
        "ignore",
    ]
    related_scenario_ids: list[str] = Field(default_factory=list)
    evidence_event_ids: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class PreMarketInstructionItem(StrictModel):
    instruction_type: InstructionType
    target: str
    reason: str
    evidence_event_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    expires_at: datetime
    requires_manual_review: bool = False

    @model_validator(mode="after")
    def require_evidence_or_source(self) -> "PreMarketInstructionItem":
        if not self.evidence_event_ids and not self.source_ids:
            raise ValueError("instruction items require evidence_event_ids or source_ids")
        return self


class PreMarketInstruction(StrictModel):
    instruction_id: str
    trading_day: date
    generated_at: datetime
    items: list[PreMarketInstructionItem] = Field(default_factory=list)
    blocked_terms: list[str] = Field(default_factory=lambda: ["buy", "sell", "order", "trade_intent"])
    source_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @field_validator("items")
    @classmethod
    def forbid_trade_words(cls, value: list[PreMarketInstructionItem]) -> list[PreMarketInstructionItem]:
        forbidden = ("buy", "sell", "order", "trade_intent")
        for item in value:
            body = f"{item.instruction_type} {item.target} {item.reason}".lower()
            if any(word in body for word in forbidden):
                raise ValueError("premarket instructions cannot contain trading command words")
        return value
