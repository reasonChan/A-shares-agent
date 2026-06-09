from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone

from trading_agent_system.agents.review_agent import ReviewAgent
from trading_agent_system.agents.review_agent.data_loader import ReviewDataset
from trading_agent_system.core.audit import AuditLedger
from trading_agent_system.core.config import load_yaml_config
from trading_agent_system.schemas import Fill, IntelBrief, MarketBar, OrderInstruction, RiskDecision, TradeIntent


def build_demo_dataset() -> ReviewDataset:
    now = datetime.now(timezone.utc)
    intel = IntelBrief(
        first_seen_at=now,
        symbols=["510300.SH"],
        event_type="official_policy",
        importance="A",
        bias="bullish",
        confidence=0.72,
        actionability="candidate",
        summary="Demo intel.",
        evidence=[{"source": "demo"}],
    )
    intent = TradeIntent(
        strategy_id="breakout_v1",
        strategy_version="1.0.0",
        symbol="510300.SH",
        side="buy",
        quantity=100,
        order_type="limit",
        limit_price=3.11,
        confidence=0.65,
        entry_reason=["demo breakout"],
        evidence_ids=[intel.event_id],
        feature_snapshot_id="demo_feature",
        created_at=now,
    )
    decision = RiskDecision(
        intent_id=intent.intent_id,
        decision="approved",
        approved_quantity=100,
        approved_price=3.11,
        reason="approved",
        checks={},
    )
    instruction = OrderInstruction(
        decision_id=decision.decision_id,
        intent_id=intent.intent_id,
        symbol=intent.symbol,
        side=intent.side,
        quantity=100,
        order_type="limit",
        limit_price=3.11,
        ttl_seconds=30,
    )
    fill = Fill(
        order_id="order_demo",
        order_instruction_id=instruction.order_instruction_id,
        decision_id=decision.decision_id,
        intent_id=intent.intent_id,
        symbol=intent.symbol,
        side="buy",
        quantity=100,
        price=3.111,
        commission=0.06,
        slippage_bps=3,
        ts=now,
    )
    bars = [
        MarketBar(symbol="510300.SH", ts=now, open=3.10, high=3.13, low=3.09, close=3.12, volume=6000),
        MarketBar(symbol="510300.SH", ts=now, open=3.12, high=3.16, low=3.11, close=3.15, volume=7000),
    ]
    return ReviewDataset(
        intel=[intel],
        intents=[intent],
        decisions=[decision],
        instructions=[instruction],
        fills=[fill],
        bars=bars,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--config", default="configs/app.yaml")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    app_config = load_yaml_config(args.config)
    audit = AuditLedger("data/audit/review_agent.jsonl")
    agent = ReviewAgent(audit=audit)
    report_date = date.fromisoformat(args.date)
    dataset = build_demo_dataset() if args.demo else ReviewDataset()
    report = agent.run_daily(report_date, dataset)
    print(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2))
    print(f"report_dir={app_config['paths']['reports']}")


if __name__ == "__main__":
    main()
