from __future__ import annotations

from datetime import date

from trading_agent_system.api import app as api_module
from trading_agent_system.core.events import make_envelope
from trading_agent_system.core.knowledge import KnowledgeRecord, KnowledgeStore
from trading_agent_system.core.storage import JsonlEventRepository


def test_decision_trace_api_groups_events_by_intent(tmp_path, monkeypatch):
    monkeypatch.setattr(api_module, "EVENT_DIR", tmp_path / "events")
    repository = JsonlEventRepository(api_module.EVENT_DIR)
    repository.append_envelope(
        make_envelope(
            "trading.intents",
            {"intent_id": "intent_1", "symbol": "688981.SH", "side": "buy", "metadata": {"theme": {"primary_theme": "半导体"}}},
            producer="intraday_agent",
            trading_day=date(2026, 6, 10),
            run_id="intraday_run_1",
            evidence_ids=["evt_theme"],
        )
    )
    repository.append_envelope(
        make_envelope(
            "risk.decisions",
            {"decision_id": "risk_1", "intent_id": "intent_1", "decision": "needs_human_approval"},
            producer="risk_gateway",
            trading_day=date(2026, 6, 10),
            run_id="risk_run_1",
            evidence_ids=["evt_theme"],
        )
    )

    response = api_module.decision_traces(intent_id="intent_1", run_id=None, limit=20)

    assert [item["topic"] for item in response["timeline"]] == ["trading.intents", "risk.decisions"]
    assert response["intent_id"] == "intent_1"
    assert response["timeline"][0]["payload"]["symbol"] == "688981.SH"


def test_rag_debug_api_returns_filters_and_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr(api_module, "KNOWLEDGE_PATH", tmp_path / "knowledge.sqlite")
    store = KnowledgeStore(api_module.KNOWLEDGE_PATH)
    store.upsert(
        KnowledgeRecord(
            record_id="rec_chip",
            record_type="event",
            trading_day=date(2026, 6, 10),
            source="上交所",
            source_rank="official",
            title="半导体并购政策",
            summary="半导体 并购 重组",
            content="半导体 机器人",
            themes=["半导体"],
            symbols=["688981.SH"],
            event_ids=["evt_theme"],
            confidence=0.91,
        )
    )

    response = api_module.rag_debug(
        q="半导体",
        trading_day=date(2026, 6, 10),
        theme=["半导体"],
        symbol=["688981.SH"],
        source_rank_min="authorized_news",
        top_k=5,
    )

    assert response["query"]["q"] == "半导体"
    assert response["query"]["source_rank_min"] == "authorized_news"
    assert response["result_count"] == 1
    assert response["results"][0]["record"]["record_id"] == "rec_chip"
    assert response["results"][0]["record"]["source_rank"] == "official"
