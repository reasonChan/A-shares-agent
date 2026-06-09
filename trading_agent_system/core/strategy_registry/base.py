from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from trading_agent_system.schemas import FeatureSnapshot, MarketState, SignalCandidate


class BaseStrategy(ABC):
    strategy_id: str
    version: str

    @abstractmethod
    def evaluate(
        self,
        symbol: str,
        snapshot: FeatureSnapshot,
        market_state: MarketState,
        context: dict[str, Any],
    ) -> list[SignalCandidate]:
        raise NotImplementedError
