from __future__ import annotations

from trading_agent_system.schemas import ExecutionMetrics, TradeReviewContext


class ExecutionReview:
    def calculate(self, contexts: list[TradeReviewContext]) -> ExecutionMetrics:
        total = len(contexts)
        if total == 0:
            return ExecutionMetrics(warnings=["no_trade_intents"])
        filled_contexts = [context for context in contexts if context.fills]
        rejected = [context for context in contexts if context.risk_decision and context.risk_decision.decision == "rejected"]
        slippages = [fill.slippage_bps for context in contexts for fill in context.fills]
        delays = []
        intel_delays = []
        for context in filled_contexts:
            first_fill = context.fills[0]
            delays.append((first_fill.ts - context.intent.created_at).total_seconds())
            if context.related_intel:
                first_seen = min(brief.first_seen_at for brief in context.related_intel)
                intel_delays.append((context.intent.created_at - first_seen).total_seconds())
        return ExecutionMetrics(
            fill_rate=len(filled_contexts) / total,
            cancel_rate=0,
            reject_rate=len(rejected) / total,
            avg_slippage_bps=sum(slippages) / len(slippages) if slippages else 0,
            max_slippage_bps=max(slippages) if slippages else 0,
            avg_intent_to_fill_seconds=sum(delays) / len(delays) if delays else 0,
            avg_intel_to_intent_seconds=sum(intel_delays) / len(intel_delays) if intel_delays else 0,
            warnings=[],
        )
