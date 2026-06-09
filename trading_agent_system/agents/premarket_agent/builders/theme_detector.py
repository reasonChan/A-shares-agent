from __future__ import annotations

from collections import defaultdict

from trading_agent_system.schemas import make_id

from ..schemas import Bias, EventCluster, ThemeCandidate


GENERIC_EVENT_TYPES = {
    "eastmoney_news",
    "sina_roll",
    "sentiment",
    "news",
    "official_policy",
}


class ThemeDetector:
    def detect(self, clusters: list[EventCluster]) -> list[ThemeCandidate]:
        buckets: dict[str, list[EventCluster]] = defaultdict(list)
        for cluster in clusters:
            if cluster.bias == Bias.BEARISH.value:
                continue
            for theme in self._themes_for_cluster(cluster):
                buckets[theme].append(cluster)
        candidates = []
        for theme, related in buckets.items():
            score = min(1.0, sum(cluster.confidence for cluster in related) / max(1, len(related)) + 0.08 * len(related))
            candidates.append(
                ThemeCandidate(
                    theme_id=make_id("pmthm"),
                    theme_name=theme,
                    rank=0,
                    score=score,
                    evidence_event_ids=[cluster.primary_event_id for cluster in related],
                    evidence_cluster_ids=[cluster.cluster_id for cluster in related],
                    related_symbols=sorted({symbol for cluster in related for symbol in cluster.symbols}),
                    catalyst_type=self._catalyst_type(related),
                    confidence=min(0.95, score),
                    risk_flags=sorted({flag for cluster in related for flag in cluster.risk_flags}),
                )
            )
        ranked = sorted(candidates, key=lambda item: item.score, reverse=True)
        return [item.model_copy(update={"rank": idx + 1}) for idx, item in enumerate(ranked[:12])]

    def _themes_for_cluster(self, cluster: EventCluster) -> list[str]:
        if cluster.title.startswith("主题:"):
            return [cluster.title.removeprefix("主题:")]
        parts = cluster.title.split(":")
        if len(parts) > 1 and 1 < len(parts[0]) <= 8 and parts[0] not in GENERIC_EVENT_TYPES:
            return [parts[0]]
        if cluster.symbols:
            return [f"个股:{cluster.symbols[0]}"]
        if cluster.event_type in GENERIC_EVENT_TYPES:
            return []
        return [cluster.event_type]

    def _catalyst_type(self, clusters: list[EventCluster]) -> str:
        event_types = {cluster.event_type for cluster in clusters}
        if any("policy" in item or "official" in item for item in event_types):
            return "policy"
        if any("earnings" in item for item in event_types):
            return "earnings"
        if any("announcement" in item for item in event_types):
            return "announcement"
        if len(event_types) > 1:
            return "mixed"
        return "news"
