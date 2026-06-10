from datetime import date, datetime, timezone

from trading_agent_system.agents.premarket_agent import PremarketAgent
from trading_agent_system.agents.premarket_agent.news_provider import NewsProviderResult
from trading_agent_system.agents.premarket_agent.rag.rag_service import PreMarketRAGService
from trading_agent_system.agents.premarket_agent.trading_calendar import TradingCalendarService
from trading_agent_system.core.audit import AuditLedger
from trading_agent_system.core.event_bus import MemoryEventBus
from trading_agent_system.schemas import PremarketNewsItem


class LocalProvider:
    source = "local"

    def fetch(self, limit: int = 30) -> NewsProviderResult:
        return NewsProviderResult(
            self.source,
            [
                PremarketNewsItem(
                    source="local professional",
                    source_tier="professional",
                    title="机器人政策催化",
                    summary="机器人产业政策催化。",
                    published_at=datetime(2026, 6, 8, 16, 0, tzinfo=timezone.utc),
                    category="official_policy",
                    sectors=["机器人"],
                    credibility=0.82,
                )
            ],
            "ok",
        )


def test_premarket_agent_publishes_rag_evidence_packs(tmp_path):
    bus = MemoryEventBus()
    agent = PremarketAgent(
        event_bus=bus,
        audit=AuditLedger(tmp_path / "audit.jsonl"),
        providers=[LocalProvider()],
        calendar=TradingCalendarService(),
        premarket_rag_service=PreMarketRAGService.local(
            qdrant_path=tmp_path / "qdrant",
            collection_name="premarket_hot",
            embedding_dimension=32,
        ),
    )

    agent.run(date(2026, 6, 9), limit_per_source=5)

    packs = bus.events("premarket.rag_evidence_packs")
    assert packs
    assert packs[0]["pack_count"] > 0
    assert any(pack["items"] for pack in packs[0]["packs"])
