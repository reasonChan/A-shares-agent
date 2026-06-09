from __future__ import annotations

from trading_agent_system.schemas import IntelBrief, IntelQualityResult, TradeReviewContext


class IntelQualityReview:
    def evaluate(self, intel: list[IntelBrief], contexts: list[TradeReviewContext]) -> list[IntelQualityResult]:
        results: list[IntelQualityResult] = []
        for brief in intel:
            related = [context for context in contexts if brief.event_id in context.intent.evidence_ids]
            related_pnl = sum(sum((fill.price * fill.quantity) for fill in context.fills) for context in related)
            diagnosis = []
            if "unverified" in brief.risk_flags or "rumor" in brief.risk_flags:
                diagnosis.append("risk_flagged_intel")
            if not related:
                diagnosis.append("no_related_trade")
            results.append(
                IntelQualityResult(
                    event_id=brief.event_id,
                    symbols=brief.symbols,
                    event_type=brief.event_type,
                    importance=brief.importance,
                    original_bias=brief.bias,
                    confirmed_later=False,
                    related_trade_count=len(related),
                    related_pnl=related_pnl,
                    diagnosis=diagnosis,
                )
            )
        return results
