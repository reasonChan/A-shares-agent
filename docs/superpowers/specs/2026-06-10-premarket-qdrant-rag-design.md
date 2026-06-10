# PreMarket Qdrant RAG Design

## Goal

Upgrade the premarket information layer from a light keyword knowledge search into an event-first hybrid RAG system with Qdrant vector retrieval, section-level evidence packs, deduplication, and measurable evidence quality.

## Scope

This design focuses on the premarket chain only. The RAG layer provides evidence retrieval, ranking, compression, and validation context for `MorningBrief`, `OpeningRadar`, and `PreMarketInstruction`. It must not generate `TradeIntent`, orders, broker instructions, or concrete buy/sell instructions.

## Architecture

The first production-shaped version uses local Qdrant mode for vector search, while retaining SQLite as the structured source of truth through the existing `KnowledgeStore`. The new premarket RAG package lives under `trading_agent_system/agents/premarket_agent/rag/` and exposes `PreMarketRAGService`.

```text
RawDocument / PreMarketEvent / EventCluster
  -> RAGDocument / EventCard
  -> SQLite structured records
  -> Keyword index
  -> Qdrant vector index
  -> RetrievalTask per morning section
  -> structured + keyword + vector + risk + portfolio retrieval
  -> RRF fusion + business score
  -> event-cluster dedup + context budget
  -> EvidencePack
  -> builders and API debug views
```

## Vector Store Choice

Qdrant is the default vector backend. The implementation uses `qdrant-client` local disk mode at `data/qdrant` by default, so the app remains runnable without Docker or a separate database service. The interface keeps `VectorStore` replaceable so later versions can move to Qdrant Server, Milvus, pgvector, or another backend.

Milvus and pgvector are intentionally not first-version defaults. Milvus is valuable at larger scale but adds operational weight now. pgvector is attractive when PostgreSQL is already part of the stack, but this project currently uses SQLite.

## Embeddings

Embeddings are provided through an interface:

```text
EmbeddingProvider.embed_text(text: str) -> list[float]
EmbeddingProvider.embed_many(texts: list[str]) -> list[list[float]]
```

The first implementation ships with `DeterministicEmbeddingProvider`, which uses stable hashing to generate fixed-size vectors for local tests and offline demos. This makes Qdrant integration real while avoiding API keys or model downloads. A later `OpenAIEmbeddingProvider` or local model provider can replace it without changing retrieval logic.

## RAG Data Model

`RAGDocument` is the retrieval unit. It stores document identity, source metadata, trading day, premarket window, symbols, themes, event type, event id, event cluster id, confidence, actionability, risk flags, and content hash. Default RAG content should prefer compact event cards over full raw document text.

`RetrievalTask` is the query unit. It splits the morning workflow into sections:

- `core_conclusion`
- `post_close_events`
- `portfolio_risks`
- `theme_candidates`
- `macro_calendar`
- `overseas_mapping`
- `avoid_list`
- `opening_radar`
- `premarket_instructions`

`EvidencePack` is the builder-facing output. Every item must include citation labels and at least one traceable id from `evidence_id`, `event_id`, `event_cluster_id`, or `source_id`.

## Retrieval Strategy

Each task runs a bounded set of retrievers:

- `StructuredRetriever` uses exact metadata filters over SQLite-backed RAG records.
- `KeywordRetriever` handles symbols, company names, announcement words, and risk phrases.
- `VectorRetriever` queries Qdrant with metadata filters.
- `RiskEventRetriever` guarantees recall for regulatory, suspension, delisting, litigation, reduction, debt, and loss risks.
- `PortfolioRetriever` guarantees recall for current holdings and watchlist symbols.
- `RecencyRetriever` boosts the hot premarket window.

The retrievers are fused with weighted Reciprocal Rank Fusion. A business score then boosts source quality, importance, recency, holding/watchlist relevance, and verified status, while penalizing duplicate clusters, stale items, rumors, and social-only evidence.

## Safety Rules

- Social or unverified evidence can only be `watch_only`.
- Evidence packs must not contain direct trade intent fields.
- Claims in derived outputs must cite evidence from the pack.
- `PreMarketInstruction` may say watch, avoid, reduce-only, require confirmation, or wait for auction confirmation. It must not say buy, sell, order, or trade intent.
- If Qdrant is unavailable, the RAG service falls back to structured and keyword retrieval and records a warning.

## Configuration

Add `configs/rag.premarket.yaml`:

```yaml
rag:
  enabled: true
  timezone: Asia/Shanghai
  vector_store:
    backend: qdrant
    mode: local
    path: data/qdrant
    collection_hot: premarket_hot
    collection_warm: premarket_warm
  embedding:
    provider: deterministic
    dimension: 384
  retrieval:
    default_top_k_per_retriever: 30
    default_final_top_k: 10
    metadata_filter_first: true
    require_premarket_window_filter: true
  diversity:
    max_per_event_cluster: 1
    max_per_symbol_per_section: 3
    max_per_theme_per_section: 5
  context_budget:
    total_max_tokens: 12000
  safety:
    block_social_as_candidate: true
    require_evidence_for_every_claim: true
    forbid_trade_words_in_instruction: true
```

## Integration Points

`PremarketAgent.run()` already creates raw documents, normalized events, clusters, morning brief, opening radar, and instruction payloads. The RAG service should first index raw documents, events, and clusters after clustering. It should then build evidence packs before final report publication. The initial integration may publish packs and metrics without fully rewriting the current rule-based builders; this keeps the chain stable while making the RAG layer observable.

## Observability and Evaluation

The RAG service records:

- `rag_index_records_total`
- `rag_retrieval_total`
- `rag_retrieval_latency_ms`
- `rag_evidence_token_estimate`
- `rag_duplicate_ratio`
- `rag_low_confidence_leakage_ratio`
- `rag_evidence_coverage_ratio`

`RAGEvaluator` produces section-level metrics for duplicate ratio, low-confidence leakage, evidence coverage, citation coverage, average source rank, token count, and retrieval latency. Golden-set recall can be added when labeled fixtures exist.

## Acceptance Criteria

1. Premarket RAG indexing writes event cards to SQLite and Qdrant.
2. Query planning splits a morning run into multiple section-specific retrieval tasks.
3. Vector retrieval works through Qdrant local mode and is replaceable through an interface.
4. Evidence packs deduplicate repeated event clusters and enforce citation labels.
5. Social/unverified evidence cannot become candidate evidence.
6. API and/or observability endpoints can inspect evidence packs and evaluation metrics.
7. Existing premarket, intraday, risk, and frontend tests keep passing.
