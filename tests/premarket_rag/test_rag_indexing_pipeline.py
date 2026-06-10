from datetime import date

from trading_agent_system.agents.premarket_agent.rag.indexing_pipeline import PreMarketRAGIndexingPipeline


def test_indexing_pipeline_prefers_event_cluster_cards():
    pipeline = PreMarketRAGIndexingPipeline()
    documents = pipeline.from_payloads(
        trading_day=date(2026, 6, 10),
        premarket_window_id="pmw_20260610",
        raw_documents=[],
        events=[],
        clusters=[
            {
                "cluster_id": "cluster_1",
                "primary_event_id": "evt_1",
                "supporting_event_ids": ["evt_2"],
                "title": "半导体: 并购重组政策催化",
                "summary": "政策支持并购重组。",
                "symbols": ["688981.SH"],
                "event_type": "official_policy",
                "primary_source_rank": "authorized_news",
                "importance": "A",
                "bias": "bullish",
                "confidence": 0.86,
                "risk_flags": [],
            }
        ],
    )

    assert documents[0].doc_id == "cluster_cluster_1"
    assert documents[0].content_type == "event_card"
    assert documents[0].event_cluster_id == "cluster_1"
    assert documents[0].themes == ["半导体"]
