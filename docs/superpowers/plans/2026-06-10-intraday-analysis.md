# 盘中分析功能实现计划

## 目标

把盘中 Agent 从“只吐交易意图”升级为“能解释盘中市场、板块、个股和过滤原因”的分析链路，并在 Web 控制台展示最新盘中分析。

## 范围

1. 后端新增 `intraday.analysis` 报告模型和事件。
2. `IntradayAgent.scan()` 生成盘中分析报告，覆盖市场状态、板块强度、个股评分、信号候选、过滤原因和最终交易意图。
3. `TradePlanner` 暴露过滤原因，避免只有空结果却不知道为什么。
4. Demo 运行写入 durable event，API 可读取最新盘中分析。
5. React 控制台增加“盘中分析”面板，跑盘中 Agent 后自动刷新。

## 验收

1. 单测覆盖报告生成、过滤原因和 API latest。
2. `run_intraday_agent.py --demo` 能输出分析报告并落 `data/events/intraday_analysis.jsonl`。
3. 前端构建通过，页面可看到市场状态、重点板块、个股扫描和信号/过滤结果。
