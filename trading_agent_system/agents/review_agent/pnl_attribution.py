from __future__ import annotations

from trading_agent_system.schemas import Fill, PnLSummary, TradeIntent, TradeReviewContext


class PnLAttribution:
    def calculate(self, contexts: list[TradeReviewContext]) -> PnLSummary:
        fees = sum(fill.commission for context in contexts for fill in context.fills)
        pnl_by_symbol: dict[str, float] = {}
        pnl_by_strategy: dict[str, float] = {}
        open_buy_costs: dict[str, list[Fill]] = {}
        realized = 0.0
        for context in contexts:
            strategy_pnl = 0.0
            for fill in context.fills:
                if fill.side == "buy":
                    open_buy_costs.setdefault(fill.symbol, []).append(fill)
                    pnl_by_symbol.setdefault(fill.symbol, 0.0)
                    continue
                realized_piece = self._match_sell(fill, open_buy_costs)
                realized += realized_piece
                strategy_pnl += realized_piece
                pnl_by_symbol[fill.symbol] = pnl_by_symbol.get(fill.symbol, 0.0) + realized_piece
            pnl_by_strategy[context.intent.strategy_id] = pnl_by_strategy.get(context.intent.strategy_id, 0.0) + strategy_pnl
        return PnLSummary(
            gross_pnl=realized,
            net_pnl=realized - fees,
            fees=fees,
            slippage=sum(abs(fill.price) * fill.quantity * fill.slippage_bps / 10000 for context in contexts for fill in context.fills),
            realized_pnl=realized - fees,
            unrealized_pnl=0,
            pnl_by_strategy=pnl_by_strategy,
            pnl_by_symbol=pnl_by_symbol,
        )

    def _match_sell(self, sell: Fill, open_buy_costs: dict[str, list[Fill]]) -> float:
        remaining = sell.quantity
        pnl = 0.0
        buys = open_buy_costs.get(sell.symbol, [])
        while remaining > 0 and buys:
            buy = buys[0]
            matched = min(remaining, buy.quantity)
            pnl += (sell.price - buy.price) * matched - sell.commission
            remaining -= matched
            if matched == buy.quantity:
                buys.pop(0)
            else:
                buys[0] = buy.model_copy(update={"quantity": buy.quantity - matched})
        return pnl
