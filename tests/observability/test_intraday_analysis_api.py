from __future__ import annotations

from datetime import date

from trading_agent_system.api import app as api_module
from trading_agent_system.core.events import make_envelope
from trading_agent_system.core.storage import JsonlEventRepository


def test_intraday_latest_api_returns_latest_analysis_report(tmp_path, monkeypatch):
    monkeypatch.setattr(api_module, "EVENT_DIR", tmp_path / "events")
    repository = JsonlEventRepository(api_module.EVENT_DIR)
    repository.append_envelope(
        make_envelope(
            "intraday.analysis",
            {
                "report_id": "intraday_old",
                "summary": "old",
                "symbol_count": 0,
                "trade_intent_count": 0,
            },
            producer="intraday_agent",
            trading_day=date(2026, 6, 9),
            run_id="run_old",
        )
    )
    repository.append_envelope(
        make_envelope(
            "intraday.analysis",
            {
                "report_id": "intraday_new",
                "summary": "重点板块 半导体",
                "symbol_count": 2,
                "trade_intent_count": 1,
            },
            producer="intraday_agent",
            trading_day=date(2026, 6, 10),
            run_id="run_new",
        )
    )

    response = api_module.latest_intraday_analysis()

    assert response["report"]["report_id"] == "intraday_new"
    assert response["report"]["summary"] == "重点板块 半导体"
    assert response["event"]["producer"] == "intraday_agent"
    assert response["event"]["trading_day"] == "2026-06-10"
