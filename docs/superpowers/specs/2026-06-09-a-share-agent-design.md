# A-Share Agent Design

## Goal

Build a Python 3.11+ MVP for a safe A-share paper-trading agent system based on the pasted technical specification. The implementation must not include tests because the user explicitly requested no tests.

## Architecture

The system is split into four service families and shared core modules:

- `IntradayAgent` reads market bars, intel, positions, account snapshots, and strategy config, then publishes only `trading.intents`.
- `RiskGateway` is the only component allowed to convert `TradeIntent` into `OrderInstruction`. It is deterministic and never calls an LLM.
- `PaperBroker` consumes only `orders.instructions`, simulates order lifecycle and fills, then publishes account and position snapshots.
- `ReviewAgent` reads events and audit data to create JSON and Markdown daily reports. It can propose strategy status changes but never applies them.

The first delivery uses an in-memory event bus and JSONL audit/event repositories. This keeps the MVP runnable locally while preserving the boundaries needed to replace the bus with Redis Streams, Kafka, or RabbitMQ later.

## Safety Defaults

- `environment: paper`.
- `trading_enabled: false`.
- `require_human_approval: true`.
- Real broker credentials are not modeled.
- `RiskGateway` rejects or requires approval before an order instruction can be emitted.
- `StrategyHealth.auto_apply` is always false.

## Data Flow

```text
IntelBrief / MarketBar
  -> IntradayAgent
  -> trading.intents
  -> RiskGateway
  -> risk.decisions + orders.instructions
  -> PaperBroker
  -> orders.submitted/orders.filled/positions.snapshots/account.snapshots
  -> ReviewAgent
  -> review.daily + reports/daily/YYYY-MM-DD.{json,md}
```

## Implementation Scope

The MVP includes:

- Pydantic schemas for shared events.
- In-memory event bus.
- JSONL audit ledger.
- YAML config loader.
- Risk checks for global trading state, kill switch, stale data, strategy/symbol blacklists, order type, price band, lot size, cash, position limit, duplicate intents, open order limit, liquidity, and human approval.
- Paper broker with simple next-bar fill behavior.
- Strategy registry with `breakout_v1`.
- Intraday feature builder and trade planner.
- Review report writer with PnL, execution, signal, intel, risk, and strategy-health sections.
- CLI scripts with `--demo` mode for smoke verification.

## Out of Scope

- Tests.
- Real broker integration.
- Live market data adapters.
- Redis/Kafka persistence.
- LLM calls.
- Automatic strategy config mutation.
