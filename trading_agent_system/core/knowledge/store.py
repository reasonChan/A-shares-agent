from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

from .schemas import KnowledgeRecord, KnowledgeSearchResult


SOURCE_RANK_SCORE = {
    "official": 6,
    "authorized_news": 5,
    "market_data": 4,
    "overseas": 3,
    "internal": 2,
    "social": 1,
}


class KnowledgeStore:
    def __init__(self, path: str | Path = "data/knowledge.sqlite") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def upsert(self, record: KnowledgeRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                insert into knowledge_records (
                    record_id, record_type, trading_day, source, source_rank, title, summary,
                    content, url, symbols, themes, event_ids, cluster_ids, evidence_ids,
                    confidence, importance, metadata, created_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(record_id) do update set
                    record_type=excluded.record_type,
                    trading_day=excluded.trading_day,
                    source=excluded.source,
                    source_rank=excluded.source_rank,
                    title=excluded.title,
                    summary=excluded.summary,
                    content=excluded.content,
                    url=excluded.url,
                    symbols=excluded.symbols,
                    themes=excluded.themes,
                    event_ids=excluded.event_ids,
                    cluster_ids=excluded.cluster_ids,
                    evidence_ids=excluded.evidence_ids,
                    confidence=excluded.confidence,
                    importance=excluded.importance,
                    metadata=excluded.metadata,
                    created_at=excluded.created_at
                """,
                self._record_values(record),
            )

    def upsert_many(self, records: list[KnowledgeRecord]) -> None:
        for record in records:
            self.upsert(record)

    def search(
        self,
        query: str,
        *,
        trading_day: date | None = None,
        themes: list[str] | None = None,
        symbols: list[str] | None = None,
        source_rank_min: str | None = None,
        record_types: list[str] | None = None,
        top_k: int = 8,
    ) -> list[KnowledgeSearchResult]:
        records = self.list_records(trading_day=trading_day, record_types=record_types)
        terms = [term.lower() for term in query.split() if term.strip()]
        results: list[KnowledgeSearchResult] = []
        for record in records:
            if themes and not set(themes).intersection(record.themes):
                continue
            if symbols and not set(symbols).intersection(record.symbols):
                continue
            if source_rank_min and not self._rank_at_least(record.source_rank, source_rank_min):
                continue
            score, matched = self._score(record, terms)
            if score <= 0 and terms:
                continue
            results.append(KnowledgeSearchResult(record=record, score=score, matched_terms=matched))
        results.sort(
            key=lambda item: (
                item.score,
                SOURCE_RANK_SCORE.get(item.record.source_rank, 0),
                item.record.confidence,
                item.record.created_at,
            ),
            reverse=True,
        )
        return results[:top_k]

    def list_records(
        self,
        *,
        trading_day: date | None = None,
        record_types: list[str] | None = None,
        limit: int | None = None,
    ) -> list[KnowledgeRecord]:
        clauses: list[str] = []
        params: list[str] = []
        if trading_day is not None:
            clauses.append("trading_day = ?")
            params.append(trading_day.isoformat())
        if record_types:
            placeholders = ",".join("?" for _ in record_types)
            clauses.append(f"record_type in ({placeholders})")
            params.extend(record_types)
        sql = "select * from knowledge_records"
        if clauses:
            sql += " where " + " and ".join(clauses)
        sql += " order by created_at asc"
        if limit is not None and limit >= 0:
            sql += " limit ?"
            params.append(str(limit))
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_record(row) for row in rows]

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                create table if not exists knowledge_records (
                    record_id text primary key,
                    record_type text not null,
                    trading_day text,
                    source text not null,
                    source_rank text not null,
                    title text not null,
                    summary text not null,
                    content text not null,
                    url text,
                    symbols text not null,
                    themes text not null,
                    event_ids text not null,
                    cluster_ids text not null,
                    evidence_ids text not null,
                    confidence real not null,
                    importance text not null,
                    metadata text not null,
                    created_at text not null
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _record_values(self, record: KnowledgeRecord) -> tuple[object, ...]:
        return (
            record.record_id,
            record.record_type,
            record.trading_day.isoformat() if record.trading_day else None,
            record.source,
            record.source_rank,
            record.title,
            record.summary,
            record.content,
            record.url,
            json.dumps(record.symbols, ensure_ascii=False),
            json.dumps(record.themes, ensure_ascii=False),
            json.dumps(record.event_ids, ensure_ascii=False),
            json.dumps(record.cluster_ids, ensure_ascii=False),
            json.dumps(record.evidence_ids, ensure_ascii=False),
            record.confidence,
            record.importance,
            json.dumps(record.metadata, ensure_ascii=False, default=str),
            record.created_at.isoformat(),
        )

    def _row_to_record(self, row: sqlite3.Row) -> KnowledgeRecord:
        return KnowledgeRecord(
            record_id=row["record_id"],
            record_type=row["record_type"],
            trading_day=date.fromisoformat(row["trading_day"]) if row["trading_day"] else None,
            source=row["source"],
            source_rank=row["source_rank"],
            title=row["title"],
            summary=row["summary"],
            content=row["content"],
            url=row["url"],
            symbols=json.loads(row["symbols"]),
            themes=json.loads(row["themes"]),
            event_ids=json.loads(row["event_ids"]),
            cluster_ids=json.loads(row["cluster_ids"]),
            evidence_ids=json.loads(row["evidence_ids"]),
            confidence=float(row["confidence"]),
            importance=row["importance"],
            metadata=json.loads(row["metadata"]),
            created_at=row["created_at"],
        )

    def _score(self, record: KnowledgeRecord, terms: list[str]) -> tuple[float, list[str]]:
        haystack = " ".join(
            [
                record.title,
                record.summary,
                record.content,
                " ".join(record.symbols),
                " ".join(record.themes),
                record.source,
            ]
        ).lower()
        matched = [term for term in terms if term in haystack]
        term_score = len(matched) / max(1, len(terms))
        quality_score = SOURCE_RANK_SCORE.get(record.source_rank, 0) / 6
        return term_score * 2 + quality_score * 0.35 + record.confidence * 0.25, matched

    def _rank_at_least(self, actual: str, minimum: str) -> bool:
        return SOURCE_RANK_SCORE.get(actual, 0) >= SOURCE_RANK_SCORE.get(minimum, 0)
