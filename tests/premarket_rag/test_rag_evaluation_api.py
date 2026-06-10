from __future__ import annotations

from datetime import date

from trading_agent_system.agents.premarket_agent.rag.evaluation import RAGEvaluator
from trading_agent_system.agents.premarket_agent.rag.schemas import EvidenceItem, EvidencePack
from trading_agent_system.api import app as api_module
from trading_agent_system.core.events import make_envelope
from trading_agent_system.core.storage import JsonlEventRepository


def test_rag_evaluation_reports_duplicate_and_coverage_ratios():
    pack = EvidencePack(
        pack_id="pack_1",
        trading_day=date(2026, 6, 10),
        premarket_window_id="pmw_20260610",
        section="portfolio_risks",
        query="持仓风险",
        items=[
            EvidenceItem(
                evidence_id="ev_1",
                source_id="src_1",
                source="上交所",
                source_type="exchange_notice",
                source_rank=1.0,
                title="监管函",
                excerpt="收到监管函",
                confidence=0.9,
                citation_label="[ev_1]",
            )
        ],
        dropped_duplicates=2,
        token_estimate=120,
    )

    metrics = RAGEvaluator().evaluate_pack(pack)

    assert metrics.duplicate_ratio > 0
    assert metrics.evidence_coverage_ratio == 1.0
    assert metrics.citation_coverage_ratio == 1.0
    assert metrics.avg_source_rank == 1.0
    assert metrics.token_count == 120


def test_premarket_rag_latest_api_returns_latest_packs_and_evaluation(tmp_path, monkeypatch):
    monkeypatch.setattr(api_module, "EVENT_DIR", tmp_path / "events")
    repository = JsonlEventRepository(api_module.EVENT_DIR)
    repository.append_envelope(
        make_envelope(
            "premarket.rag_evidence_packs",
            {
                "trading_day": "2026-06-10",
                "premarket_window_id": "pmw_2026-06-10",
                "pack_count": 1,
                "token_estimate": 120,
                "packs": [{"section": "portfolio_risks", "items": [{"evidence_id": "ev_1"}]}],
            },
            producer="premarket_agent",
            trading_day=date(2026, 6, 10),
            run_id="run_1",
            evidence_ids=["ev_1"],
        )
    )
    repository.append_envelope(
        make_envelope(
            "premarket.rag_evaluation",
            {
                "trading_day": "2026-06-10",
                "premarket_window_id": "pmw_2026-06-10",
                "metrics": [{"section": "portfolio_risks", "evidence_coverage_ratio": 1.0}],
                "summary": {"avg_evidence_coverage_ratio": 1.0},
            },
            producer="premarket_agent",
            trading_day=date(2026, 6, 10),
            run_id="run_1",
            evidence_ids=["ev_1"],
        )
    )

    response = api_module.premarket_rag_latest()

    assert response["evidence"]["payload"]["pack_count"] == 1
    assert response["evaluation"]["payload"]["summary"]["avg_evidence_coverage_ratio"] == 1.0
    assert response["evidence"]["event"]["run_id"] == "run_1"
