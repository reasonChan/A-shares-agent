# Agent Clarity Console Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rework the web console and docs so users can clearly distinguish business Agents, deterministic services, premarket knowledge capabilities, and operations/audit views.

**Architecture:** Keep the backend behavior unchanged and express the new mental model through a small frontend information-architecture module, React sections, CSS layout, README copy, and an architecture document. Add lightweight Python tests that lock the boundary labels and documentation because the current remote environment has no Node or npm for frontend unit tests.

**Tech Stack:** React 18, Vite, lucide-react, CSS, Python 3.11, pytest.

---

## File Structure

- Create: `web/src/consoleInformationArchitecture.js`
  - Owns the static taxonomy for pipeline nodes, premarket knowledge modules, and operations/audit modules.
  - Exports `PIPELINE_NODES`, `PREMARKET_KNOWLEDGE_MODULES`, `OPS_AUDIT_MODULES`, `buildPipelineNodes`, `buildKnowledgeCards`, and `buildOpsAuditCards`.
- Modify: `web/src/main.jsx`
  - Imports the information-architecture constants and builders.
  - Replaces the generic job list section with `TradingPipelineSection`.
  - Renames `ObservabilityPanel` into a premarket knowledge system section while reusing existing RAG/context data.
  - Renames `DecisionOpsPanel` into an operations and audit section while keeping existing APIs unchanged.
  - Keeps job execution IDs stable: `premarket`, `intraday`, `risk`, `broker`, `review`.
- Modify: `web/src/styles.css`
  - Adds styles for pipeline nodes, role badges, module status cards, and the three-section console layout.
  - Reuses the current card radius, color palette, and spacing conventions.
- Modify: `README.md`
  - Adds a `Project Boundaries` section before quick start.
  - Updates the default loop to include `PremarketAgent`.
- Create: `docs/architecture/agent-boundaries.md`
  - Documents the trading pipeline, premarket knowledge system, operations/audit layer, and responsibility table.
- Create: `tests/frontend/test_console_information_architecture.py`
  - Reads the frontend IA source and docs to verify the visible taxonomy.

## Task 1: Lock Console Information Architecture With Tests

**Files:**
- Create: `tests/frontend/test_console_information_architecture.py`
- Test source that will be created in Task 2: `web/src/consoleInformationArchitecture.js`
- Docs source that will be created or modified in Task 5: `README.md`, `docs/architecture/agent-boundaries.md`

- [ ] **Step 1: Write the failing test**

Create `tests/frontend/test_console_information_architecture.py`:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
IA_SOURCE = ROOT / "web" / "src" / "consoleInformationArchitecture.js"
README = ROOT / "README.md"
BOUNDARIES_DOC = ROOT / "docs" / "architecture" / "agent-boundaries.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_pipeline_order_and_roles_are_explicit():
    source = read(IA_SOURCE)
    expected_order = [
        "premarket",
        "intraday",
        "risk",
        "broker",
        "review",
    ]
    positions = [source.index(f"id: '{item}'") for item in expected_order]

    assert positions == sorted(positions)
    assert "role: 'Agent'" in source
    assert "role: 'Service'" in source
    assert "title: '风控审批'" in source
    assert "title: '模拟执行'" in source
    assert "RiskGateway 不是 Agent" in source
    assert "PaperBroker 不是 Agent" in source


def test_console_has_three_named_sections():
    source = read(IA_SOURCE)

    assert "今日交易流水线" in source
    assert "盘前知识系统" in source
    assert "运维与审计" in source
    assert "信息源覆盖" in source
    assert "RAG 证据包" in source
    assert "规则/历史案例" in source
    assert "Approval Queue" in source


def test_docs_explain_agent_service_capability_boundaries():
    readme = read(README)
    boundaries = read(BOUNDARIES_DOC)

    assert "项目功能边界" in readme
    assert "PremarketAgent -> IntradayAgent -> RiskGateway -> PaperBroker -> ReviewAgent" in readme
    assert "RiskGateway 是确定性风控服务，不是业务 Agent" in readme
    assert "PaperBroker 是模拟执行服务，不是业务 Agent" in readme

    assert "交易流水线" in boundaries
    assert "盘前知识系统" in boundaries
    assert "运维与审计" in boundaries
    assert "RiskGateway 不是 Agent" in boundaries
    assert "RAG、信息源、知识库、PremarketContext 是能力模块" in boundaries
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run:

```bash
python3 -m pytest tests/frontend/test_console_information_architecture.py -q
```

Expected: FAIL because `web/src/consoleInformationArchitecture.js` and `docs/architecture/agent-boundaries.md` do not exist yet.

## Task 2: Add Console Information Architecture Model

**Files:**
- Create: `web/src/consoleInformationArchitecture.js`
- Test: `tests/frontend/test_console_information_architecture.py`

- [ ] **Step 1: Create the IA model**

Create `web/src/consoleInformationArchitecture.js`:

```javascript
export const CONSOLE_SECTIONS = {
  pipeline: '今日交易流水线',
  knowledge: '盘前知识系统',
  ops: '运维与审计',
};

export const PIPELINE_NODES = [
  {
    id: 'premarket',
    title: '盘前分析',
    module: 'PremarketAgent',
    role: 'Agent',
    hint: 'Ctrl+5',
    summary: '收集盘前信息，生成市场判断、观察清单和禁入约束。',
    outputLabel: '观察',
  },
  {
    id: 'intraday',
    title: '盘中扫描',
    module: 'IntradayAgent',
    role: 'Agent',
    hint: 'Ctrl+1',
    summary: '读取行情与盘前约束，输出候选信号和交易意图。',
    outputLabel: '意图',
  },
  {
    id: 'risk',
    title: '风控审批',
    module: 'RiskGateway',
    role: 'Service',
    hint: 'Ctrl+2',
    summary: 'RiskGateway 不是 Agent；它是确定性风控服务，负责硬约束和人工审批。',
    outputLabel: '审批',
  },
  {
    id: 'broker',
    title: '模拟执行',
    module: 'PaperBroker',
    role: 'Service',
    hint: 'Ctrl+3',
    summary: 'PaperBroker 不是 Agent；它是模拟成交服务，只处理 paper orders。',
    outputLabel: '成交',
  },
  {
    id: 'review',
    title: '盘后复盘',
    module: 'ReviewAgent',
    role: 'Agent',
    hint: 'Ctrl+4',
    summary: '复盘信号、风控、执行和收益，不直接改策略配置。',
    outputLabel: '净收益',
  },
];

export const PREMARKET_KNOWLEDGE_MODULES = [
  {
    id: 'sources',
    title: '信息源覆盖',
    status: '已接入',
    detail: '个股信息、财经新闻、公告源和后续社群线索统一进入盘前信息层。',
  },
  {
    id: 'context',
    title: '盘前上下文',
    status: '已接入',
    detail: 'PremarketContext 把盘前结论变成盘中可执行约束。',
  },
  {
    id: 'rag',
    title: 'RAG 证据包',
    status: '已接入',
    detail: 'EvidencePack、引用覆盖率和来源质量用于降低无证据结论。',
  },
  {
    id: 'knowledge',
    title: '规则/历史案例',
    status: '部分接入',
    detail: 'KnowledgeStore 已存在，PlaybookRule、HistoricalCase 和 HumanFeedback 继续接入。',
  },
  {
    id: 'constraints',
    title: '盘前约束',
    status: '已接入',
    detail: '确认题材、失败题材、禁入标的和开盘雷达进入盘中扫描。',
  },
];

export const OPS_AUDIT_MODULES = [
  {
    id: 'events',
    title: 'Events',
    status: '已接入',
    detail: 'EventBus 记录每个脚本和服务产出的事件。',
  },
  {
    id: 'traces',
    title: 'Trace',
    status: '已接入',
    detail: 'TraceLogger 记录关键决策步骤和耗时。',
  },
  {
    id: 'metrics',
    title: 'Metrics',
    status: '已接入',
    detail: 'MetricsRecorder 汇总运行次数、检索质量和延迟。',
  },
  {
    id: 'approvals',
    title: 'Approval Queue',
    status: '已接入',
    detail: 'RiskGateway 输出需要人工确认的高风险动作。',
  },
  {
    id: 'reports',
    title: 'Reports',
    status: '已接入',
    detail: '日报和复盘报告用于审计，不承担盘前或盘中分析职责。',
  },
];

export function resultStatus(result, running) {
  if (running) return '运行中';
  if (!result) return '待命';
  if (result.status === 'success') return '成功';
  if (result.status === 'failed') return '失败';
  return result.status || '待命';
}

export function buildPipelineNodes({ results, running, timers, premarket, intraday }) {
  return PIPELINE_NODES.map((node) => {
    const result = results[node.id];
    const isRunning = Boolean(running[node.id]);
    return {
      ...node,
      statusText: resultStatus(result, isRunning),
      elapsedMs: isRunning ? timers[node.id] : result?.elapsed_ms,
      outputValue: summarizePipelineOutput(node.id, result, premarket, intraday),
    };
  });
}

export function buildKnowledgeCards({ observability }) {
  const context = observability.premarketContext;
  const rag = observability.premarketRag || {};
  const evidencePayload = rag.evidence?.payload || {};
  const evaluationPayload = rag.evaluation?.payload || {};
  const evaluationSummary = evaluationPayload.summary || {};

  return PREMARKET_KNOWLEDGE_MODULES.map((module) => {
    if (module.id === 'context') {
      return {
        ...module,
        metric: context ? `${context.constraints?.length || 0} 条约束` : '无上下文',
      };
    }
    if (module.id === 'rag') {
      return {
        ...module,
        metric: `${evidencePayload.pack_count || 0} packs / 覆盖 ${formatPercent(evaluationSummary.avg_evidence_coverage_ratio)}`,
      };
    }
    if (module.id === 'sources') {
      return {
        ...module,
        metric: `${observability.ragDebug?.result_count || 0} 条检索结果`,
      };
    }
    return {
      ...module,
      metric: module.status,
    };
  });
}

export function buildOpsAuditCards({ observability, reports }) {
  const counts = {
    events: observability.events?.length || 0,
    traces: observability.traces?.length || 0,
    metrics: observability.metrics?.length || 0,
    approvals: observability.approvalQueue?.length || 0,
    reports: reports?.length || 0,
  };

  return OPS_AUDIT_MODULES.map((module) => ({
    ...module,
    metric: `${counts[module.id] || 0} 条`,
  }));
}

function summarizePipelineOutput(id, result, premarket, intraday) {
  if (id === 'premarket') return `${premarket?.watchlist?.length || 0} 个观察`;
  if (id === 'intraday') return `${intraday?.report?.trade_intent_count || 0} 个意图`;
  if (id === 'risk') return result?.parsed?.decision || '-';
  if (id === 'broker') {
    const fill = Array.isArray(result?.parsed) ? result.parsed[0] : null;
    return fill ? `${fill.quantity}@${Number(fill.price).toFixed(3)}` : '-';
  }
  if (id === 'review') return result?.parsed?.pnl ? Number(result.parsed.pnl.net_pnl).toFixed(2) : '-';
  return '-';
}

function formatPercent(value) {
  if (value === null || value === undefined || value === '') return '-';
  return `${(Number(value) * 100).toFixed(0)}%`;
}
```

- [ ] **Step 2: Run the focused test and verify the model resolves part of the failure**

Run:

```bash
python3 -m pytest tests/frontend/test_console_information_architecture.py -q
```

Expected: still FAIL because README and `docs/architecture/agent-boundaries.md` are not updated yet.

## Task 3: Rework Console Sections

**Files:**
- Modify: `web/src/main.jsx`
- Modify: `web/src/styles.css`
- Test: `tests/frontend/test_console_information_architecture.py`

- [ ] **Step 1: Import the IA model and remove the generic `JOBS` taxonomy**

In `web/src/main.jsx`, add the import:

```javascript
import {
  CONSOLE_SECTIONS,
  PIPELINE_NODES,
  buildKnowledgeCards,
  buildOpsAuditCards,
  buildPipelineNodes,
} from './consoleInformationArchitecture.js';
```

Replace the `JOBS` constant with:

```javascript
const JOB_LABELS = Object.fromEntries(PIPELINE_NODES.map((item) => [item.id, item.title]));
```

Update the failed-result label inside `executeJob`:

```javascript
label: JOB_LABELS[job] || job,
```

- [ ] **Step 2: Build section view models inside `App`**

After `const summary = useMemo(() => buildSummary(results), [results]);`, add:

```javascript
const pipelineNodes = useMemo(() => buildPipelineNodes({
  results,
  running,
  timers,
  premarket,
  intraday,
}), [intraday, premarket, results, running, timers]);

const knowledgeCards = useMemo(() => buildKnowledgeCards({
  observability,
}), [observability]);

const opsAuditCards = useMemo(() => buildOpsAuditCards({
  observability,
  reports,
}), [observability, reports]);
```

- [ ] **Step 3: Replace the old run workspace with the trading pipeline section**

Replace the `<section className="workspace">...</section>` block with:

```jsx
<TradingPipelineSection
  title={CONSOLE_SECTIONS.pipeline}
  nodes={pipelineNodes}
  selectedJob={selectedJob}
  activeResult={activeResult}
  running={running}
  timers={timers}
  reports={reports}
  selectedReport={selectedReport}
  reportText={reportText}
  onSelectJob={setSelectedJob}
  onRunJob={executeJob}
  onRunAll={executeAll}
  onSelectReport={setSelectedReport}
  onRefreshReports={refreshReports}
/>
```

- [ ] **Step 4: Rename and pass cards to the knowledge and ops sections**

Update the existing panel calls:

```jsx
<PremarketKnowledgeSection
  title={CONSOLE_SECTIONS.knowledge}
  cards={knowledgeCards}
  data={observability}
  loading={observabilityLoading}
  error={observabilityError}
  query={knowledgeQuery}
  onQueryChange={setKnowledgeQuery}
  onRefresh={refreshObservability}
/>

<OperationsAuditSection
  title={CONSOLE_SECTIONS.ops}
  cards={opsAuditCards}
  data={observability}
  loading={observabilityLoading}
  decisionQuery={decisionQuery}
  onDecisionQueryChange={setDecisionQuery}
  onRefresh={refreshObservability}
/>
```

Rename function declarations:

```javascript
function ObservabilityPanel(...) {
```

to:

```javascript
function PremarketKnowledgeSection({ title, cards, data, loading, error, query, onQueryChange, onRefresh }) {
```

Rename:

```javascript
function DecisionOpsPanel(...) {
```

to:

```javascript
function OperationsAuditSection({ title, cards, data, loading, decisionQuery, onDecisionQueryChange, onRefresh }) {
```

- [ ] **Step 5: Add the new pipeline components**

Add these components above `StatusPill`:

```jsx
function TradingPipelineSection({
  title,
  nodes,
  selectedJob,
  activeResult,
  running,
  timers,
  reports,
  selectedReport,
  reportText,
  onSelectJob,
  onRunJob,
  onRunAll,
  onSelectReport,
  onRefreshReports,
}) {
  return (
    <section className="pipeline-section">
      <div className="pipeline-header">
        <div className="section-title">
          <BarChart3 size={18} />
          <span>{title}</span>
        </div>
        <button className="run-all compact-run" type="button" onClick={onRunAll} disabled={running.all}>
          {running.all ? <RefreshCw className="spin" size={18} /> : <Play size={18} />}
          <span>运行完整链路</span>
          <kbd>Ctrl Enter</kbd>
        </button>
      </div>
      <div className="pipeline-flow">
        {nodes.map((node, index) => (
          <React.Fragment key={node.id}>
            <PipelineNode
              node={node}
              selected={selectedJob === node.id}
              onSelect={() => onSelectJob(node.id)}
              onRun={() => onRunJob(node.id)}
            />
            {index < nodes.length - 1 ? <span className="pipeline-arrow">-&gt;</span> : null}
          </React.Fragment>
        ))}
      </div>
      <div className="pipeline-detail-grid">
        <div className="output-panel pipeline-output">
          <div className="section-title">
            <Terminal size={18} />
            <span>节点输出</span>
          </div>
          <OutputView result={activeResult} running={Boolean(running[selectedJob])} elapsed={timers[selectedJob]} />
        </div>
        <div className="report-panel pipeline-report">
          <div className="section-title">
            <FileText size={18} />
            <span>报告预览</span>
          </div>
          <div className="report-select-row">
            <select value={selectedReport} onChange={(event) => onSelectReport(event.target.value)}>
              <option value="">无报告</option>
              {reports.map((report) => (
                <option key={report.name} value={report.name}>{report.name}</option>
              ))}
            </select>
            <button className="icon-button" type="button" onClick={onRefreshReports} aria-label="刷新报告">
              <RefreshCw size={16} />
            </button>
          </div>
          <pre className="report-preview">{reportText || '暂无报告'}</pre>
        </div>
      </div>
    </section>
  );
}

function PipelineNode({ node, selected, onSelect, onRun }) {
  return (
    <article className={`pipeline-node ${selected ? 'selected' : ''}`}>
      <button className="pipeline-node-main" type="button" onClick={onSelect}>
        <span className={`role-badge role-${node.role.toLowerCase()}`}>{node.role}</span>
        <strong>{node.title}</strong>
        <small>{node.module}</small>
      </button>
      <p>{node.summary}</p>
      <div className="pipeline-node-meta">
        <span className={`pipeline-state state-${node.statusText}`}>{node.statusText}</span>
        <span>{node.outputLabel}: {node.outputValue}</span>
      </div>
      <button className="job-run pipeline-run" type="button" onClick={onRun} disabled={node.statusText === '运行中'}>
        <Play size={16} />
        <kbd>{node.hint}</kbd>
      </button>
    </article>
  );
}

function ModuleStatusCards({ cards }) {
  return (
    <div className="module-status-grid">
      {cards.map((card) => (
        <article className="module-status-card" key={card.id}>
          <div>
            <strong>{card.title}</strong>
            <span className={`module-status ${statusClassName(card.status)}`}>{card.status}</span>
          </div>
          <p>{card.detail}</p>
          <small>{card.metric}</small>
        </article>
      ))}
    </div>
  );
}
```

Add the helper near the other formatting helpers:

```javascript
function statusClassName(value) {
  return {
    已接入: 'ready',
    部分接入: 'partial',
    待接入: 'pending',
    失败: 'failed',
  }[value] || 'pending';
}
```

- [ ] **Step 6: Render status cards inside the renamed sections**

At the start of the content inside `PremarketKnowledgeSection`, after any error block, render:

```jsx
<ModuleStatusCards cards={cards} />
```

Change the section title text to `{title}`.

At the start of the content inside `OperationsAuditSection`, render:

```jsx
<ModuleStatusCards cards={cards} />
```

Change the section title text to `{title}`.

- [ ] **Step 7: Add CSS for the new sections**

Append to `web/src/styles.css`:

```css
.pipeline-section {
  margin-bottom: 16px;
  padding: 16px;
  border: 1px solid #F0F0F0;
  border-radius: 8px;
  background: #FFFFFF;
}

.pipeline-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
}

.pipeline-header .section-title {
  margin-bottom: 0;
}

.compact-run {
  width: auto;
  min-width: 188px;
}

.pipeline-flow {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr) auto minmax(0, 1fr) auto minmax(0, 1fr) auto minmax(0, 1fr);
  gap: 10px;
  align-items: stretch;
}

.pipeline-arrow {
  align-self: center;
  color: #888888;
  font-weight: 800;
}

.pipeline-node {
  min-width: 0;
  min-height: 210px;
  padding: 12px;
  border: 1px solid #F0F0F0;
  border-top: 4px solid #0A77F5;
  border-radius: 8px;
  background: #FAFAFA;
}

.pipeline-node.selected {
  border-color: #FFDD00;
  border-top-color: #FFDD00;
  background: #FFFDF0;
}

.pipeline-node-main {
  display: grid;
  gap: 4px;
  width: 100%;
  padding: 0;
  background: transparent;
  color: #111111;
  text-align: left;
}

.pipeline-node-main strong,
.pipeline-node-main small,
.pipeline-node p,
.pipeline-node-meta span {
  overflow: hidden;
  text-overflow: ellipsis;
}

.pipeline-node-main strong {
  white-space: nowrap;
  font-size: 16px;
}

.pipeline-node-main small,
.pipeline-node p {
  color: #888888;
}

.pipeline-node p {
  min-height: 54px;
  margin: 10px 0;
}

.role-badge,
.module-status,
.pipeline-state {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  min-height: 24px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 800;
}

.role-agent {
  color: #0A77F5;
  background: #F5FAFF;
}

.role-service {
  color: #7A3100;
  background: #FFFAD8;
}

.pipeline-node-meta {
  display: grid;
  gap: 4px;
  margin-bottom: 10px;
  color: #555555;
  font-size: 12px;
}

.pipeline-state {
  color: #555555;
  background: #F0F0F0;
}

.state-成功 {
  color: #008500;
  background: #E1FAE8;
}

.state-失败 {
  color: #FF2D19;
  background: #FFF1F0;
}

.state-运行中 {
  color: #7A3100;
  background: #FFFAD8;
}

.pipeline-run {
  width: 100%;
  background: #FFFFFF;
}

.pipeline-detail-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 420px);
  gap: 16px;
  margin-top: 16px;
}

.pipeline-output,
.pipeline-report {
  min-height: 460px;
}

.module-status-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.module-status-card {
  min-width: 0;
  min-height: 132px;
  padding: 12px;
  border: 1px solid #F0F0F0;
  border-radius: 8px;
  background: #FAFAFA;
}

.module-status-card div {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.module-status-card strong {
  color: #111111;
}

.module-status-card p {
  margin: 8px 0;
  color: #555555;
  font-size: 12px;
}

.module-status-card small {
  color: #888888;
  font-weight: 700;
}

.module-status.ready {
  color: #008500;
  background: #E1FAE8;
}

.module-status.partial {
  color: #7A3100;
  background: #FFFAD8;
}

.module-status.pending {
  color: #555555;
  background: #F0F0F0;
}

.module-status.failed {
  color: #FF2D19;
  background: #FFF1F0;
}
```

Add this media query near the existing responsive rules if the file has them, or append it after the new CSS:

```css
@media (max-width: 1180px) {
  .pipeline-flow {
    grid-template-columns: 1fr;
  }

  .pipeline-arrow {
    display: none;
  }

  .pipeline-detail-grid,
  .module-status-grid {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 8: Run the focused frontend IA test**

Run:

```bash
python3 -m pytest tests/frontend/test_console_information_architecture.py -q
```

Expected: still FAIL until documentation is updated in Task 4.

## Task 4: Document Agent Boundaries

**Files:**
- Modify: `README.md`
- Create: `docs/architecture/agent-boundaries.md`
- Test: `tests/frontend/test_console_information_architecture.py`

- [ ] **Step 1: Update README boundary section**

Insert after the intro paragraph in `README.md`:

```markdown
## 项目功能边界

项目对外展示为三条主线：

- 交易流水线：`PremarketAgent -> IntradayAgent -> RiskGateway -> PaperBroker -> ReviewAgent`。
- 盘前知识系统：信息源、事件抽取、RAG 证据、规则/历史案例、`PremarketContext`。
- 运维与审计：事件、Trace、Metrics、Approval Queue、报告预览。

真正的业务 Agent 只有 `PremarketAgent`、`IntradayAgent` 和 `ReviewAgent`。`RiskGateway` 是确定性风控服务，不是业务 Agent；`PaperBroker` 是模拟执行服务，不是业务 Agent。RAG、信息源、知识库、`PremarketContext` 是能力模块，用来支撑盘前分析和盘中约束。
```

Update the default loop block to:

```text
External information / MarketBar
  -> PremarketAgent
  -> PremarketContext
  -> IntradayAgent
  -> trading.intents
  -> RiskGateway
  -> risk.decisions + orders.instructions
  -> PaperBroker
  -> orders.filled + account/position snapshots
  -> ReviewAgent daily reports
```

- [ ] **Step 2: Create the architecture boundary document**

Create `docs/architecture/agent-boundaries.md`:

```markdown
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
```

- [ ] **Step 3: Run the focused IA test**

Run:

```bash
python3 -m pytest tests/frontend/test_console_information_architecture.py -q
```

Expected: PASS.

## Task 5: Verify Build and Regression Safety

**Files:**
- Read-only verification across frontend and backend.

- [ ] **Step 1: Run focused docs/frontend boundary tests**

Run:

```bash
python3 -m pytest tests/frontend/test_console_information_architecture.py -q
```

Expected: 3 passed.

- [ ] **Step 2: Run backend tests that should not be affected**

Run:

```bash
python3 -m pytest tests/premarket tests/intraday tests/risk tests/observability -q
```

Expected: existing tests pass. If unrelated environment failures appear, record the exact failing tests and error text.

- [ ] **Step 3: Try the frontend build**

Run:

```bash
cd web && npm run build
```

Expected in this remote environment: command cannot run because `npm` is not installed. Record `npm not found` in the final verification notes. If Node/npm becomes available, expected result is a successful Vite build.

- [ ] **Step 4: Check formatting and worktree**

Run:

```bash
git diff --check
git status --short
```

Expected: no whitespace errors. Worktree should show only the files intentionally changed by this implementation plus the two existing untracked premarket plan files if they remain uncommitted.

## Self-Review Notes

- Spec coverage:
  - Trading pipeline section is covered by Tasks 2 and 3.
  - Premarket knowledge system section is covered by Tasks 2 and 3.
  - Operations and audit section is covered by Tasks 2 and 3.
  - README and architecture documentation are covered by Task 4.
  - No backend business behavior is changed; Task 5 verifies relevant tests.
- Placeholder scan:
  - The plan contains no placeholder keywords, no deferred implementation wording, and no empty test-writing steps.
- Type consistency:
  - `PIPELINE_NODES`, `PREMARKET_KNOWLEDGE_MODULES`, and `OPS_AUDIT_MODULES` are imported into `main.jsx`.
  - `buildPipelineNodes`, `buildKnowledgeCards`, and `buildOpsAuditCards` accept the same object keys shown in Task 3.
  - `statusClassName` maps the exact status labels emitted by the IA model.
