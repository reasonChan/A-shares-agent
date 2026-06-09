from __future__ import annotations

import json
from pathlib import Path

from trading_agent_system.schemas import DailyReviewReport


class ReportWriter:
    def __init__(self, output_dir: str | Path = "reports/daily") -> None:
        self.output_dir = Path(output_dir)

    def write(self, report: DailyReviewReport) -> tuple[Path, Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        json_path = self.output_dir / f"{report.date.isoformat()}.json"
        md_path = self.output_dir / f"{report.date.isoformat()}.md"
        json_path.write_text(
            json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        md_path.write_text(report.markdown_report, encoding="utf-8")
        return json_path, md_path

    def render_markdown(self, report: DailyReviewReport) -> str:
        return "\n".join(
            [
                f"# 交易复盘日报：{report.date.isoformat()}",
                "",
                "## 1. 总览",
                f"- 净收益：{report.pnl.net_pnl:.2f}",
                f"- 交易次数：{len(report.signal_quality)}",
                "- 胜率：0.00",
                "- 最大单笔亏损：0.00",
                f"- 最大滑点：{report.execution.max_slippage_bps:.2f} bps",
                f"- 风控拒单：{report.risk_review.rejected_count}",
                "",
                "## 2. 收益归因",
                f"- 按策略：{report.pnl.pnl_by_strategy}",
                f"- 按标的：{report.pnl.pnl_by_symbol}",
                "",
                "## 3. 最好交易",
                json.dumps(report.best_trades, ensure_ascii=False),
                "",
                "## 4. 最差交易",
                json.dumps(report.worst_trades, ensure_ascii=False),
                "",
                "## 5. 情报质量",
                json.dumps([item.model_dump(mode="json") for item in report.intel_quality], ensure_ascii=False, indent=2),
                "",
                "## 6. 执行质量",
                json.dumps(report.execution.model_dump(mode="json"), ensure_ascii=False, indent=2),
                "",
                "## 7. 风控表现",
                json.dumps(report.risk_review.model_dump(mode="json"), ensure_ascii=False, indent=2),
                "",
                "## 8. 策略状态建议",
                json.dumps([item.model_dump(mode="json") for item in report.strategy_health], ensure_ascii=False, indent=2),
                "",
                "## 9. 明日关注",
                "- 只观察已配置 watchlist 与风控阈值，不输出确定性买卖建议。",
                "",
            ]
        )
