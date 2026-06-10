from datetime import date

from trading_agent_system.core.knowledge import KnowledgeRecord, KnowledgeStore, RagRetriever


def test_knowledge_store_indexes_and_searches_records(tmp_path):
    store = KnowledgeStore(tmp_path / "knowledge.sqlite")
    store.upsert(
        KnowledgeRecord(
            record_id="rec_robot",
            record_type="event",
            trading_day=date(2026, 6, 10),
            source="央视财经",
            source_rank="authorized_news",
            title="人形机器人专项行动启动",
            summary="工信部和国资委推动人形机器人常态化部署。",
            content="人形机器人 具身智能 政策支持",
            themes=["机器人"],
            symbols=["002747.SZ"],
            evidence_ids=["evt_robot"],
            confidence=0.9,
        )
    )
    store.upsert(
        KnowledgeRecord(
            record_id="rec_chip",
            record_type="event",
            trading_day=date(2026, 6, 11),
            source="新浪财经",
            source_rank="authorized_news",
            title="芯片产业链活跃",
            summary="半导体方向出现海外催化。",
            content="半导体 芯片",
            themes=["半导体"],
            symbols=["688981.SH"],
            evidence_ids=["evt_chip"],
            confidence=0.8,
        )
    )

    results = store.search("机器人 政策", trading_day=date(2026, 6, 10), themes=["机器人"], top_k=5)

    assert len(results) == 1
    assert results[0].record.record_id == "rec_robot"
    assert results[0].record.evidence_ids == ["evt_robot"]
    assert results[0].score > 0


def test_retriever_applies_source_rank_filter(tmp_path):
    store = KnowledgeStore(tmp_path / "knowledge.sqlite")
    store.upsert(
        KnowledgeRecord(
            record_id="rec_social",
            record_type="raw_document",
            trading_day=date(2026, 6, 10),
            source="股吧",
            source_rank="social",
            title="传闻机器人利好",
            summary="未确认消息。",
            content="机器人",
            themes=["机器人"],
            confidence=0.2,
        )
    )
    store.upsert(
        KnowledgeRecord(
            record_id="rec_official",
            record_type="event",
            trading_day=date(2026, 6, 10),
            source="证监会",
            source_rank="official",
            title="机器人政策确认",
            summary="官方政策确认。",
            content="机器人 政策",
            themes=["机器人"],
            confidence=0.95,
        )
    )

    results = RagRetriever(store).search(
        query="机器人",
        trading_day=date(2026, 6, 10),
        themes=["机器人"],
        source_rank_min="authorized_news",
        top_k=5,
    )

    assert [item.record.record_id for item in results] == ["rec_official"]
