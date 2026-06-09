from __future__ import annotations

from datetime import date
from typing import Any

from .schemas import KnowledgeRecord
from .store import KnowledgeStore


class RagIndexer:
    def __init__(self, store: KnowledgeStore) -> None:
        self.store = store

    def index_premarket_payload(
        self,
        *,
        trading_day: date,
        raw_documents: list[dict[str, Any]] | None = None,
        events: list[dict[str, Any]] | None = None,
        clusters: list[dict[str, Any]] | None = None,
        morning_brief: dict[str, Any] | None = None,
        instruction: dict[str, Any] | None = None,
    ) -> list[KnowledgeRecord]:
        records: list[KnowledgeRecord] = []
        records.extend(self._raw_documents(trading_day, raw_documents or []))
        records.extend(self._events(trading_day, events or []))
        records.extend(self._clusters(trading_day, clusters or []))
        if morning_brief:
            records.extend(self._morning_brief(trading_day, morning_brief))
        if instruction:
            records.extend(self._instruction(trading_day, instruction))
        self.store.upsert_many(records)
        return records

    def _raw_documents(self, trading_day: date, documents: list[dict[str, Any]]) -> list[KnowledgeRecord]:
        records: list[KnowledgeRecord] = []
        for document in documents:
            records.append(
                KnowledgeRecord(
                    record_id=f"raw_{document.get('source_id')}",
                    record_type="raw_document",
                    trading_day=trading_day,
                    source=str(document.get("source_name") or ""),
                    source_rank=str(document.get("source_rank") or "internal"),
                    title=str(document.get("title") or ""),
                    summary=str(document.get("raw_text") or document.get("title") or ""),
                    content=str(document.get("raw_text") or document.get("title") or ""),
                    url=document.get("url"),
                    symbols=list(document.get("symbols") or []),
                    themes=[item for item in document.get("tags", []) if isinstance(item, str)],
                    evidence_ids=[str(document.get("source_id"))],
                    confidence=0.5,
                    metadata={"external_id": document.get("external_id")},
                )
            )
        return records

    def _events(self, trading_day: date, events: list[dict[str, Any]]) -> list[KnowledgeRecord]:
        records: list[KnowledgeRecord] = []
        for event in events:
            records.append(
                KnowledgeRecord(
                    record_id=f"event_{event.get('event_id')}",
                    record_type="event",
                    trading_day=trading_day,
                    source=str(event.get("source_rank") or ""),
                    source_rank=str(event.get("source_rank") or "internal"),
                    title=str(event.get("title") or ""),
                    summary=str(event.get("summary") or ""),
                    content=f"{event.get('title') or ''} {event.get('summary') or ''}",
                    symbols=list(event.get("symbols") or []),
                    themes=list(event.get("related_themes") or []),
                    event_ids=[str(event.get("event_id"))],
                    evidence_ids=list(event.get("source_ids") or []),
                    confidence=float(event.get("confidence") or 0.5),
                    importance=str(event.get("importance") or "C"),
                    metadata={"bias": event.get("bias"), "event_type": event.get("event_type")},
                )
            )
        return records

    def _clusters(self, trading_day: date, clusters: list[dict[str, Any]]) -> list[KnowledgeRecord]:
        records: list[KnowledgeRecord] = []
        for cluster in clusters:
            title = str(cluster.get("title") or "")
            theme = title.split(":", 1)[0] if ":" in title else ""
            records.append(
                KnowledgeRecord(
                    record_id=f"cluster_{cluster.get('cluster_id')}",
                    record_type="event_cluster",
                    trading_day=trading_day,
                    source=str(cluster.get("primary_source_rank") or ""),
                    source_rank=str(cluster.get("primary_source_rank") or "internal"),
                    title=title,
                    summary=str(cluster.get("summary") or ""),
                    content=f"{title} {cluster.get('summary') or ''}",
                    symbols=list(cluster.get("symbols") or []),
                    themes=[theme] if theme and len(theme) <= 12 else [],
                    event_ids=[str(cluster.get("primary_event_id")), *[str(item) for item in cluster.get("supporting_event_ids", [])]],
                    cluster_ids=[str(cluster.get("cluster_id"))],
                    evidence_ids=[str(cluster.get("primary_event_id"))],
                    confidence=float(cluster.get("confidence") or 0.5),
                    importance=str(cluster.get("importance") or "C"),
                    metadata={"bias": cluster.get("bias"), "event_type": cluster.get("event_type")},
                )
            )
        return records

    def _morning_brief(self, trading_day: date, brief: dict[str, Any]) -> list[KnowledgeRecord]:
        records: list[KnowledgeRecord] = []
        for theme in brief.get("top_themes", []):
            records.append(
                KnowledgeRecord(
                    record_id=f"theme_{theme.get('theme_id')}",
                    record_type="theme",
                    trading_day=trading_day,
                    source="premarket_agent",
                    source_rank="internal",
                    title=str(theme.get("theme_name") or ""),
                    summary=f"{theme.get('theme_name')} 盘前主题候选",
                    content=f"{theme.get('theme_name')} {theme.get('catalyst_type')}",
                    symbols=list(theme.get("related_symbols") or []),
                    themes=[str(theme.get("theme_name"))],
                    event_ids=list(theme.get("evidence_event_ids") or []),
                    cluster_ids=list(theme.get("evidence_cluster_ids") or []),
                    evidence_ids=list(theme.get("evidence_event_ids") or []),
                    confidence=float(theme.get("confidence") or 0.5),
                    importance="B",
                    metadata={"rank": theme.get("rank"), "score": theme.get("score")},
                )
            )
        return records

    def _instruction(self, trading_day: date, instruction: dict[str, Any]) -> list[KnowledgeRecord]:
        records: list[KnowledgeRecord] = []
        for idx, item in enumerate(instruction.get("items", [])):
            target = str(item.get("target") or "")
            records.append(
                KnowledgeRecord(
                    record_id=f"decision_{instruction.get('instruction_id')}_{idx}",
                    record_type="decision",
                    trading_day=trading_day,
                    source="premarket_agent",
                    source_rank="internal",
                    title=f"{item.get('instruction_type')} {target}",
                    summary=str(item.get("reason") or ""),
                    content=f"{item.get('instruction_type')} {target} {item.get('reason') or ''}",
                    themes=[target.removeprefix("板块:")] if target.startswith("板块:") else [],
                    event_ids=list(item.get("evidence_event_ids") or []),
                    evidence_ids=[*list(item.get("evidence_event_ids") or []), *list(item.get("source_ids") or [])],
                    confidence=0.7,
                    importance="B",
                    metadata={"requires_manual_review": item.get("requires_manual_review")},
                )
            )
        return records
