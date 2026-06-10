from __future__ import annotations

from statistics import mean

from trading_agent_system.agents.premarket_agent.rag.schemas import EvidenceItem, EvidencePack, RAGEvaluationMetrics


class RAGEvaluator:
    def __init__(self, low_confidence_threshold: float = 0.5) -> None:
        self.low_confidence_threshold = low_confidence_threshold

    def evaluate_pack(self, pack: EvidencePack) -> RAGEvaluationMetrics:
        item_count = len(pack.items)
        total_candidates = item_count + pack.dropped_duplicates + pack.dropped_low_confidence
        return RAGEvaluationMetrics(
            trading_day=pack.trading_day,
            section=pack.section,
            duplicate_ratio=_safe_ratio(pack.dropped_duplicates, total_candidates),
            low_confidence_leakage_ratio=_safe_ratio(
                sum(1 for item in pack.items if item.confidence < self.low_confidence_threshold),
                item_count,
            ),
            evidence_coverage_ratio=_safe_ratio(sum(1 for item in pack.items if _has_traceable_id(item)), item_count),
            citation_coverage_ratio=_safe_ratio(sum(1 for item in pack.items if item.citation_label), item_count),
            avg_source_rank=mean([item.source_rank for item in pack.items]) if pack.items else 0,
            token_count=pack.token_estimate,
            dropped_duplicates=pack.dropped_duplicates,
            dropped_low_confidence=pack.dropped_low_confidence,
        )

    def evaluate_packs(self, packs: list[EvidencePack]) -> list[RAGEvaluationMetrics]:
        return [self.evaluate_pack(pack) for pack in packs]

    def summarize(self, metrics: list[RAGEvaluationMetrics]) -> dict[str, float | int]:
        if not metrics:
            return {
                "pack_count": 0,
                "avg_duplicate_ratio": 0.0,
                "avg_evidence_coverage_ratio": 0.0,
                "avg_citation_coverage_ratio": 0.0,
                "avg_source_rank": 0.0,
                "token_count": 0,
            }
        return {
            "pack_count": len(metrics),
            "avg_duplicate_ratio": mean(item.duplicate_ratio for item in metrics),
            "avg_evidence_coverage_ratio": mean(item.evidence_coverage_ratio for item in metrics),
            "avg_citation_coverage_ratio": mean(item.citation_coverage_ratio for item in metrics),
            "avg_source_rank": mean(item.avg_source_rank for item in metrics),
            "token_count": sum(item.token_count for item in metrics),
        }


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def _has_traceable_id(item: EvidenceItem) -> bool:
    return bool(item.evidence_id or item.event_id or item.event_cluster_id or item.source_id)
