from __future__ import annotations

from trading_agent_system.schemas import PositionSnapshot, TradeIntent


class PositionGuardian:
    def build_reduce_intents(self, positions: PositionSnapshot) -> list[TradeIntent]:
        return []
