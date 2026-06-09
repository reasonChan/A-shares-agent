from __future__ import annotations

from datetime import date

from .schemas import KnowledgeSearchResult
from .store import KnowledgeStore


class RagRetriever:
    def __init__(self, store: KnowledgeStore) -> None:
        self.store = store

    def search(
        self,
        *,
        query: str,
        trading_day: date | None = None,
        themes: list[str] | None = None,
        symbols: list[str] | None = None,
        source_rank_min: str | None = None,
        top_k: int = 8,
    ) -> list[KnowledgeSearchResult]:
        return self.store.search(
            query,
            trading_day=trading_day,
            themes=themes,
            symbols=symbols,
            source_rank_min=source_rank_min,
            top_k=top_k,
        )
