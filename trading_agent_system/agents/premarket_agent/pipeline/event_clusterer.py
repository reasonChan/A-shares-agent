from __future__ import annotations

from collections import defaultdict

from trading_agent_system.schemas import make_id

from ..schemas import EventCluster, PreMarketEvent, SourceRank


SOURCE_PRIORITY = {
    SourceRank.OFFICIAL.value: 6,
    SourceRank.AUTHORIZED_NEWS.value: 5,
    SourceRank.MARKET_DATA.value: 4,
    SourceRank.OVERSEAS.value: 3,
    SourceRank.INTERNAL.value: 2,
    SourceRank.SOCIAL.value: 1,
}


class EventClusterer:
    def cluster(self, events: list[PreMarketEvent]) -> list[EventCluster]:
        grouped: dict[str, list[PreMarketEvent]] = defaultdict(list)
        for event in events:
            grouped[self._cluster_key(event)].append(event)
        return [self._build_cluster(related) for related in grouped.values()]

    def _cluster_key(self, event: PreMarketEvent) -> str:
        if event.symbols:
            return f"{event.event_type}:symbol:{event.symbols[0]}"
        if event.related_themes:
            return f"{event.event_type}:theme:{event.related_themes[0]}"
        return f"{event.event_type}:title:{event.title[:24]}"

    def _build_cluster(self, related: list[PreMarketEvent]) -> EventCluster:
        primary = sorted(
            related,
            key=lambda event: (
                SOURCE_PRIORITY.get(str(event.source_rank), 0),
                event.importance,
                event.confidence,
            ),
            reverse=True,
        )[0]
        confidence = min(0.95, max(event.confidence for event in related) + min(0.12, 0.03 * (len(related) - 1)))
        themes = sorted({theme for event in related for theme in event.related_themes})
        symbols = sorted({symbol for event in related for symbol in event.symbols})
        title_prefix = themes[0] if themes else symbols[0] if symbols else ""
        title = f"{title_prefix}: {primary.title}" if title_prefix and not primary.title.startswith(f"{title_prefix}:") else primary.title
        return EventCluster(
            cluster_id=make_id("pmclu"),
            primary_event_id=primary.event_id,
            supporting_event_ids=[event.event_id for event in related if event.event_id != primary.event_id],
            first_seen_at=min(event.first_seen_at for event in related),
            last_updated_at=max(event.last_updated_at for event in related),
            symbols=symbols,
            companies=sorted({company for event in related for company in event.companies}),
            event_type=primary.event_type,
            title=title,
            summary=primary.summary,
            primary_source_rank=primary.source_rank,
            evidence_count=len(related),
            importance=primary.importance,
            bias=primary.bias,
            confidence=confidence,
            actionability=primary.actionability,
            risk_flags=sorted({flag for event in related for flag in event.risk_flags}),
        )
