# Premarket Debug Tab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a dedicated `盘前调试` tab that shows how crawler/provider data flows into events, clusters, KnowledgeStore, RAG evidence, and the final premarket conclusion.

**Architecture:** Add one FastAPI aggregation endpoint backed by existing JSONL events, report files, and `KnowledgeStore`. Add one frontend API client and one React page inside the current console shell; no trading behavior changes.

**Tech Stack:** FastAPI, Python 3.13, pytest, React 18, Vite, CSS.

---

## File Structure

- Modify `trading_agent_system/api/app.py`: add `GET /api/premarket/debug`.
- Modify `web/src/api.js`: add `fetchPremarketDebug`.
- Modify `web/src/main.jsx`: add top-level `盘前调试` tab and `PremarketDebugPage`.
- Modify `web/src/styles.css`: add debug page layout.
- Create `tests/premarket/test_premarket_debug_api.py`: backend endpoint coverage.
- Create `tests/frontend/test_premarket_debug_tab.py`: static frontend coverage.

## Tasks

### Task 1: Backend Debug API

- [ ] Write `tests/premarket/test_premarket_debug_api.py` that seeds JSONL events, KnowledgeStore, and report JSON, then asserts `/api/premarket/debug` returns steps, knowledge, rag, and conclusion.
- [ ] Run `.venv/bin/python -m pytest tests/premarket/test_premarket_debug_api.py -q` and verify it fails because endpoint is missing.
- [ ] Implement endpoint and helpers in `trading_agent_system/api/app.py`.
- [ ] Re-run the focused backend test and verify it passes.

### Task 2: Frontend Debug Tab

- [ ] Write `tests/frontend/test_premarket_debug_tab.py` to assert the tab label, API client, and core chain labels exist.
- [ ] Run `.venv/bin/python -m pytest tests/frontend/test_premarket_debug_tab.py -q` and verify it fails.
- [ ] Add `fetchPremarketDebug` in `web/src/api.js`.
- [ ] Add `PremarketDebugPage` and navigation branch in `web/src/main.jsx`.
- [ ] Add CSS for the debug page in `web/src/styles.css`.
- [ ] Re-run the focused frontend static test and verify it passes.

### Task 3: Verification

- [ ] Run `.venv/bin/python -m pytest tests/premarket/test_premarket_debug_api.py tests/frontend/test_premarket_debug_tab.py -q`.
- [ ] Run `.venv/bin/python -m pytest -q`.
- [ ] Run `cd web && npm run build`.
- [ ] Restart API server because `app.py` changed.
- [ ] Confirm `curl -s http://127.0.0.1:8000/api/premarket/debug?q=机器人 | head -c 400` returns JSON.

## Self-Review

- Spec coverage: backend aggregation, frontend tab, manual run/refresh, query view, and no trading behavior changes are covered.
- Placeholder scan: no deferred placeholders.
- Type consistency: frontend consumes the endpoint keys `steps`, `knowledge`, `rag`, `conclusion`, and `warnings`.
