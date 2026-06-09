from __future__ import annotations

from trading_agent_system.core.strategy_registry import StrategyRegistry
from trading_agent_system.schemas import FeatureSnapshot, IntelBrief, MarketState, SignalCandidate


class SignalEngine:
    def evaluate(
        self,
        symbol: str,
        snapshot: FeatureSnapshot,
        market_state: MarketState,
        strategy_registry: StrategyRegistry,
        intel: list[IntelBrief],
        last_price: float,
    ) -> list[SignalCandidate]:
        candidates: list[SignalCandidate] = []
        intel_by_id = {brief.event_id: brief for brief in intel}
        for strategy, config in strategy_registry.enabled_for_symbol(symbol):
            if config.requires_intel_confirmation and not snapshot.related_intel_event_ids:
                continue
            blocked = False
            for event_id in snapshot.related_intel_event_ids:
                brief = intel_by_id.get(event_id)
                if brief and any(flag in config.blocked_risk_flags for flag in brief.risk_flags):
                    blocked = True
                    break
            if blocked:
                continue
            for candidate in strategy.evaluate(symbol, snapshot, market_state, {"last_price": last_price}):
                if candidate.side not in config.allowed_sides:
                    continue
                candidates.append(
                    candidate.model_copy(update={"confidence": min(candidate.confidence, config.max_confidence_cap)})
                )
        return candidates
