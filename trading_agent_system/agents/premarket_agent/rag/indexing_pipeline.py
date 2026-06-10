from __future__ import annotations

from datetime import date, datetime, timezone
from hashlib import sha256
from typing import Any

from trading_agent_system.agents.premarket_agent.rag.schemas import RAGDocument


SOURCE_RANK_VALUE = {
    "official": 1.0,
    "official_announcement": 1.0,
    "official_policy": 1.0,
    "exchange_notice": 0.95,
    "authorized_news": 0.8,
    "market_data": 0.7,
    "overseas": 0.55,
    "overseas_market": 0.55,
    "internal": 0.45,
    "internal_review": 0.45,
    "social": 0.2,
    "unknown": 0.3,
}


class PreMarketRAGIndexingPipeline:
    def from_payloads(
        self,
        *,
        trading_day: date,
        premarket_window_id: str,
        raw_documents: list[dict[str, Any]],
        events: list[dict[str, Any]],
        clusters: list[dict[str, Any]],
    ) -> list[RAGDocument]:
        documents: list[RAGDocument] = []
        documents.extend(self._clusters(trading_day, premarket_window_id, clusters))
        documents.extend(self._events(trading_day, premarket_window_id, events))
        documents.extend(self._raw_documents(trading_day, premarket_window_id, raw_documents))
        return documents

    def _clusters(
        self,
        trading_day: date,
        premarket_window_id: str,
        clusters: list[dict[str, Any]],
    ) -> list[RAGDocument]:
        documents = []
        for cluster in clusters:
            cluster_id = str(cluster.get("cluster_id") or "")
            if not cluster_id:
                continue
            title = str(cluster.get("title") or "")
            summary = str(cluster.get("summary") or "")
            doc_id = f"cluster_{cluster_id}"
            risk_flags = _strings(cluster.get("risk_flags"))
            source_rank_name = str(cluster.get("primary_source_rank") or "unknown")
            documents.append(
                RAGDocument(
                    doc_id=doc_id,
                    event_id=str(cluster.get("primary_event_id") or "") or None,
                    event_cluster_id=cluster_id,
                    title=title,
                    content=_event_card(title, summary, cluster),
                    content_type="event_card",
                    source=source_rank_name,
                    source_type=_source_type(source_rank_name),
                    source_rank=_source_rank(source_rank_name),
                    published_at=_datetime_or_none(cluster.get("first_seen_at") or cluster.get("published_at")),
                    fetched_at=_datetime_or_none(cluster.get("last_updated_at")) or datetime.now(timezone.utc),
                    trading_day=trading_day,
                    premarket_window_id=premarket_window_id,
                    symbols=_strings(cluster.get("symbols")),
                    companies=_strings(cluster.get("companies")),
                    event_type=str(cluster.get("event_type") or "") or None,
                    themes=_themes_from(title, cluster),
                    importance=_importance(cluster.get("importance")),
                    bias=_bias(cluster.get("bias")),
                    confidence=float(cluster.get("confidence") or 0.5),
                    actionability=_actionability(cluster.get("actionability"), risk_flags),
                    risk_flags=risk_flags,
                    is_post_close=bool(cluster.get("is_post_close", True)),
                    is_verified=_source_rank(source_rank_name) >= 0.75 and "unverified" not in risk_flags and "rumor" not in risk_flags,
                    metadata={
                        "supporting_event_ids": _strings(cluster.get("supporting_event_ids")),
                        "primary_event_id": cluster.get("primary_event_id"),
                    },
                    content_hash=_hash(doc_id, title, summary),
                )
            )
        return documents

    def _events(
        self,
        trading_day: date,
        premarket_window_id: str,
        events: list[dict[str, Any]],
    ) -> list[RAGDocument]:
        documents = []
        for event in events:
            event_id = str(event.get("event_id") or "")
            if not event_id:
                continue
            title = str(event.get("title") or "")
            summary = str(event.get("summary") or "")
            doc_id = f"event_{event_id}"
            risk_flags = _strings(event.get("risk_flags"))
            source_rank_name = str(event.get("source_rank") or "unknown")
            documents.append(
                RAGDocument(
                    doc_id=doc_id,
                    raw_document_id=_first_or_none(event.get("source_ids")),
                    event_id=event_id,
                    title=title,
                    content=f"{title} {summary}".strip(),
                    content_type="summary",
                    source=source_rank_name,
                    source_type=_source_type(source_rank_name),
                    source_rank=_source_rank(source_rank_name),
                    published_at=_datetime_or_none(event.get("published_at")),
                    fetched_at=_datetime_or_none(event.get("first_seen_at")) or datetime.now(timezone.utc),
                    trading_day=trading_day,
                    premarket_window_id=premarket_window_id,
                    symbols=_strings(event.get("symbols")),
                    companies=_strings(event.get("companies")),
                    event_type=str(event.get("event_type") or "") or None,
                    themes=_strings(event.get("related_themes")),
                    importance=_importance(event.get("importance")),
                    bias=_bias(event.get("bias")),
                    confidence=float(event.get("confidence") or 0.5),
                    actionability=_actionability(event.get("actionability"), risk_flags),
                    risk_flags=risk_flags,
                    is_post_close=bool(event.get("is_post_close", True)),
                    is_holding_related=bool(event.get("is_holding_related", False)),
                    is_watchlist_related=bool(event.get("is_watchlist_related", False)),
                    is_verified=_source_rank(source_rank_name) >= 0.75 and "unverified" not in risk_flags and "rumor" not in risk_flags,
                    metadata={"source_ids": _strings(event.get("source_ids"))},
                    content_hash=_hash(doc_id, title, summary),
                )
            )
        return documents

    def _raw_documents(
        self,
        trading_day: date,
        premarket_window_id: str,
        raw_documents: list[dict[str, Any]],
    ) -> list[RAGDocument]:
        documents = []
        for raw in raw_documents:
            source_id = str(raw.get("source_id") or "")
            if not source_id:
                continue
            title = str(raw.get("title") or "")
            content = str(raw.get("raw_text") or title)
            source_rank_name = str(raw.get("source_rank") or "unknown")
            documents.append(
                RAGDocument(
                    doc_id=f"raw_{source_id}",
                    raw_document_id=source_id,
                    title=title,
                    content=content,
                    content_type="body_chunk",
                    source=str(raw.get("source_name") or source_rank_name),
                    source_type=_source_type(source_rank_name),
                    source_rank=_source_rank(source_rank_name),
                    published_at=_datetime_or_none(raw.get("published_at")),
                    fetched_at=_datetime_or_none(raw.get("fetched_at")) or datetime.now(timezone.utc),
                    trading_day=trading_day,
                    premarket_window_id=premarket_window_id,
                    symbols=_strings(raw.get("symbols")),
                    themes=_strings(raw.get("tags")),
                    confidence=0.5,
                    actionability=_actionability(None, _strings(raw.get("risk_flags"))),
                    risk_flags=_strings(raw.get("risk_flags")),
                    metadata={"external_id": raw.get("external_id"), "format": raw.get("format")},
                    content_hash=str(raw.get("content_hash") or _hash(source_id, title, content)),
                )
            )
        return documents


def _event_card(title: str, summary: str, payload: dict[str, Any]) -> str:
    facts = [
        f"标题: {title}",
        f"摘要: {summary}",
        f"事件类型: {payload.get('event_type') or 'unknown'}",
        f"重要性: {payload.get('importance') or 'C'}",
    ]
    symbols = ", ".join(_strings(payload.get("symbols")))
    if symbols:
        facts.append(f"标的: {symbols}")
    return "\n".join(facts)


def _themes_from(title: str, payload: dict[str, Any]) -> list[str]:
    explicit = _strings(payload.get("themes") or payload.get("related_themes"))
    if explicit:
        return explicit
    if ":" in title:
        theme = title.split(":", 1)[0].strip()
        if 0 < len(theme) <= 12:
            return [theme]
    return []


def _source_type(value: str) -> str:
    mapping = {
        "official": "official_announcement",
        "authorized_news": "authorized_news",
        "market_data": "market_data",
        "overseas": "overseas_market",
        "internal": "internal_review",
        "social": "social",
    }
    return mapping.get(value, value if value in SOURCE_RANK_VALUE else "unknown")


def _source_rank(value: object) -> float:
    if isinstance(value, (int, float)):
        return max(0.0, min(1.0, float(value)))
    return SOURCE_RANK_VALUE.get(str(value or "unknown"), 0.3)


def _actionability(value: object, risk_flags: list[str]) -> str | None:
    if any(flag in {"unverified", "rumor"} for flag in risk_flags):
        return "watch_only"
    item = str(value or "")
    return item if item in {"watch", "candidate", "block", "watch_only"} else None


def _importance(value: object) -> str | None:
    item = str(value or "")
    return item if item in {"S", "A", "B", "C"} else None


def _bias(value: object) -> str | None:
    item = str(value or "")
    return item if item in {"bullish", "bearish", "neutral", "mixed", "unclear"} else None


def _datetime_or_none(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return None


def _strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None and str(item)]


def _first_or_none(value: object) -> str | None:
    items = _strings(value)
    return items[0] if items else None


def _hash(*values: object) -> str:
    text = "|".join(str(value or "") for value in values)
    return sha256(text.encode("utf-8")).hexdigest()
