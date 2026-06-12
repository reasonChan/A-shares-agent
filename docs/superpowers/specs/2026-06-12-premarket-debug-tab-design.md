# Premarket Debug Tab Design

## Goal

新增一个顶级 `盘前调试` Tab，把盘前信息 Agent 的链路单独展开，便于查看爬虫信息如何进入结构化事件、如何落入知识库、如何被 RAG/Knowledge 查询、以及最终如何形成盘前结论。

## Scope

第一版做只读调试视图和手动触发，不做知识库编辑、不做规则改写、不做结论人工覆盖。

## User Flow

用户打开 `盘前调试`：

1. 选择交易日。
2. 点击运行盘前分析，或刷新已有数据。
3. 左侧看到链路步骤和每步数量。
4. 点击步骤查看明细。
5. 在调试查询框输入关键词，查看 KnowledgeStore/RAG 查询结果。
6. 右侧查看最终盘前结论和对应 evidence pack。

## Backend Design

新增 API：

```text
GET /api/premarket/debug?trading_day=YYYY-MM-DD&q=机器人
```

接口从现有持久化数据聚合：

- `premarket.raw_documents`
- `premarket.normalized_events`
- `premarket.event_clusters`
- `premarket.morning_brief`
- `premarket.opening_radar`
- `premarket.instructions`
- `premarket.rag_evidence_packs`
- `premarket.rag_evaluation`
- `reports/premarket/*.json`
- `data/knowledge.sqlite`

返回结构：

- `steps`：每个链路步骤的状态、数量、样例。
- `knowledge`：最近入库记录和查询结果。
- `rag`：evidence packs、evaluation summary、query result。
- `conclusion`：市场观点、摘要、观察清单、禁入清单、催化因素。

## Frontend Design

顶部导航新增：

```text
控制台 | 盘前调试 | 架构说明
```

`盘前调试` 页面布局：

- 顶部工具条：运行盘前分析、刷新、查询词输入。
- 左侧：链路步骤列表。
- 中间：当前步骤明细列表。
- 右侧：盘前结论、RAG 覆盖、Knowledge 查询结果。

页面不解释“如何使用”，只呈现可操作调试数据。

## Error Handling

- 没有报告：显示空状态，允许运行盘前分析。
- 没有事件：步骤数量为 0。
- KnowledgeStore 为空：显示 0 条入库记录和 0 条查询结果。
- RAG 事件为空：RAG 区显示无 evidence pack。
- API 单项读取失败：接口继续返回其它区块，并在 `warnings` 中标记失败项。

## Testing

- 后端测试：验证 `/api/premarket/debug` 能从 JSONL events、报告和 KnowledgeStore 聚合链路数据。
- 前端结构测试：验证 `盘前调试` Tab、关键链路步骤和 API client 存在。
- 回归：全量 pytest 和 `npm run build` 通过。

## Acceptance Criteria

1. 顶部有独立 `盘前调试` Tab。
2. 页面能看到爬虫信息、事件、聚类、知识库、RAG、结论链路。
3. 支持运行盘前分析并刷新调试数据。
4. 支持关键词查询 KnowledgeStore/RAG。
5. 不改变盘前 Agent、交易、风控、执行的业务行为。
