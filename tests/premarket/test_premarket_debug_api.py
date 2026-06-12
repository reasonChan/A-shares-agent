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
    raw_documents = next(step for step in response["steps"] if step["id"] == "raw_documents")
    assert raw_documents["count"] == 1
    assert response["knowledge"]["query_results"][0]["record"]["record_id"] == "rec_robot"
    assert response["rag"]["evidence"]["payload"]["pack_count"] == 1
    assert response["rag"]["evaluation"]["payload"]["summary"]["avg_evidence_coverage_ratio"] == 1.0


def test_premarket_debug_api_separates_source_fetch_from_window_filtered_documents(tmp_path, monkeypatch):
    monkeypatch.setattr(api_module, "EVENT_DIR", tmp_path / "events")
    monkeypatch.setattr(api_module, "KNOWLEDGE_PATH", tmp_path / "knowledge.sqlite")
    monkeypatch.setattr(api_module, "PREMARKET_REPORT_DIR", tmp_path / "reports" / "premarket")
    api_module.PREMARKET_REPORT_DIR.mkdir(parents=True)

    repository = JsonlEventRepository(api_module.EVENT_DIR)
    trading_day = date(2026, 6, 12)
    repository.append_envelope(
        make_envelope(
            "premarket.raw_documents",
            [],
            producer="premarket_agent",
            trading_day=trading_day,
            run_id="run_empty",
        )
    )
    (api_module.PREMARKET_REPORT_DIR / "2026-06-12.json").write_text(
        json.dumps(
            {
                "date": "2026-06-12",
                "market_view": "cautious",
                "summary": "盘前消息源质量不足。",
                "source_status": [
                    {"source": "东方财富财经新闻", "status": "ok", "fetched_count": 10, "used_count": 0},
                    {"source": "新浪财经滚动", "status": "ok", "fetched_count": 30, "used_count": 0},
                ],
                "warnings": ["盘前窗口内没有可用消息，禁止基于新闻做主动买入。"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    response = api_module.premarket_debug(trading_day=trading_day, q="盘前")

    source_fetch = response["steps"][0]
    raw_documents = response["steps"][1]
    assert source_fetch["id"] == "source_fetch"
    assert source_fetch["label"] == "源站抓取状态"
    assert source_fetch["count"] == 40
    assert source_fetch["items"][0]["source"] == "东方财富财经新闻"
    assert raw_documents["id"] == "raw_documents"
    assert raw_documents["label"] == "窗口内原始文档"
    assert raw_documents["status"] == "empty"
    assert raw_documents["count"] == 0
    assert raw_documents["items"] == []
    assert "盘前窗口内没有可用消息" in response["warnings"][0]
