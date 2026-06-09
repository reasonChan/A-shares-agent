from __future__ import annotations

from trading_agent_system.schemas import RiskReviewResult, TradeReviewContext


class RiskReview:
    def evaluate(self, contexts: list[TradeReviewContext]) -> RiskReviewResult:
        rejected_count = 0
        needs_human = 0
        scaled_down = 0
        breaches: list[dict] = []
        for context in contexts:
            decision = context.risk_decision
            if not decision:
                breaches.append({"intent_id": context.intent.intent_id, "reason": "missing_risk_decision"})
                continue
            if decision.decision == "rejected":
                rejected_count += 1
            if decision.decision == "needs_human_approval":
                needs_human += 1
            if any(result.status == "scale_down" for result in decision.checks.values()):
                scaled_down += 1
        return RiskReviewResult(
            rejected_count=rejected_count,
            needs_human_approval_count=needs_human,
            scaled_down_count=scaled_down,
            kill_switch_triggered=any(
                decision.risk_decision
                and any(result.reason == "kill_switch_enabled" for result in decision.risk_decision.checks.values())
                for decision in contexts
            ),
            risk_breaches=breaches,
            suspicious_patterns=[],
        )
