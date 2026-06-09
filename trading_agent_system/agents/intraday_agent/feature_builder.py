from __future__ import annotations

from datetime import datetime, timezone

from trading_agent_system.schemas import FeatureSnapshot, IntelBrief, MarketBar, MarketState


class FeatureBuilder:
    def build(
        self,
        symbol: str,
        bars: list[MarketBar],
        intel: list[IntelBrief],
        market_state: MarketState,
    ) -> FeatureSnapshot:
        if not bars:
            raise ValueError(f"no bars for {symbol}")
        latest = bars[-1]
        close_5m_ago = bars[-6].close if len(bars) >= 6 else bars[0].close
        close_1m_ago = bars[-2].close if len(bars) >= 2 else bars[0].close
        avg_volume_5 = sum(bar.volume for bar in bars[-6:-1]) / max(1, len(bars[-6:-1]))
        intraday_high = max(bar.high for bar in bars[:-1]) if len(bars) > 1 else latest.high
        recent_intel = [brief for brief in intel if symbol in brief.symbols]
        bullish = sum(brief.confidence for brief in recent_intel if brief.bias == "bullish")
        bearish = sum(brief.confidence for brief in recent_intel if brief.bias == "bearish")
        features = {
            "return_1m": (latest.close - close_1m_ago) / close_1m_ago if close_1m_ago else 0,
            "return_5m": (latest.close - close_5m_ago) / close_5m_ago if close_5m_ago else 0,
            "return_15m": (latest.close - bars[0].close) / bars[0].close if bars[0].close else 0,
            "volume_ratio_5m": latest.volume / avg_volume_5 if avg_volume_5 else 0,
            "volume_ratio_20d_same_minute": latest.volume / avg_volume_5 if avg_volume_5 else 0,
            "intraday_high_break": latest.high > intraday_high,
            "intraday_low_break": latest.low < min(bar.low for bar in bars[:-1]) if len(bars) > 1 else False,
            "vwap_distance": 0.0,
            "realized_volatility": abs((latest.close - close_5m_ago) / close_5m_ago) if close_5m_ago else 0,
            "spread_bps": 0.0,
            "order_book_imbalance": 0.0,
            "recent_intel_count": len(recent_intel),
            "recent_bullish_intel_score": bullish,
            "recent_bearish_intel_score": bearish,
            "market_regime": market_state.regime,
        }
        return FeatureSnapshot(
            symbol=symbol,
            ts=latest.ts if latest.ts else datetime.now(timezone.utc),
            features=features,
            related_intel_event_ids=[brief.event_id for brief in recent_intel],
        )
