from __future__ import annotations

import json
from datetime import date

from trading_agent_system.api import app as api_module
from trading_agent_system.core.events import make_envelope
from trading_agent_system.core.knowledge import KnowledgeRecord, KnowledgeStore
from trading_agent_system.core.storage import JsonlEventRepository


def test_premarket_debug_api_returns_chain_from_events_knowledge_and_report(tmp_path, monkeypatch):
    monkeypatch.setattr(api_module, "EVENT_DIR", tmp_path / "events")
    monkeypatch.setattr(api_module, "KNOWLEDGE_PATH", tmp_path / "knowledge.sqlite")
    monkeypatch.setattr(api_module, "PREMARKET_REPORT_DIR", tmp_path / "reports" / "premarket")
    api_module.PREMARKET_REPORT_DIR.mkdir(parents=True)

    repository = JsonlEventRepository(api_module.EVENT_DIR)
    trading_day = date(2026, 6, 10)
    repository.append_envelope(
        make_envelope(
            "premarket.raw_documents",
            [{"source_id": "src_1", "title": "机器人政策新闻", "source_name": "新浪财经"}],
            producer="premarket_agent",
            trading_day=trading_day,
            run_id="run_1",
        )
    )
    repository.append_envelope(
        make_envelope(
            "premarket.normalized_events",
            [{"event_id": "evt_1", "title": "机器人政策催化", "related_themes": ["机器人"]}],
            producer="premarket_agent",
            trading_day=trading_day,
            run_id="run_1",
            evidence_ids=["src_1"],
        )
    )
    repository.append_envelope(
        make_envelope(
            "premarket.event_clusters",
            [{"cluster_id": "cluster_1", "title": "机器人: 政策催化", "primary_event_id": "evt_1"}],
            producer="premarket_agent",
            trading_day=trading_day,
            run_id="run_1",
            evidence_ids=["evt_1"],
        )
    )
    repository.append_envelope(
        make_envelope(
            "premarket.rag_evidence_packs",
            {
                "pack_count": 1,
                "packs": [{"section": "theme_candidates", "items": [{"evidence_id": "evt_1", "title": "机器人政策催化"}]}],
            },
            producer="premarket_agent",
            trading_day=trading_day,
            run_id="run_1",
            evidence_ids=["evt_1"],
        )
    )
    repository.append_envelope(
        make_envelope(
            "premarket.rag_evaluation",
            {"summary": {"avg_evidence_coverage_ratio": 1.0}},
            producer="premarket_agent",
            trading_day=trading_day,
            run_id="run_1",
            evidence_ids=["evt_1"],
        )
    )

    KnowledgeStore(api_module.KNOWLEDGE_PATH).upsert(
        KnowledgeRecord(
            record_id="rec_robot",
            record_type="event",
            trading_day=trading_day,
            source="新浪财经",
            source_rank="authorized_news",
            title="机器人政策催化",
            summary="机器人政策进入盘前知识库。",
            content="机器人 政策",
            themes=["机器人"],
            event_ids=["evt_1"],
            evidence_ids=["src_1"],
            confidence=0.9,
        )
    )
    (api_module.PREMARKET_REPORT_DIR / "2026-06-10.json").write_text(
        json.dumps(
            {
                "date": "2026-06-10",
                "market_view": "neutral",
                "summary": "盘前关注机器人。",
                "watchlist": [{"symbol": "002747.SZ", "reason": "机器人政策催化"}],
                "avoid_list": [],
                "catalysts": [{"title": "机器人政策催化", "importance": "A"}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    response = api_module.premarket_debug(trading_day=trading_day, q="机器人")

    assert response["trading_day"] == "2026-06-10"
    assert response["conclusion"]["summary"] == "盘前关注机器人。"
    assert response["steps"][0]["id"] == "raw_documents"
    assert response["steps"][0]["count"] == 1
    assert response["knowledge"]["query_results"][0]["record"]["record_id"] == "rec_robot"
    assert response["rag"]["evidence"]["payload"]["pack_count"] == 1
    assert response["rag"]["evaluation"]["payload"]["summary"]["avg_evidence_coverage_ratio"] == 1.0
