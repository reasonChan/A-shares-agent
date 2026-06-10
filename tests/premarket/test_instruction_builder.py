from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from trading_agent_system.agents.premarket_agent import PremarketAgent
from trading_agent_system.agents.premarket_agent.news_provider import NewsProviderResult
from trading_agent_system.agents.premarket_agent.trading_calendar import TradingCalendarService
from trading_agent_system.core.audit import AuditLedger
from trading_agent_system.core.event_bus import MemoryEventBus
from trading_agent_system.agents.premarket_agent.schemas import (
    InstructionType,
    PreMarketInstruction,
    PreMarketInstructionItem,
)


class EmptyProvider:
    source = "empty"

    def fetch(self, limit: int = 30) -> NewsProviderResult:
        return NewsProviderResult(self.source, [], "empty")


def test_instruction_item_requires_evidence_or_source():
    expires_at = datetime(2026, 6, 9, 9, 30, tzinfo=ZoneInfo("Asia/Shanghai"))

    with pytest.raises(ValueError):
        PreMarketInstructionItem(
            instruction_type=InstructionType.WATCH_OPENING_AUCTION,
            target="板块:半导体",
            reason="等待竞价确认",
            expires_at=expires_at,
        )


def test_instruction_rejects_trading_command_words():
    expires_at = datetime(2026, 6, 9, 9, 30, tzinfo=ZoneInfo("Asia/Shanghai"))

    with pytest.raises(ValueError):
        PreMarketInstruction(
            instruction_id="pmins_test",
            trading_day=date(2026, 6, 9),
            generated_at=expires_at,
            source_ids=["source_1"],
            items=[
                PreMarketInstructionItem(
                    instruction_type=InstructionType.REQUIRE_CONFIRMATION,
                    target="ALL",
                    reason="do not buy before confirmation",
                    source_ids=["source_1"],
                    expires_at=expires_at,
                )
            ],
        )


def test_premarket_agent_empty_window_instruction_keeps_system_evidence(tmp_path):
    agent = PremarketAgent(
        event_bus=MemoryEventBus(),
        audit=AuditLedger(tmp_path / "audit.jsonl"),
        providers=[EmptyProvider()],
        calendar=TradingCalendarService(),
    )

    report = agent.run(date(2026, 6, 10), limit_per_source=5)

    avoid_items = [
        item
        for item in (report.instruction or {}).get("items", [])
        if item["instruction_type"] == InstructionType.AVOID_NEW_ENTRY.value
    ]
    assert avoid_items
    assert all(item["source_ids"] or item["evidence_event_ids"] for item in avoid_items)
    assert any("system" in item["source_ids"] for item in avoid_items)
