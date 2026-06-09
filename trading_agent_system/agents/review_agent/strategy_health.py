from __future__ import annotations

from collections import defaultdict

from trading_agent_system.schemas import PnLSummary, StrategyHealth, TradeReviewContext


class StrategyHealthEvaluator:
    def evaluate(self, contexts: list[TradeReviewContext], pnl: PnLSummary) -> list[StrategyHealth]:
        versions: dict[str, str] = {}
        counts: dict[str, int] = defaultdict(int)
        for context in contexts:
            versions[context.intent.strategy_id] = context.intent.strategy_version
            counts[context.intent.strategy_id] += 1
        health: list[StrategyHealth] = []
        for strategy_id, count in counts.items():
            strategy_pnl = pnl.pnl_by_strategy.get(strategy_id, 0)
            if count < 5:
                recommendation = "keep"
                reasons = ["sample_size_small", "requires_more_paper_trading"]
            elif strategy_pnl < 0:
                recommendation = "reduce_size"
                reasons = ["negative_net_pnl"]
            else:
                recommendation = "keep"
                reasons = ["paper_metrics_acceptable"]
            health.append(
                StrategyHealth(
                    strategy_id=strategy_id,
                    strategy_version=versions[strategy_id],
                    status_recommendation=recommendation,
                    reasons=reasons,
                    metrics={"trade_count": count, "strategy_pnl": strategy_pnl},
                    requires_backtest=True,
                    auto_apply=False,
                )
            )
        return health
