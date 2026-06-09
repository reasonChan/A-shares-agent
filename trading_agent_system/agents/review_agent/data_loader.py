from __future__ import annotations

from dataclasses import dataclass, field

from trading_agent_system.schemas import (
    BrokerOrder,
    Fill,
    IntelBrief,
    MarketBar,
    OrderInstruction,
    RiskDecision,
    TradeIntent,
    TradeReviewContext,
)


@dataclass
class ReviewDataset:
    intel: list[IntelBrief] = field(default_factory=list)
    intents: list[TradeIntent] = field(default_factory=list)
    decisions: list[RiskDecision] = field(default_factory=list)
    instructions: list[OrderInstruction] = field(default_factory=list)
    submitted: list[BrokerOrder] = field(default_factory=list)
    fills: list[Fill] = field(default_factory=list)
    cancelled: list[BrokerOrder] = field(default_factory=list)
    rejected: list[BrokerOrder] = field(default_factory=list)
    bars: list[MarketBar] = field(default_factory=list)


class ReviewDataLoader:
    def build_contexts(self, dataset: ReviewDataset) -> list[TradeReviewContext]:
        decisions = {decision.intent_id: decision for decision in dataset.decisions}
        instructions = {instruction.intent_id: instruction for instruction in dataset.instructions}
        fills_by_intent: dict[str, list[Fill]] = {}
        for fill in dataset.fills:
            fills_by_intent.setdefault(fill.intent_id, []).append(fill)
        contexts: list[TradeReviewContext] = []
        for intent in dataset.intents:
            related_intel = [brief for brief in dataset.intel if brief.event_id in intent.evidence_ids]
            contexts.append(
                TradeReviewContext(
                    trade_id=intent.intent_id,
                    intent=intent,
                    risk_decision=decisions.get(intent.intent_id),
                    order_instruction=instructions.get(intent.intent_id),
                    fills=fills_by_intent.get(intent.intent_id, []),
                    related_intel=related_intel,
                    market_before=[bar for bar in dataset.bars if bar.symbol == intent.symbol][:5],
                    market_after=[bar for bar in dataset.bars if bar.symbol == intent.symbol][-10:],
                    strategy_config={},
                )
            )
        return contexts
