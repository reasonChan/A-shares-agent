from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from trading_agent_system.agents.premarket_agent.schemas import (
    InstructionType,
    PreMarketInstruction,
    PreMarketInstructionItem,
)


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
