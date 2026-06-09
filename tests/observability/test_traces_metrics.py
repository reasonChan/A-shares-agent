from trading_agent_system.core.observability import MetricsRecorder, TraceLogger


def test_trace_logger_records_successful_step(tmp_path):
    logger = TraceLogger(base_dir=tmp_path / "traces")

    with logger.step(
        agent="premarket_agent",
        step="theme_detection",
        run_id="run_1",
        input_refs=["evt_1"],
        evidence_ids=["evt_1"],
    ) as span:
        span.set_output_refs(["theme_1"])
        span.set_summary("机器人进入观察")

    traces = logger.load(run_id="run_1")

    assert len(traces) == 1
    assert traces[0].status == "success"
    assert traces[0].duration_ms >= 0
    assert traces[0].output_refs == ["theme_1"]
    assert traces[0].decision_summary == "机器人进入观察"


def test_trace_logger_records_failed_step(tmp_path):
    logger = TraceLogger(base_dir=tmp_path / "traces")

    try:
        with logger.step(agent="premarket_agent", step="collect_sources", run_id="run_2"):
            raise RuntimeError("source failed")
    except RuntimeError:
        pass

    traces = logger.load(run_id="run_2")

    assert traces[0].status == "failed"
    assert "source failed" in traces[0].error


def test_metrics_recorder_writes_and_filters_metrics(tmp_path):
    recorder = MetricsRecorder(base_dir=tmp_path / "metrics")

    recorder.record("agent_run_total", 1, tags={"agent": "premarket", "status": "success"}, run_id="run_1")
    recorder.record("rag_query_duration_ms", 42, tags={"agent": "intraday"}, run_id="run_2")

    loaded = recorder.load(name="agent_run_total")

    assert len(loaded) == 1
    assert loaded[0].name == "agent_run_total"
    assert loaded[0].value == 1
    assert loaded[0].tags["status"] == "success"
