# Premarket Source System Design

## Goal

升级盘前信息来源系统，让架构明确支持三层来源：

- 个股信息：公告、财报、业绩预告、监管函、减持、回购、公司新闻、个股异动摘要。
- 财经新闻：监管、交易所、宏观、行业、专业快讯和财经媒体新闻。
- 社群新闻：雪球、开盘啦、东方财富股吧/热榜/讨论等第三方社群线索。

第一版目标是把来源边界、可信度分层、配置和降级策略做清楚。系统仍保持 paper trading 安全边界：信息源只能影响观察、禁入、人工确认和盘中关注权重，不能直接生成买卖或下单指令。

## Current State

当前盘前入口在 `scripts/run_premarket_agent.py`，通过 `configs/app.yaml` 中的 `premarket.providers` 构建 provider。现有 provider 集中在 `trading_agent_system/agents/premarket_agent/news_provider.py`：

- `CsrcNewsProvider`：证监会要闻，官方源。
- `EastMoneyNewsProvider`：东方财富财经新闻，专业新闻源。
- `SinaFinanceRollProvider`：新浪财经滚动，专业新闻源。
- `CailianpressTelegraphProvider`：财联社电报，专业快讯源。
- `RssNewsProvider`：自定义 RSS。
- `DemoPremarketNewsProvider`：本地 demo。

这些 provider 都直接返回 `PremarketNewsItem`。现状能跑通，但缺少来源层级、个股信息和社群信息的独立边界。雪球、开盘啦、东方财富股吧、机构财报分析等还没有专门接入。

## Recommended Architecture

新增 `sources` 包，形成 `SourceHub -> SourceLayer -> Provider -> Normalizer -> Quality` 的结构。

```text
configs/sources.premarket.yaml

trading_agent_system/agents/premarket_agent/sources/
  base.py
  source_hub.py
  normalization.py
  quality.py
  stock_info/
  finance_news/
  community/
```

`SourceHub` 负责按配置构建三层来源，统一执行抓取，汇总 `SourceFetchResult`，并输出现有 agent 可消费的 `PremarketNewsItem` 列表。这样 `PremarketAgent` 主流程可以继续复用现有标准化、事件聚类、RAG 和风控链路。

## Source Layers

### StockInfoLayer

个股层面面向 watchlist、持仓和配置中的重点标的。第一版优先支持公开信息：

- 东方财富个股新闻或 F10 摘要。
- 交易所/证监会公开公告中能映射到个股的事件。
- 后续可接巨潮资讯、公告 PDF、财报结构化指标。

个股信息可以进入催化、回避、持仓风险和人工确认。财报或机构分析必须区分硬事实和观点：

- 财报原文、公告、业绩快报是硬事实。
- 机构研报、券商观点、社群解读是观点来源。
- 观点不能单独覆盖公告事实，也不能单独解除风险约束。

### FinanceNewsLayer

财经新闻层承接现有官方和专业新闻源。第一版迁移现有 provider，不改变输出语义：

- 证监会要闻。
- 东方财富财经新闻。
- 新浪财经滚动。
- 财联社电报。
- 自定义 RSS。

官方和专业财经新闻可以参与 `market_view`、主题候选、重点催化、回避清单和 RAG evidence packs。

### CommunityLayer

社群层用于捕捉热度、异动、传闻和讨论方向。候选来源包括：

- 雪球。
- 开盘啦。
- 东方财富股吧、热榜、讨论。

第一版只实现不需要登录 cookie 的公开可访问入口。需要登录、cookie、授权或容易触发反爬的入口只保留 provider 接口和配置位，默认关闭。

社群层安全规则固定为：

- `source_tier="sentiment"`。
- 默认 `category="community_signal"` 或更具体的社群类别。
- 默认可信度低于专业新闻源。
- 只能生成 `watch_only` 或 `require_confirmation` 线索。
- 不能单独生成买入候选。
- 不能解除 `avoid_new_entry`、`reduce_only` 或 `block_until_official_confirmation`。
- 出现传闻、小作文、未经证实、网传、股吧爆料等词时强制添加风险标记。

## Data Model

保留 `PremarketNewsItem` 作为 agent 主流程输入，新增轻量内部模型用于来源系统：

```text
SourceLayer: stock_info | finance_news | community
SourceProviderConfig: name, layer, enabled, limit, timeout, params, auth_required
SourceFetchResult: source, layer, status, items, error, fetched_count, used_count
SourceQualityProfile: source, layer, base_credibility, max_actionability, failure_policy
```

`PremarketNewsItem` 继续承载输出字段：

- `source`
- `source_tier`
- `title`
- `summary`
- `url`
- `published_at`
- `category`
- `symbols`
- `sectors`
- `credibility`
- `risk_flags`

后续如果需要更细证据追踪，可以在 `raw_payload` 或 RAG 文档 metadata 中记录 provider 原始字段，但第一版不扩展公共 schema，避免影响下游。

## Configuration

新增 `configs/sources.premarket.yaml`，由 `configs/app.yaml` 引用。第一版配置示例：

```yaml
sources:
  timeout_seconds: 8
  default_limit: 30

  layers:
    stock_info:
      enabled: true
      providers:
        - name: eastmoney_stock_news
          enabled: true
          auth_required: false

    finance_news:
      enabled: true
      providers:
        - name: csrc
          enabled: true
        - name: eastmoney
          enabled: true
        - name: sina
          enabled: true
        - name: cailianpress
          enabled: true

    community:
      enabled: true
      providers:
        - name: eastmoney_guba
          enabled: false
          auth_required: false
        - name: xueqiu
          enabled: false
          auth_required: true
        - name: kaipanla
          enabled: false
          auth_required: true

  quality:
    official:
      base_credibility: 0.92
    professional:
      base_credibility: 0.76
    sentiment:
      base_credibility: 0.35
      max_actionability: watch_only
```

`premarket.providers` 暂时保留兼容。新配置存在时优先使用 `SourceHub`，否则回退到旧的 `build_providers`。

## Data Flow

```text
configs/sources.premarket.yaml
  -> SourceHub
  -> StockInfoLayer / FinanceNewsLayer / CommunityLayer
  -> Provider.fetch()
  -> SourceFetchResult
  -> Normalizer + SourceQuality
  -> PremarketNewsItem[]
  -> PremarketAgent existing pipeline
  -> RawDocument / PreMarketEvent / EventCluster
  -> MorningBrief / OpeningRadar / Instruction / RAG EvidencePack
```

## Error Handling

每个 provider 失败时只影响自身来源状态，不中断整轮盘前 agent：

- 网络失败：记录 `failed`，保留错误信息。
- 空结果：记录 `empty`。
- 需要登录但未配置凭据：记录 `disabled` 或 `failed_auth_required`，不尝试绕过。
- 被反爬或返回页面壳：记录 `failed_blocked`，不重试高频抓取。
- 社群源全部失败：不影响财经新闻和个股信息层。
- 官方/专业源全部失败：全局 warning，盘前结论转谨慎，增加人工确认约束。

## Safety Rules

- 任何社群源都不能单独支撑买入、加仓、下单、交易意图。
- 任何未经证实的信息必须带风险标记。
- 个股负面硬事实优先级高于社群热度。
- 机构研报和财报分析必须标记来源类型：`hard_fact` 或 `opinion`。
- 若 opinion 与 hard_fact 冲突，系统输出人工确认，不自动采纳 opinion。
- 所有进入 `PreMarketInstruction` 的约束必须有 `source_ids` 或 `evidence_event_ids`。

## Institutional Research And Earnings Analysis

机构财报分析不作为第一版默认外部抓取源，因为大多数研报全文依赖 Wind、Choice、iFinD、慧博、券商账号或其他授权来源。

第一版只预留 `InstitutionResearchProvider` 接口和本地文件入口：

- `data/research/` 下的用户自有 PDF、Markdown 或 JSON 摘要。
- 手动结构化的机构观点数据。
- 未来授权 API 的 adapter。

硬事实优先来自公告、财报原文和公开 F10 数据。机构观点只能作为观点 evidence，不能单独生成交易方向。

## Testing

第一版测试范围：

- `SourceHub` 能按三层配置构建 provider。
- 旧 `premarket.providers` 配置仍可回退。
- 社群 provider 输出强制降级为 `sentiment` 和 `watch_only`。
- 社群传闻词会添加风险标记。
- 单个 provider 失败不影响其他 provider。
- 个股信息能按 watchlist 生成带 symbol 的 `PremarketNewsItem`。
- 现有 `tests/premarket`、`tests/premarket_rag`、盘中上下文和风控约束测试保持通过。

## Acceptance Criteria

1. 盘前信息源架构支持 `stock_info`、`finance_news`、`community` 三层。
2. 现有财经新闻 provider 通过新架构运行，旧配置仍兼容。
3. 个股信息层至少能基于 watchlist 产生结构化个股新闻或个股摘要。
4. 社群层有 provider 接口和至少一个公开可访问 provider 的实现或可测试 stub。
5. 社群源默认降权，不能单独生成 candidate 或解除风险约束。
6. Provider 失败会被记录到 source status，但不会中断整轮盘前分析。
7. RAG 和下游 `PremarketContext`、`IntradayAgent`、`RiskGateway` 继续消费相同的 `PremarketNewsItem`/report 结构。
8. 新增和现有相关测试通过。
