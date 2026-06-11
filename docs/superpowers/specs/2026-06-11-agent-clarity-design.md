# Agent Clarity And Console Information Architecture Design

## Goal

让当前 A 股 Agent 项目的功能边界变清楚。用户打开项目时，应先理解系统在做什么、哪些是真正的业务 Agent、哪些是安全/执行服务、哪些只是盘前能力模块或观测工具。

本次整理优先解决“各个 Agent 混在一起，看不懂”的问题。第一阶段重点是命名、页面分区、README 和架构说明，不做大规模业务逻辑重构。

## Current Confusion

当前控制台和文档把多种概念放在同一个层级：

- `PremarketAgent`、`IntradayAgent`、`ReviewAgent` 是业务 Agent。
- `RiskGateway` 是确定性风控服务，不是 Agent。
- `PaperBroker` 是模拟执行服务，不是 Agent。
- `RAG`、`KnowledgeStore`、`SourceHub`、`PremarketContext` 是能力模块，不是 Agent。
- `Events`、`Trace`、`Metrics`、`ApprovalQueue` 是运维/观测视图，也不是 Agent。

这些概念都很重要，但需要在 UI 和文档里分层展示。

## Target Mental Model

系统对用户展示为三条主线。

### 1. Trading Pipeline

交易流水线展示“今天从信息到复盘怎么走”：

```text
盘前分析 -> 盘中扫描 -> 风控审批 -> 模拟执行 -> 盘后复盘
```

对应模块：

- 盘前分析：`PremarketAgent`
- 盘中扫描：`IntradayAgent`
- 风控审批：`RiskGateway`
- 模拟执行：`PaperBroker`
- 盘后复盘：`ReviewAgent`

这里允许一键运行和查看最新结果。

### 2. Premarket Knowledge System

盘前知识系统展示“盘前 Agent 依赖哪些能力”：

```text
信息源 -> 事件抽取 -> RAG 证据 -> 规则库/历史案例 -> 盘前约束
```

对应模块：

- 信息源：个股信息、财经新闻、社群线索。
- 事件抽取：RawDocument、PreMarketEvent、EventCluster。
- RAG 证据：EvidencePack、RAG evaluation、RAG debug。
- 规则/案例：PlaybookRule、HistoricalCase、HumanFeedback。
- 盘前约束：PremarketContext、Instruction、OpeningRadar。

这里不叫 Agent，而叫能力模块。

### 3. Operations And Audit

运维与审计展示“系统发生了什么，为什么这么判断”：

```text
Events -> Trace -> Metrics -> Reports -> Approval Queue
```

对应模块：

- EventBus / JSONL events
- TraceLogger
- MetricsRecorder
- report files
- risk approval queue
- decision timeline

这里用于排查问题和复盘，不承担业务分析职责。

## Frontend Design

控制台第一屏改成更清楚的信息架构。

### Navigation

顶部页面保留两个主入口：

- `控制台`
- `架构说明`

控制台内部按三个区块组织：

1. `今日交易流水线`
2. `盘前知识系统`
3. `运维与审计`

### Trading Pipeline Section

把现在的 job 列表从“Agent 按钮”改成流水线卡片：

```text
[盘前分析] -> [盘中扫描] -> [风控审批] -> [模拟执行] -> [盘后复盘]
```

每个节点显示：

- 角色类型：Agent / Service
- 最新状态：待命、运行中、成功、失败
- 输出摘要：例如观察数、交易意图数、审批结果、成交结果、复盘净收益
- 运行按钮

`RiskGateway` 和 `PaperBroker` 的标签应显示为 `服务`，避免误认为业务 Agent。

### Premarket Knowledge Section

把现在散落的 RAG、知识检索、盘前上下文聚合成一个区：

- `信息源覆盖`
- `盘前上下文`
- `RAG 证据包`
- `规则/历史案例`
- `盘前约束`

第一版可以先复用现有数据，不要求所有未来功能都已完成。未实现的模块用 `待接入` 标记，不放在交易流水线里。

### Operations Section

现有 observability 面板移动到 `运维与审计`：

- 最近事件
- Trace
- Metrics
- Risk approval queue
- Decision timeline
- 报告文件预览

这个区块强调“为什么”和“发生过什么”。

## Documentation Design

README 增加 `项目功能边界` 章节，用同一套命名解释：

- 什么是真 Agent。
- 什么是服务。
- 什么是能力模块。
- 什么是运维视图。

新增或更新架构说明文档：

```text
docs/architecture/agent-boundaries.md
```

内容包含：

- 交易流水线图。
- 盘前知识系统图。
- 模块责任表。
- 常见误区，例如 “RiskGateway 不是 Agent”。

## Code Boundary Guidance

第一阶段不做大规模目录迁移，只在命名和文档中明确边界：

- `trading_agent_system/agents/`：业务 Agent。
- `trading_agent_system/core/risk_gateway/`：风控服务。
- `trading_agent_system/core/broker/`：执行/模拟成交服务。
- `trading_agent_system/agents/premarket_agent/rag/`：盘前 RAG 能力。
- `trading_agent_system/agents/premarket_agent/sources/`：盘前信息源能力。
- `trading_agent_system/agents/premarket_agent/knowledge/`：盘前规则、案例、反馈能力。
- `trading_agent_system/core/observability/`：观测能力。

如果后续要重构目录，应另起计划，避免和前端可理解性改造混在一起。

## Error Handling And Empty States

页面应明确显示模块状态：

- `已接入`：有真实数据或可运行脚本。
- `部分接入`：有结构和测试，但业务输出尚未完全使用。
- `待接入`：只有设计或计划，不能误导用户以为已运行。
- `失败`：接口或脚本返回错误。

空状态文案要说明下一步动作，而不是只写“暂无”。

## Testing

第一阶段测试范围：

- 前端构建通过。
- Trading pipeline 的节点顺序和角色标签正确。
- README 和架构文档存在关键边界说明。
- 不改变现有 API 行为。
- 现有后端相关测试保持通过。

## Acceptance Criteria

1. 控制台不再把所有模块都展示成同一类 Agent。
2. `RiskGateway` 和 `PaperBroker` 在 UI 和文档中明确标成服务。
3. RAG、信息源、知识库、盘前上下文被归到盘前知识系统，而不是交易流水线 Agent。
4. 运维数据被归到运维与审计区。
5. README 有一段能让新用户快速理解系统边界的说明。
6. 架构文档用图和表说明当前功能边界。
7. 不改动交易、风控、执行的核心业务行为。
