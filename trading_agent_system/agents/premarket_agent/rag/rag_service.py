from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from trading_agent_system.agents.premarket_agent.rag.deduper import EventClusterDeduper
from trading_agent_system.agents.premarket_agent.rag.embeddings import DeterministicEmbeddingProvider, EmbeddingProvider
from trading_agent_system.agents.premarket_agent.rag.evidence_pack_builder import EvidencePackBuilder
from trading_agent_system.agents.premarket_agent.rag.fusion import rrf_fuse
from trading_agent_system.agents.premarket_agent.rag.indexing_pipeline import PreMarketRAGIndexingPipeline
from trading_agent_system.agents.premarket_agent.rag.query_planner import PreMarketRAGQueryPlanner
from trading_agent_system.agents.premarket_agent.rag.retrievers import (
    KeywordRetriever,
    PortfolioRetriever,
    RecencyRetriever,
    RiskEventRetriever,
    StructuredRetriever,
    ThemeRetriever,
    VectorRetriever,
)
from trading_agent_system.agents.premarket_agent.rag.schemas import EvidencePack, RAGDocument, RetrievalResult, RetrievalTask
from trading_agent_system.agents.premarket_agent.rag.stores import QdrantVectorStore


class PreMarketRAGService:
    def __init__(
        self,
        *,
        vector_store: QdrantVectorStore,
        embeddings: EmbeddingProvider,
        planner: PreMarketRAGQueryPlanner | None = None,
        evidence_builder: EvidencePackBuilder | None = None,
        indexing_pipeline: PreMarketRAGIndexingPipeline | None = None,
    ) -> None:
        self.vector_store = vector_store
        self.embeddings = embeddings
        self.planner = planner or PreMarketRAGQueryPlanner()
        self.evidence_builder = evidence_builder or EvidencePackBuilder()
        self.indexing_pipeline = indexing_pipeline or PreMarketRAGIndexingPipeline()
        self.documents: list[RAGDocument] = []

    @classmethod
    def local(
        cls,
        *,
        qdrant_path: str | Path,
        collection_name: str,
        embedding_dimension: int = 384,
    ) -> "PreMarketRAGService":
        embeddings = DeterministicEmbeddingProvider(dimension=embedding_dimension)
        vector_store = QdrantVectorStore(
            path=qdrant_path,
            collection_name=collection_name,
            vector_size=embedding_dimension,
        )
        return cls(vector_store=vector_store, embeddings=embeddings)

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "PreMarketRAGService | None":
        rag = config.get("rag", {})
        if not isinstance(rag, dict) or not rag.get("enabled", False):
            return None
        vector_config = rag.get("vector_store", {}) if isinstance(rag.get("vector_store"), dict) else {}
        embedding_config = rag.get("embedding", {}) if isinstance(rag.get("embedding"), dict) else {}
        dimension = int(embedding_config.get("dimension", 384))
        collection_name = str(vector_config.get("collection_hot") or "premarket_hot")
        return cls.local(
            qdrant_path=Path(str(vector_config.get("path") or "data/qdrant")),
            collection_name=collection_name,
            embedding_dimension=dimension,
        )

    def index_payloads(
        self,
        *,
        trading_day: date,
        premarket_window_id: str,
        raw_documents: list[dict[str, Any]],
        events: list[dict[str, Any]],
        clusters: list[dict[str, Any]],
    ) -> list[RAGDocument]:
        documents = self.indexing_pipeline.from_payloads(
            trading_day=trading_day,
            premarket_window_id=premarket_window_id,
            raw_documents=raw_documents,
            events=events,
            clusters=clusters,
        )
        self.documents = _dedupe_documents([*self.documents, *documents])
        self.vector_store.upsert_documents(documents, self.embeddings)
        return documents

    def build_retrieval_tasks(self, trading_day: date, premarket_window_id: str) -> list[RetrievalTask]:
        return self.planner.build_tasks(trading_day=trading_day, premarket_window_id=premarket_window_id)

    def retrieve(self, task: RetrievalTask) -> list[RetrievalResult]:
        results_by_retriever: dict[str, list[RetrievalResult]] = {}
        retrievers = self._retrievers()
        for retriever_name in task.retrievers:
            retriever = retrievers.get(retriever_name)
            if retriever is None:
                continue
            results_by_retriever[retriever_name] = retriever.retrieve(task)
        if not results_by_retriever:
            return []
        fused = rrf_fuse(results_by_retriever)
        deduped, _ = EventClusterDeduper(max_per_cluster=1).dedup(fused)
        return deduped[: task.final_top_k]

    def retrieve_evidence_pack(self, task: RetrievalTask, trading_day: date, premarket_window_id: str) -> EvidencePack:
        return self.evidence_builder.build(
            trading_day=trading_day,
            premarket_window_id=premarket_window_id,
            section=task.section,
            query=task.query,
            results=self.retrieve(task),
        )

    def retrieve_all_evidence_packs(self, trading_day: date, premarket_window_id: str) -> list[EvidencePack]:
        return [
            self.retrieve_evidence_pack(task, trading_day, premarket_window_id)
            for task in self.build_retrieval_tasks(trading_day, premarket_window_id)
        ]

    def _retrievers(self) -> dict[str, object]:
        return {
            "structured": StructuredRetriever(self.documents),
            "keyword": KeywordRetriever(self.documents),
            "risk_event": RiskEventRetriever(self.documents),
            "portfolio": PortfolioRetriever(self.documents),
            "theme": ThemeRetriever(self.documents),
            "recency": RecencyRetriever(self.documents),
            "vector": VectorRetriever(self.vector_store, self.embeddings),
        }


def _dedupe_documents(documents: list[RAGDocument]) -> list[RAGDocument]:
    by_id = {document.doc_id: document for document in documents}
    return list(by_id.values())
