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
