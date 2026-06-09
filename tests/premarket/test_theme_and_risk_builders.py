from datetime import datetime
from zoneinfo import ZoneInfo

from trading_agent_system.agents.premarket_agent.builders import RiskFilter, ThemeDetector
from trading_agent_system.agents.premarket_agent.pipeline import EventClusterer
from trading_agent_system.agents.premarket_agent.schemas import Actionability, Bias, Importance, PreMarketEvent, SourceRank


def make_event(
    title: str,
    *,
    theme: str = "机器人",
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
        confidence=0.82,
        actionability=Actionability.WATCH if bias != Bias.BEARISH else Actionability.BLOCK,
        risk_flags=risk_flags or [],
    )


def test_theme_detector_builds_ranked_theme_candidates():
    clusters = EventClusterer().cluster([make_event("人形机器人订单增长"), make_event("机器人产业政策支持")])

    themes = ThemeDetector().detect(clusters)

    assert themes
    assert themes[0].theme_name == "机器人"
    assert themes[0].rank == 1
    assert themes[0].evidence_cluster_ids


def test_risk_filter_builds_avoid_candidates_from_bearish_or_risky_clusters():
    clusters = EventClusterer().cluster([make_event("机器人公司收到监管函", bias=Bias.BEARISH, risk_flags=["监管函"])])

    avoid_items = RiskFilter().build_avoid_candidates(clusters)

    assert avoid_items
    assert avoid_items[0].restriction == "no_new_entry"
    assert avoid_items[0].related_event_ids
