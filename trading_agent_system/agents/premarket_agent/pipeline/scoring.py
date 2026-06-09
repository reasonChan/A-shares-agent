from __future__ import annotations

from trading_agent_system.schemas import PremarketNewsItem

from ..schemas import Actionability, Bias, Importance, SourceRank


SOURCE_CONFIDENCE = {
    SourceRank.OFFICIAL.value: 0.95,
    SourceRank.AUTHORIZED_NEWS.value: 0.75,
    SourceRank.MARKET_DATA.value: 0.65,
    SourceRank.OVERSEAS.value: 0.60,
    SourceRank.SOCIAL.value: 0.15,
    SourceRank.INTERNAL.value: 0.80,
}

EVENT_IMPORTANCE_SCORE = {
    "delisting_risk": 1.00,
    "regulatory_penalty": 0.95,
    "suspension_resumption": 0.95,
    "debt_risk": 0.90,
    "earnings_revision": 0.88,
    "earnings_preannouncement": 0.85,
    "ma_restructuring": 0.85,
    "control_change": 0.82,
    "shareholder_reduction": 0.78,
    "major_contract": 0.72,
    "buyback": 0.70,
    "policy_release": 0.85,
    "official_policy": 0.85,
    "industry_catalyst": 0.58,
    "eastmoney_news": 0.46,
    "sina_roll": 0.42,
    "rumor": 0.10,
}


class EventScorer:
    def source_rank(self, item: PremarketNewsItem) -> SourceRank:
        if item.source_tier == "official":
            return SourceRank.OFFICIAL
        if item.source_tier == "professional":
            return SourceRank.AUTHORIZED_NEWS
        if item.source_tier == "sentiment":
            return SourceRank.SOCIAL
        return SourceRank.INTERNAL

    def importance(self, item: PremarketNewsItem, positive_count: int, negative_count: int) -> Importance:
        score = EVENT_IMPORTANCE_SCORE.get(item.category, 0.35)
        if item.source_tier == "official":
            score += 0.12
        if item.symbols:
            score += 0.08
        if positive_count or negative_count:
            score += 0.05
        if score >= 0.90:
            return Importance.S
        if score >= 0.72:
            return Importance.A
        if score >= 0.45:
            return Importance.B
        return Importance.C

    def confidence(self, item: PremarketNewsItem, source_rank: SourceRank | str, evidence_count: int = 1) -> float:
        rank_value = source_rank.value if isinstance(source_rank, SourceRank) else str(source_rank)
        base = max(item.credibility, SOURCE_CONFIDENCE.get(rank_value, 0.5))
        if item.risk_flags:
            base -= 0.22
        return min(0.95, max(0, base + min(0.12, 0.03 * max(0, evidence_count - 1))))

    def actionability(self, item: PremarketNewsItem, bias: Bias) -> Actionability:
        if item.risk_flags or bias == Bias.BEARISH:
            return Actionability.BLOCK
        if item.source_tier == "sentiment":
            return Actionability.WATCH_ONLY
        if item.symbols or item.sectors:
            return Actionability.WATCH
        return Actionability.WATCH_ONLY
