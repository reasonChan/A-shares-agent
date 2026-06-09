from __future__ import annotations

from trading_agent_system.schemas import SignalQualityResult, TradeReviewContext


class SignalReview:
    def evaluate(self, contexts: list[TradeReviewContext]) -> list[SignalQualityResult]:
        results: list[SignalQualityResult] = []
        for context in contexts:
            after_prices = [bar.close for bar in context.market_after]
            entry_price = context.fills[0].price if context.fills else None
            if entry_price and after_prices:
                returns = [(price - entry_price) / entry_price * 10000 for price in after_prices]
                mfe = max(returns)
                mae = min(returns)
            else:
                mfe = mae = 0
            results.append(
                SignalQualityResult(
                    intent_id=context.intent.intent_id,
                    symbol=context.intent.symbol,
                    strategy_id=context.intent.strategy_id,
                    mfe_bps=mfe,
                    mae_bps=mae,
                    return_after_5m_bps=after_prices[4] / entry_price * 10000 - 10000 if entry_price and len(after_prices) > 4 else 0,
                    return_after_15m_bps=0,
                    return_after_30m_bps=0,
                    diagnosis=["post_trade_analysis"],
                )
            )
        return results
