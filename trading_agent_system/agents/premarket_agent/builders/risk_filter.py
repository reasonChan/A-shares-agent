from __future__ import annotations

from ..schemas import AvoidItem, Bias, EventCluster


HIGH_RISK_TYPES = {
    "regulatory_penalty",
    "delisting_risk",
    "suspension_resumption",
    "debt_risk",
    "regulatory_inquiry",
    "risk_warning",
}


class RiskFilter:
    def build_avoid_candidates(self, clusters: list[EventCluster]) -> list[AvoidItem]:
        items: list[AvoidItem] = []
        for cluster in clusters:
            if not self._is_risk(cluster):
                continue
            targets = cluster.symbols or [cluster.title.split(":")[0] if ":" in cluster.title else "ALL"]
            for target in targets:
                items.append(
                    AvoidItem(
                        symbol=target,
                        reason=cluster.summary or cluster.title,
                        risk_level=self._risk_level(cluster),
                        related_event_ids=[cluster.primary_event_id, *cluster.supporting_event_ids],
                        related_cluster_ids=[cluster.cluster_id],
                        restriction=self._restriction(cluster),
                    )
                )
        return items[:20]

    def _is_risk(self, cluster: EventCluster) -> bool:
        return bool(cluster.risk_flags) or cluster.bias == Bias.BEARISH.value or cluster.event_type in HIGH_RISK_TYPES

    def _risk_level(self, cluster: EventCluster) -> str:
        if cluster.event_type in {"delisting_risk", "debt_risk", "regulatory_penalty"}:
            return "critical"
        if cluster.risk_flags or cluster.importance in {"S", "A"}:
            return "high"
        return "medium"

    def _restriction(self, cluster: EventCluster) -> str:
        if cluster.event_type in {"delisting_risk", "debt_risk"}:
            return "reduce_only"
        if "传闻" in cluster.risk_flags or "unverified" in cluster.risk_flags:
            return "manual_approval_required"
        return "no_new_entry"
