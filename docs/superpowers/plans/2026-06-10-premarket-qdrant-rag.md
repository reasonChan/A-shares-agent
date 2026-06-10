# PreMarket Qdrant RAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Qdrant-backed event-first RAG layer for the premarket agent that produces traceable EvidencePacks for morning sections.

**Architecture:** Add `trading_agent_system/agents/premarket_agent/rag/` as a bounded package. It indexes `RawDocument`, `PreMarketEvent`, and `EventCluster` into structured records plus Qdrant vectors, then retrieves section-specific EvidencePacks through query planning, hybrid retrieval, fusion, deduplication, and budgeting.

**Tech Stack:** Python 3.11, Pydantic v2, SQLite existing `KnowledgeStore`, `qdrant-client` local mode, deterministic local embeddings, pytest, FastAPI debug endpoint.

---

## File Structure

- Create `configs/rag.premarket.yaml`: RAG backend, Qdrant, embedding, retrieval, diversity, and safety config.
- Modify `pyproject.toml`: add `qdrant-client` and `numpy`.
- Create `trading_agent_system/agents/premarket_agent/rag/schemas.py`: `RAGDocument`, `RetrievalFilter`, `RetrievalTask`, `RetrievalResult`, `EvidenceItem`, `EvidencePack`, `RAGEvaluationMetrics`.
- Create `trading_agent_system/agents/premarket_agent/rag/embeddings.py`: `EmbeddingProvider`, `DeterministicEmbeddingProvider`.
- Create `trading_agent_system/agents/premarket_agent/rag/stores/qdrant_vector_store.py`: Qdrant collection management, upsert, search.
- Create `trading_agent_system/agents/premarket_agent/rag/indexing_pipeline.py`: convert premarket payloads to `RAGDocument` event cards.
- Create `trading_agent_system/agents/premarket_agent/rag/query_planner.py`: build section-level tasks.
- Create retrievers under `trading_agent_system/agents/premarket_agent/rag/retrievers/`: structured, keyword, vector, risk, portfolio, recency.
- Create `fusion.py`, `deduper.py`, `context_budgeter.py`, `evidence_pack_builder.py`, `evaluation.py`, `rag_service.py`.
- Modify `trading_agent_system/agents/premarket_agent/agent.py`: instantiate and use RAG service when configured.
- Modify `scripts/run_premarket_agent.py`: load `configs/rag.premarket.yaml`.
- Modify `trading_agent_system/api/app.py` and `web/src/*`: expose and display RAG evidence debug data after backend is stable.

## Task 1: Dependencies and Config

**Files:**
- Modify: `pyproject.toml`
- Create: `configs/rag.premarket.yaml`
- Test: `tests/premarket_rag/test_rag_config.py`

- [ ] **Step 1: Write failing config test**

```python
from pathlib import Path
import yaml


def test_rag_config_enables_qdrant_local_mode():
    payload = yaml.safe_load(Path("configs/rag.premarket.yaml").read_text(encoding="utf-8"))

    assert payload["rag"]["enabled"] is True
    assert payload["rag"]["vector_store"]["backend"] == "qdrant"
    assert payload["rag"]["vector_store"]["mode"] == "local"
    assert payload["rag"]["embedding"]["provider"] == "deterministic"
    assert payload["rag"]["embedding"]["dimension"] == 384
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/premarket_rag/test_rag_config.py -q`
Expected: FAIL because config file does not exist.

- [ ] **Step 3: Add dependencies and config**

Add dependencies:

```toml
"numpy>=1.26,<3",
"qdrant-client>=1.9,<2",
```

Create config with the YAML from the design spec.

- [ ] **Step 4: Install dependencies and pass test**

Run: `.venv/bin/pip install -e .`
Run: `.venv/bin/pytest tests/premarket_rag/test_rag_config.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml configs/rag.premarket.yaml tests/premarket_rag/test_rag_config.py
MSG=$(git-guard format-msg --msg "feat: configure premarket qdrant rag" --agent codex)
git-guard pre-commit --msg "$MSG"
git commit -m "$MSG"
```

## Task 2: RAG Schemas and Embeddings

**Files:**
- Create: `trading_agent_system/agents/premarket_agent/rag/__init__.py`
- Create: `trading_agent_system/agents/premarket_agent/rag/schemas.py`
- Create: `trading_agent_system/agents/premarket_agent/rag/embeddings.py`
- Test: `tests/premarket_rag/test_rag_schemas_embeddings.py`

- [ ] **Step 1: Write failing schema and embedding tests**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/premarket_rag/test_rag_schemas_embeddings.py -q`
Expected: FAIL because package does not exist.

- [ ] **Step 3: Implement schemas and deterministic embeddings**

Implement Pydantic models and a hashing-based normalized vector:

```python
class DeterministicEmbeddingProvider:
    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension

    def embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        for token in text.split() or [text]:
            digest = sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]
```

- [ ] **Step 4: Run schema tests**

Run: `.venv/bin/pytest tests/premarket_rag/test_rag_schemas_embeddings.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add trading_agent_system/agents/premarket_agent/rag tests/premarket_rag/test_rag_schemas_embeddings.py
MSG=$(git-guard format-msg --msg "feat: add premarket rag schemas and embeddings" --agent codex)
git-guard pre-commit --msg "$MSG"
git commit -m "$MSG"
```

## Task 3: Qdrant Vector Store

**Files:**
- Create: `trading_agent_system/agents/premarket_agent/rag/stores/__init__.py`
- Create: `trading_agent_system/agents/premarket_agent/rag/stores/qdrant_vector_store.py`
- Test: `tests/premarket_rag/test_qdrant_vector_store.py`

- [ ] **Step 1: Write failing vector store test**

```python
from datetime import date, datetime, timezone

from trading_agent_system.agents.premarket_agent.rag.embeddings import DeterministicEmbeddingProvider
from trading_agent_system.agents.premarket_agent.rag.schemas import RAGDocument
from trading_agent_system.agents.premarket_agent.rag.stores.qdrant_vector_store import QdrantVectorStore


def test_qdrant_vector_store_upserts_and_searches_documents(tmp_path):
    provider = DeterministicEmbeddingProvider(dimension=32)
    store = QdrantVectorStore(path=tmp_path / "qdrant", collection_name="premarket_hot", vector_size=32)
    document = RAGDocument(
        doc_id="doc_chip",
        title="半导体并购重组",
        content="半导体 并购 重组 政策支持",
        content_type="event_card",
        source="央视财经",
        source_type="authorized_news",
        source_rank=0.8,
        fetched_at=datetime.now(timezone.utc),
        trading_day=date(2026, 6, 10),
        premarket_window_id="pmw_20260610",
        themes=["半导体"],
        content_hash="hash_chip",
    )

    store.upsert_documents([document], provider)
    results = store.search(
        query_vector=provider.embed_text("芯片 并购"),
        trading_day=date(2026, 6, 10),
        premarket_window_id="pmw_20260610",
        top_k=3,
    )

    assert results[0].doc_id == "doc_chip"
    assert results[0].score > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/premarket_rag/test_qdrant_vector_store.py -q`
Expected: FAIL because `QdrantVectorStore` does not exist.

- [ ] **Step 3: Implement Qdrant local store**

Use `QdrantClient(path=str(path))`, create collection when missing, store full document payload through `model_dump(mode="json")`, and convert search hits back to `VectorSearchHit`.

- [ ] **Step 4: Run vector store test**

Run: `.venv/bin/pytest tests/premarket_rag/test_qdrant_vector_store.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add trading_agent_system/agents/premarket_agent/rag/stores tests/premarket_rag/test_qdrant_vector_store.py
MSG=$(git-guard format-msg --msg "feat: add qdrant vector store" --agent codex)
git-guard pre-commit --msg "$MSG"
git commit -m "$MSG"
```

## Task 4: Indexing Pipeline

**Files:**
- Create: `trading_agent_system/agents/premarket_agent/rag/indexing_pipeline.py`
- Test: `tests/premarket_rag/test_rag_indexing_pipeline.py`

- [ ] **Step 1: Write failing indexing tests**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/premarket_rag/test_rag_indexing_pipeline.py -q`
Expected: FAIL because pipeline does not exist.

- [ ] **Step 3: Implement payload-to-RAGDocument conversion**

Convert clusters, events, and raw documents. Generate stable `content_hash` from `doc_id + title + content`, map source rank strings to numeric `source_rank`, and set `actionability="watch_only"` when risk flags include `unverified` or `rumor`.

- [ ] **Step 4: Run indexing test**

Run: `.venv/bin/pytest tests/premarket_rag/test_rag_indexing_pipeline.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add trading_agent_system/agents/premarket_agent/rag/indexing_pipeline.py tests/premarket_rag/test_rag_indexing_pipeline.py
MSG=$(git-guard format-msg --msg "feat: index premarket evidence documents" --agent codex)
git-guard pre-commit --msg "$MSG"
git commit -m "$MSG"
```

## Task 5: Query Planner and Retrievers

**Files:**
- Create: `trading_agent_system/agents/premarket_agent/rag/query_planner.py`
- Create: `trading_agent_system/agents/premarket_agent/rag/retrievers/base.py`
- Create: `trading_agent_system/agents/premarket_agent/rag/retrievers/structured_retriever.py`
- Create: `trading_agent_system/agents/premarket_agent/rag/retrievers/keyword_retriever.py`
- Create: `trading_agent_system/agents/premarket_agent/rag/retrievers/vector_retriever.py`
- Create: `trading_agent_system/agents/premarket_agent/rag/retrievers/risk_event_retriever.py`
- Test: `tests/premarket_rag/test_query_planner_retrievers.py`

- [ ] **Step 1: Write failing planner and retriever tests**

```python
from datetime import date

from trading_agent_system.agents.premarket_agent.rag.query_planner import PreMarketRAGQueryPlanner
from trading_agent_system.agents.premarket_agent.rag.retrievers.risk_event_retriever import RiskEventRetriever
from trading_agent_system.agents.premarket_agent.rag.schemas import RAGDocument


def test_query_planner_splits_by_morning_sections():
    planner = PreMarketRAGQueryPlanner()

    tasks = planner.build_tasks(trading_day=date(2026, 6, 10), premarket_window_id="pmw_20260610")

    sections = {task.section for task in tasks}
    assert "core_conclusion" in sections
    assert "portfolio_risks" in sections
    assert "theme_candidates" in sections
    assert len(tasks) >= 5


def test_risk_event_retriever_finds_risk_without_vector_search():
    document = RAGDocument(
        doc_id="doc_risk",
        title="收到监管函",
        content="公司收到监管函",
        content_type="event_card",
        source="上交所",
        source_type="exchange_notice",
        source_rank=1.0,
        fetched_at="2026-06-10T00:00:00Z",
        trading_day=date(2026, 6, 10),
        premarket_window_id="pmw_20260610",
        symbols=["600000.SH"],
        risk_flags=["regulatory_inquiry"],
        content_hash="hash_risk",
    )
    retriever = RiskEventRetriever([document])
    task = PreMarketRAGQueryPlanner().build_tasks(date(2026, 6, 10), "pmw_20260610")[0]

    results = retriever.retrieve(task)

    assert results[0].doc_id == "doc_risk"
    assert results[0].retrieval_method == "risk_event"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/premarket_rag/test_query_planner_retrievers.py -q`
Expected: FAIL because modules do not exist.

- [ ] **Step 3: Implement planner and retrievers**

Planner returns section tasks with metadata filters. Retrievers return `RetrievalResult` objects with `retrieval_method` set to the retriever name and `raw_score` in `[0, 1]`.

- [ ] **Step 4: Run tests**

Run: `.venv/bin/pytest tests/premarket_rag/test_query_planner_retrievers.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add trading_agent_system/agents/premarket_agent/rag/query_planner.py trading_agent_system/agents/premarket_agent/rag/retrievers tests/premarket_rag/test_query_planner_retrievers.py
MSG=$(git-guard format-msg --msg "feat: add premarket rag query planning and retrievers" --agent codex)
git-guard pre-commit --msg "$MSG"
git commit -m "$MSG"
```

## Task 6: Fusion, Dedup, Budget, and EvidencePack

**Files:**
- Create: `trading_agent_system/agents/premarket_agent/rag/fusion.py`
- Create: `trading_agent_system/agents/premarket_agent/rag/deduper.py`
- Create: `trading_agent_system/agents/premarket_agent/rag/context_budgeter.py`
- Create: `trading_agent_system/agents/premarket_agent/rag/evidence_pack_builder.py`
- Test: `tests/premarket_rag/test_evidence_pack_builder.py`

- [ ] **Step 1: Write failing evidence pack tests**

```python
from datetime import date

from trading_agent_system.agents.premarket_agent.rag.evidence_pack_builder import EvidencePackBuilder
from trading_agent_system.agents.premarket_agent.rag.schemas import RetrievalResult


def _result(result_id, cluster_id, score, confidence=0.9):
    return RetrievalResult(
        result_id=result_id,
        task_id="task_1",
        doc_id=result_id,
        event_cluster_id=cluster_id,
        content="公司公告收到监管函",
        title="监管函",
        source="上交所",
        source_type="exchange_notice",
        symbols=["600000.SH"],
        retrieval_method="structured",
        raw_score=score,
        final_score=score,
        evidence_ids=[result_id],
        confidence=confidence,
    )


def test_evidence_pack_dedups_event_clusters_and_cites_items():
    builder = EvidencePackBuilder(max_tokens=1200, max_per_event_cluster=1)

    pack = builder.build(
        trading_day=date(2026, 6, 10),
        premarket_window_id="pmw_20260610",
        section="portfolio_risks",
        query="持仓风险",
        results=[_result("ev_1", "cluster_1", 0.9), _result("ev_2", "cluster_1", 0.8)],
    )

    assert len(pack.items) == 1
    assert pack.dropped_duplicates == 1
    assert pack.items[0].citation_label == "[ev_1]"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/premarket_rag/test_evidence_pack_builder.py -q`
Expected: FAIL because builder does not exist.

- [ ] **Step 3: Implement RRF, dedup, and evidence pack builder**

`rrf_fuse()` groups by `doc_id`, `EventClusterDeduper` limits cluster repetition, and `ContextBudgeter` estimates tokens as `ceil(len(text) / 2)`.

- [ ] **Step 4: Run evidence pack tests**

Run: `.venv/bin/pytest tests/premarket_rag/test_evidence_pack_builder.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add trading_agent_system/agents/premarket_agent/rag/fusion.py trading_agent_system/agents/premarket_agent/rag/deduper.py trading_agent_system/agents/premarket_agent/rag/context_budgeter.py trading_agent_system/agents/premarket_agent/rag/evidence_pack_builder.py tests/premarket_rag/test_evidence_pack_builder.py
MSG=$(git-guard format-msg --msg "feat: build premarket rag evidence packs" --agent codex)
git-guard pre-commit --msg "$MSG"
git commit -m "$MSG"
```

## Task 7: RAG Service Integration

**Files:**
- Create: `trading_agent_system/agents/premarket_agent/rag/rag_service.py`
- Modify: `trading_agent_system/agents/premarket_agent/agent.py`
- Modify: `scripts/run_premarket_agent.py`
- Test: `tests/premarket_rag/test_premarket_rag_service.py`

- [ ] **Step 1: Write failing service test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/premarket_rag/test_premarket_rag_service.py -q`
Expected: FAIL because service does not exist.

- [ ] **Step 3: Implement service and optional agent integration**

`PreMarketRAGService` wires indexing pipeline, Qdrant store, planner, retrievers, fusion, and evidence pack builder. `PremarketAgent.run()` indexes payloads and publishes `premarket.rag_evidence_packs` when RAG is configured.

- [ ] **Step 4: Run service and premarket tests**

Run: `.venv/bin/pytest tests/premarket_rag tests/premarket -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add trading_agent_system/agents/premarket_agent/rag/rag_service.py trading_agent_system/agents/premarket_agent/agent.py scripts/run_premarket_agent.py tests/premarket_rag/test_premarket_rag_service.py
MSG=$(git-guard format-msg --msg "feat: integrate qdrant rag with premarket agent" --agent codex)
git-guard pre-commit --msg "$MSG"
git commit -m "$MSG"
```

## Task 8: Evaluation and Debug API

**Files:**
- Create: `trading_agent_system/agents/premarket_agent/rag/evaluation.py`
- Modify: `trading_agent_system/schemas.py`
- Modify: `trading_agent_system/api/app.py`
- Modify: `web/src/api.js`
- Modify: `web/src/main.jsx`
- Modify: `web/src/styles.css`
- Test: `tests/premarket_rag/test_rag_evaluation_api.py`

- [ ] **Step 1: Write failing evaluation/API test**

```python
from datetime import date

from trading_agent_system.agents.premarket_agent.rag.evaluation import RAGEvaluator
from trading_agent_system.agents.premarket_agent.rag.schemas import EvidenceItem, EvidencePack


def test_rag_evaluation_reports_duplicate_and_coverage_ratios():
    pack = EvidencePack(
        pack_id="pack_1",
        trading_day=date(2026, 6, 10),
        premarket_window_id="pmw_20260610",
        section="portfolio_risks",
        query="持仓风险",
        items=[
            EvidenceItem(
                evidence_id="ev_1",
                source_id="src_1",
                source="上交所",
                source_type="exchange_notice",
                source_rank=1.0,
                title="监管函",
                excerpt="收到监管函",
                confidence=0.9,
                citation_label="[ev_1]",
            )
        ],
        dropped_duplicates=2,
        token_estimate=120,
    )

    metrics = RAGEvaluator().evaluate_pack(pack)

    assert metrics.duplicate_ratio > 0
    assert metrics.evidence_coverage_ratio == 1.0
    assert metrics.citation_coverage_ratio == 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/premarket_rag/test_rag_evaluation_api.py -q`
Expected: FAIL because evaluator does not exist.

- [ ] **Step 3: Implement evaluator and latest evidence API**

Add endpoint `GET /api/premarket/rag/latest` reading latest `premarket.rag_evidence_packs` and `premarket.rag_evaluation` events.

- [ ] **Step 4: Add compact frontend RAG debug panel**

Show section packs, evidence count, duplicate drops, token estimate, source ranks, and citations in the existing observability/RAG area.

- [ ] **Step 5: Run full verification**

Run: `.venv/bin/pytest tests -q`
Run: `npm run build` in `web`
Run: `.venv/bin/python scripts/run_premarket_agent.py --date 2026-06-10 --config configs/app.yaml`
Expected: all pass and latest RAG API returns evidence packs.

- [ ] **Step 6: Commit**

```bash
git add trading_agent_system/agents/premarket_agent/rag/evaluation.py trading_agent_system/schemas.py trading_agent_system/api/app.py web/src/api.js web/src/main.jsx web/src/styles.css tests/premarket_rag/test_rag_evaluation_api.py
MSG=$(git-guard format-msg --msg "feat: expose premarket rag evaluation" --agent codex)
git-guard pre-commit --msg "$MSG"
git commit -m "$MSG"
```

## Final Verification

- [ ] Run `.venv/bin/pytest tests -q`; expected all tests pass.
- [ ] Run `npm run build` in `web`; expected Vite build succeeds.
- [ ] Run `.venv/bin/python scripts/run_premarket_agent.py --date 2026-06-10 --config configs/app.yaml`; expected report plus `premarket.rag_evidence_packs` events.
- [ ] Check the local latest RAG API endpoint `/api/premarket/rag/latest`; expected latest packs and metrics.
- [ ] Run `git-guard pre-push --branch feat/agent-observability-rag && git push`; expected dry-run and push succeed.

## Self-Review

- Spec coverage: covers Qdrant local mode, replaceable embedding provider, section tasks, retrievers, RRF, business scoring, evidence packs, safety, evaluation, and observability.
- Placeholder scan: no unfinished marker, incomplete task, or deferred implementation wording remains.
- Type consistency: names are consistent across tasks: `RAGDocument`, `RetrievalTask`, `RetrievalResult`, `EvidencePack`, `PreMarketRAGService`, `QdrantVectorStore`, `DeterministicEmbeddingProvider`.
