from __future__ import annotations

from datetime import date

from trading_agent_system.core.audit import AuditLedger
from trading_agent_system.schemas import DailyReviewReport

from .data_loader import ReviewDataLoader, ReviewDataset
from .execution_review import ExecutionReview
from .intel_quality_review import IntelQualityReview
from .pnl_attribution import PnLAttribution
from .report_writer import ReportWriter
from .risk_review import RiskReview
from .signal_review import SignalReview
from .strategy_health import StrategyHealthEvaluator


class ReviewAgent:
    def __init__(self, audit: AuditLedger, report_writer: ReportWriter | None = None) -> None:
        self.audit = audit
        self.loader = ReviewDataLoader()
        self.pnl = PnLAttribution()
        self.execution = ExecutionReview()
        self.signal = SignalReview()
        self.intel_quality = IntelQualityReview()
        self.risk = RiskReview()
        self.strategy_health = StrategyHealthEvaluator()
        self.report_writer = report_writer or ReportWriter()

    def run_daily(self, report_date: date, dataset: ReviewDataset) -> DailyReviewReport:
        contexts = self.loader.build_contexts(dataset)
        pnl = self.pnl.calculate(contexts)
        execution = self.execution.calculate(contexts)
        signal_quality = self.signal.evaluate(contexts)
        intel_quality = self.intel_quality.evaluate(dataset.intel, contexts)
        risk_review = self.risk.evaluate(contexts)
        strategy_health = self.strategy_health.evaluate(contexts, pnl)
        report = DailyReviewReport(
            date=report_date,
            pnl=pnl,
            execution=execution,
            risk_review=risk_review,
            signal_quality=signal_quality,
            intel_quality=intel_quality,
            strategy_health=strategy_health,
            best_trades=[],
            worst_trades=[],
            key_mistakes=[],
            action_items=[
                {
                    "type": "watch",
                    "description": "明日只保留观察项，策略变更需回测与人工确认。",
                    "requires_backtest": True,
                }
            ],
        )
        report = report.model_copy(update={"markdown_report": self.report_writer.render_markdown(report)})
        self.report_writer.write(report)
        self.audit.write("review_daily", report)
        return report
