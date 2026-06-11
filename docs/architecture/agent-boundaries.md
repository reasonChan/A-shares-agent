# Agent Boundaries

This document explains the current functional boundaries of the A-share Agent MVP. It describes the implemented mental model, not a future ideal architecture.

## 交易流水线

```text
盘前分析 -> 盘中扫描 -> 风控审批 -> 模拟执行 -> 盘后复盘
PremarketAgent -> IntradayAgent -> RiskGateway -> PaperBroker -> ReviewAgent
```

| Stage | Module | Type | Responsibility |
| --- | --- | --- | --- |
| 盘前分析 | `PremarketAgent` | Agent | Build the premarket view, catalysts, watchlist, avoid list, and opening constraints. |
| 盘中扫描 | `IntradayAgent` | Agent | Read market data and premarket constraints, then produce candidate signals and trading intents. |
| 风控审批 | `RiskGateway` | Service | Apply deterministic safety checks and produce decisions or approval requests. RiskGateway 不是 Agent. |
| 模拟执行 | `PaperBroker` | Service | Convert approved paper instructions into simulated fills and account snapshots. PaperBroker 不是 Agent. |
| 盘后复盘 | `ReviewAgent` | Agent | Review signals, risk decisions, executions, PnL, and information quality. |

## 盘前知识系统

```text
信息源 -> 事件抽取 -> RAG 证据 -> 规则/历史案例 -> 盘前约束
```

RAG、信息源、知识库、PremarketContext 是能力模块，不是独立业务 Agent。它们支撑 `PremarketAgent`，并把盘前结论沉淀成盘中可使用的上下文。

| Capability | Current Code | Status |
| --- | --- | --- |
| 信息源 | `trading_agent_system/agents/premarket_agent/news_provider.py` | 已接入 |
| 事件抽取 | `trading_agent_system/agents/premarket_agent/pipeline/` | 已接入 |
| RAG 证据 | `trading_agent_system/agents/premarket_agent/rag/` | 已接入 |
| 规则/历史案例 | `trading_agent_system/core/knowledge/` | 部分接入 |
| 盘前约束 | `trading_agent_system/core/premarket/context.py` | 已接入 |

## 运维与审计

```text
Events -> Trace -> Metrics -> Reports -> Approval Queue
```

这一层解释系统发生过什么、为什么这样判断、哪些动作需要人工确认。它不直接承担盘前分析、盘中交易信号生成或模拟执行。

| View | Current Code | Responsibility |
| --- | --- | --- |
| Events | `trading_agent_system/core/event_bus/` | Persist event stream for agent and service outputs. |
| Trace | `trading_agent_system/core/observability/traces.py` | Record decision steps and runtime details. |
| Metrics | `trading_agent_system/core/observability/metrics.py` | Record counters, ratios, and timing metrics. |
| Reports | `reports/daily/` | Store generated daily reports and review output. |
| Approval Queue | `trading_agent_system/core/risk_gateway/` | Surface high-risk actions that require human review. |

## 常见误区

- `RiskGateway` 不是 Agent，它是确定性风控服务。
- `PaperBroker` 不是 Agent，它是模拟执行服务。
- RAG、信息源、知识库、`PremarketContext` 是能力模块。
- Observability 页面不是业务 Agent，它用于排查和复盘。
