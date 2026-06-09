# A-Share Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the pasted A-share trading-agent MVP without writing tests.

**Architecture:** Create a Python package with shared schemas, event bus, audit ledger, deterministic risk gateway, paper broker, intraday agent, and review agent. Use YAML configs and JSONL artifacts for local paper-trading runs.

**Tech Stack:** Python 3.11+, Pydantic v2, PyYAML, standard-library JSONL persistence.

---

### Task 1: Project Metadata And Documentation

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `docs/superpowers/specs/2026-06-09-a-share-agent-design.md`
- Create: `docs/superpowers/plans/2026-06-09-a-share-agent.md`

- [x] Define package metadata and dependencies.
- [x] Record the design and no-tests constraint.
- [x] Record the implementation plan.

### Task 2: Shared Core

**Files:**
- Create package `trading_agent_system`
- Create schemas, bus, audit, repositories, and config loader.

- [x] Implement all Pydantic schemas from the pasted specification.
- [x] Implement `MemoryEventBus`.
- [x] Implement `AuditLedger`.
- [x] Implement JSONL repositories.
- [x] Implement YAML config loading.

### Task 3: Risk Gateway

**Files:**
- Create `trading_agent_system/core/risk_gateway/*`

- [x] Implement deterministic checks.
- [x] Implement risk state context.
- [x] Implement `RiskGateway.on_trade_intent`.
- [x] Ensure approved decisions emit `orders.instructions`.
- [x] Ensure rejected and approval-needed decisions do not emit orders.

### Task 4: Paper Broker

**Files:**
- Create `trading_agent_system/core/broker/*`

- [x] Implement order state machine.
- [x] Implement next-bar fill rules.
- [x] Update positions and account snapshots after fills.
- [x] Emit order and account events.

### Task 5: Intraday Agent And Strategies

**Files:**
- Create `trading_agent_system/agents/intraday_agent/*`
- Create `trading_agent_system/core/strategy_registry/*`

- [x] Implement market state monitor.
- [x] Implement feature builder.
- [x] Implement strategy registry.
- [x] Implement `breakout_v1`.
- [x] Implement signal engine and trade planner.
- [x] Ensure intraday publishes only `trading.intents`.

### Task 6: Review Agent

**Files:**
- Create `trading_agent_system/agents/review_agent/*`

- [x] Load daily events.
- [x] Link intents, risk decisions, order instructions, fills, and intel.
- [x] Compute PnL and execution metrics.
- [x] Generate JSON and Markdown daily reports.
- [x] Ensure strategy proposals use `auto_apply=false`.

### Task 7: Scripts And Configs

**Files:**
- Create `configs/*.yaml`
- Create `scripts/*.py`

- [x] Add safe default configs.
- [x] Add demo-capable entry points.
- [x] Verify with compile and demo commands instead of tests.
