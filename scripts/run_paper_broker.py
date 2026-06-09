from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone

from trading_agent_system.core.audit import AuditLedger
from trading_agent_system.core.broker import PaperBroker
from trading_agent_system.core.config import load_yaml_config
from trading_agent_system.core.event_bus import MemoryEventBus
from trading_agent_system.schemas import MarketBar, OrderInstruction


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/app.yaml")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    app_config = load_yaml_config(args.config)
    broker_config = app_config["paper_broker"]
    bus = MemoryEventBus()
    audit = AuditLedger("data/audit/paper_broker.jsonl")
    broker = PaperBroker(
        event_bus=bus,
        audit=audit,
        initial_cash=broker_config["initial_cash"],
        commission_bps=broker_config["commission_bps"],
        slippage_bps=broker_config["slippage_bps"],
        allow_partial_fill=broker_config["allow_partial_fill"],
    )
    if args.demo:
        instruction = OrderInstruction(
            decision_id="risk_demo",
            intent_id="intent_demo",
            symbol="510300.SH",
            side="buy",
            quantity=100,
            order_type="limit",
            limit_price=3.11,
            ttl_seconds=60,
        )
        broker.on_order_instruction(instruction)
        fills = broker.on_market_bar(
            MarketBar(
                symbol="510300.SH",
                ts=datetime.now(timezone.utc) + timedelta(seconds=1),
                open=3.10,
                high=3.12,
                low=3.09,
                close=3.11,
                volume=6000,
            )
        )
        print(json.dumps([fill.model_dump(mode="json") for fill in fills], ensure_ascii=False, indent=2))
        print(f"account.snapshots={len(bus.events('account.snapshots'))}")
    else:
        print("PaperBroker initialized. Use --demo for a local smoke run.")


if __name__ == "__main__":
    main()
