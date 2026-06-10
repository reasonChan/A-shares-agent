from datetime import date, datetime, timezone

from trading_agent_system.agents.premarket_agent.rag.embeddings import DeterministicEmbeddingProvider
from trading_agent_system.agents.premarket_agent.rag.schemas import EvidenceItem, EvidencePack, RAGDocument


def test_rag_document_requires_traceable_content_hash():
    document = RAGDocument(
        doc_id="doc_1",
        title="监管函",
        content="公司收到监管函",
        content_type="event_card",
        source="上交所",
        source_type="exchange_notice",
        source_rank=1.0,
        fetched_at=datetime.now(timezone.utc),
        trading_day=date(2026, 6, 10),
        premarket_window_id="pmw_20260610",
        event_id="evt_1",
        event_cluster_id="cluster_1",
        risk_flags=["regulatory_inquiry"],
        content_hash="hash_1",
    )

    assert document.event_id == "evt_1"
    assert document.content_type == "event_card"


def test_deterministic_embedding_provider_is_stable():
    provider = DeterministicEmbeddingProvider(dimension=16)

    first = provider.embed_text("半导体 并购 重组")
    second = provider.embed_text("半导体 并购 重组")

    assert first == second
    assert len(first) == 16
    assert abs(sum(value * value for value in first) - 1.0) < 1e-6


def test_evidence_pack_items_have_citation_labels():
    item = EvidenceItem(
        evidence_id="ev_1",
        source_id="src_1",
        source="上交所",
        source_type="exchange_notice",
        source_rank=1.0,
        title="监管函",
        excerpt="公司收到监管函",
        confidence=0.9,
        citation_label="[ev_1]",
    )
    pack = EvidencePack(
        pack_id="pack_1",
        trading_day=date(2026, 6, 10),
        premarket_window_id="pmw_20260610",
        section="portfolio_risks",
        query="持仓风险",
        items=[item],
    )

    assert pack.items[0].citation_label == "[ev_1]"
