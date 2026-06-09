from datetime import datetime
from zoneinfo import ZoneInfo

from trading_agent_system.agents.premarket_agent.pipeline import EventClusterer
from trading_agent_system.agents.premarket_agent.schemas import Actionability, Bias, Importance, PreMarketEvent, SourceRank


def make_event(
    title: str,
    *,
    theme: str = "半导体",
    bias: Bias = Bias.BULLISH,
    risk_flags: list[str] | None = None,
) -> PreMarketEvent:
    now = datetime(2026, 6, 9, 8, 30, tzinfo=ZoneInfo("Asia/Shanghai"))
    return PreMarketEvent(
        event_id=f"evt_{title}",
        source_ids=[f"src_{title}"],
        source_rank=SourceRank.AUTHORIZED_NEWS,
        title=title,
        summary=title,
        published_at=now,
        first_seen_at=now,
        last_updated_at=now,
        event_type="industry_catalyst",
        related_themes=[theme],
        importance=Importance.A,
        bias=bias,
        confidence=0.8,
        actionability=Actionability.WATCH if bias != Bias.BEARISH else Actionability.BLOCK,
        risk_flags=risk_flags or [],
    )


def test_event_clusterer_keeps_theme_semantics_in_title():
    clusters = EventClusterer().cluster([make_event("芯片设备订单增长"), make_event("半导体融资支持")])

    assert len(clusters) == 1
    assert clusters[0].title.startswith("半导体:")
    assert clusters[0].evidence_count == 2
