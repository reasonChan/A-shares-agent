from __future__ import annotations

from datetime import datetime, timezone

from trading_agent_system.schemas import IntelBrief, MarketBar, MarketState


class MarketStateMonitor:
    def __init__(self, max_delay_ms: int = 1000) -> None:
        self.max_delay_ms = max_delay_ms

    def build(
        self,
        bars: dict[str, list[MarketBar]],
        delays_ms: dict[str, int],
        recent_intel: list[IntelBrief],
    ) -> MarketState:
        active_bars = {symbol: symbol_bars for symbol, symbol_bars in bars.items() if symbol_bars}
        if not active_bars:
            return MarketState(
                ts=datetime.now(timezone.utc),
                regime="data_missing",
                volatility_level="normal",
                liquidity_level="normal",
                data_quality="missing",
                risk_mode="halt_new_entries",
                reasons=["missing_market_bars"],
            )
        stale_symbols = [
            symbol
            for symbol in active_bars
            if delays_ms.get(symbol, self.max_delay_ms + 1) > self.max_delay_ms
        ]
        if stale_symbols:
            return MarketState(
                ts=datetime.now(timezone.utc),
                regime="data_stale",
                volatility_level="normal",
                liquidity_level="normal",
                data_quality="stale",
                risk_mode="halt_new_entries",
                reasons=[f"stale_market_data:{','.join(stale_symbols)}"],
            )
        latest_returns = []
        for symbol_bars in active_bars.values():
            if len(symbol_bars) >= 2 and symbol_bars[-2].close:
                latest_returns.append((symbol_bars[-1].close - symbol_bars[-2].close) / symbol_bars[-2].close)
        max_abs_return = max([abs(item) for item in latest_returns], default=0)
        news_driven = len(recent_intel) >= 3
        return MarketState(
            ts=datetime.now(timezone.utc),
            regime="news_driven" if news_driven else ("volatile" if max_abs_return > 0.02 else "normal"),
            volatility_level="high" if max_abs_return > 0.02 else "normal",
            liquidity_level="normal",
            data_quality="ok",
            risk_mode="reduced" if max_abs_return > 0.05 else "normal",
            reasons=["recent_intel_cluster"] if news_driven else [],
        )
