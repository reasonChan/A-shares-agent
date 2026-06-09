from datetime import date

from trading_agent_system.api import app as api_module
from trading_agent_system.core.events import make_envelope
from trading_agent_system.core.knowledge import KnowledgeRecord, KnowledgeStore
from trading_agent_system.core.observability import MetricsRecorder, TraceLogger
from trading_agent_system.core.storage import JsonlEventRepository


def test_observability_api_reads_events_traces_metrics_and_knowledge(tmp_path, monkeypatch):
    monkeypatch.setattr(api_module, "EVENT_DIR", tmp_path / "events")
    monkeypatch.setattr(api_module, "TRACE_DIR", tmp_path / "traces")
    monkeypatch.setattr(api_module, "METRICS_DIR", tmp_path / "metrics")
    monkeypatch.setattr(api_module, "KNOWLEDGE_PATH", tmp_path / "knowledge.sqlite")

    JsonlEventRepository(api_module.EVENT_DIR).append_envelope(
        make_envelope(
            "premarket.instructions",
            {"items": [{"target": "板块:机器人"}]},
            producer="premarket_agent",
            trading_day=date(2026, 6, 10),
            run_id="run_1",
        )
    )
    TraceLogger(api_module.TRACE_DIR).record(
        agent="premarket_agent",
        step="theme_detection",
        run_id="run_1",
        status="success",
        decision_summary="机器人进入观察",
    )
    MetricsRecorder(api_module.METRICS_DIR).record(
        "agent_run_total",
        1,
        tags={"agent": "premarket", "status": "success"},
        run_id="run_1",
    )
    store = KnowledgeStore(api_module.KNOWLEDGE_PATH)
    store.upsert(
        KnowledgeRecord(
            record_id="rec_robot",
            record_type="event",
            trading_day=date(2026, 6, 10),
            source="央视财经",
            source_rank="authorized_news",
            title="机器人政策催化",
            summary="人形机器人专项行动。",
            content="机器人 政策",
            themes=["机器人"],
            confidence=0.9,
        )
    )

    events = api_module.observability_events(topic="premarket.instructions", limit=100)
    traces = api_module.observability_traces(run_id="run_1", limit=100)
    metrics = api_module.observability_metrics(name="agent_run_total", limit=100)
    search = api_module.observability_knowledge_search(
        q="机器人",
        trading_day=date(2026, 6, 10),
        theme=["机器人"],
        symbol=None,
        source_rank_min=None,
        top_k=8,
    )

    assert events["events"][0]["payload"]["items"][0]["target"] == "板块:机器人"
    assert traces["traces"][0]["decision_summary"] == "机器人进入观察"
    assert metrics["metrics"][0]["tags"]["status"] == "success"
    assert search["results"][0]["record"]["record_id"] == "rec_robot"
