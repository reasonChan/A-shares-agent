# A股 Agent MVP

This repository implements a safe paper-trading MVP for the pasted A-share trading-agent specification.

The default loop is:

```text
IntelBrief / MarketBar
  -> IntradayAgent
  -> trading.intents
  -> RiskGateway
  -> risk.decisions + orders.instructions
  -> PaperBroker
  -> orders.filled + account/position snapshots
  -> ReviewAgent daily reports
```

Safety defaults:

- Paper trading only.
- `trading_enabled: false`.
- `require_human_approval: true`.
- No real broker adapter.
- `RiskGateway` is deterministic and does not call an LLM.
- `IntradayAgent` never publishes `orders.instructions`.
- Review output is advisory and never mutates strategy config.

## Quick Start

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .

python scripts/run_intraday_agent.py --config configs/app.yaml --demo
python scripts/run_risk_gateway.py --config configs/risk.paper.yaml --demo
python scripts/run_paper_broker.py --config configs/app.yaml --demo
python scripts/run_review_agent.py --date 2026-06-09 --config configs/app.yaml --demo
```

Reports are written to `reports/daily/`.

## Web Console

Start the local API:

```bash
. .venv/bin/activate
pip install -e .
python scripts/run_api.py --port 8000
```

Start the React console in another terminal:

```bash
cd web
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.
