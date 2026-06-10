from datetime import date

from trading_agent_system.agents.premarket_agent.rag.rag_service import PreMarketRAGService


def test_rag_service_indexes_and_retrieves_all_evidence_packs(tmp_path):
    service = PreMarketRAGService.local(
        qdrant_path=tmp_path / "qdrant",
        collection_name="premarket_hot",
        embedding_dimension=32,
    )
    service.index_payloads(
        trading_day=date(2026, 6, 10),
        premarket_window_id="pmw_20260610",
        raw_documents=[],
        events=[],
        clusters=[
            {
                "cluster_id": "cluster_1",
                "primary_event_id": "evt_1",
                "title": "机器人: 政策催化",
                "summary": "机器人政策催化。",
                "symbols": ["300750.SZ"],
                "event_type": "official_policy",
                "primary_source_rank": "authorized_news",
                "importance": "A",
                "bias": "bullish",
                "confidence": 0.8,
                "risk_flags": [],
            }
        ],
    )

    packs = service.retrieve_all_evidence_packs(date(2026, 6, 10), "pmw_20260610")

    assert packs
    assert any(pack.items for pack in packs)
