from __future__ import annotations

from typing import Any

from trading_agent_system.schemas import FeatureSnapshot, MarketState, SignalCandidate

from .base import BaseStrategy


class BreakoutV1(BaseStrategy):
    strategy_id = "breakout_v1"
    version = "1.0.0"

    def evaluate(
        self,
        symbol: str,
        snapshot: FeatureSnapshot,
        market_state: MarketState,
        context: dict[str, Any],
    ) -> list[SignalCandidate]:
        f = snapshot.features
        if market_state.risk_mode != "normal":
            return []
        if (
            float(f.get("return_5m", 0)) > 0.02
            and float(f.get("volume_ratio_5m", 0)) > 3
            and bool(f.get("intraday_high_break", False))
        ):
            price = context.get("last_price")
            return [
                SignalCandidate(
                    strategy_id=self.strategy_id,
                    strategy_version=self.version,
                    symbol=symbol,
                    side="buy",
                    raw_score=0.72,
                    confidence=0.65,
                    reasons=["5分钟涨幅超过阈值", "成交量显著放大", "突破日内高点"],
                    feature_snapshot_id=snapshot.snapshot_id,
                    evidence_ids=snapshot.related_intel_event_ids,
                    suggested_quantity=100,
                    suggested_limit_price=price,
                    invalidation={"price_below_vwap": True, "market_data_delay_ms_above": 1000},
                )
            ]
        return []
