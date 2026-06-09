from __future__ import annotations

from datetime import datetime, timezone

from trading_agent_system.core.audit import AuditLedger
from trading_agent_system.core.event_bus import MemoryEventBus
from trading_agent_system.schemas import IntelBrief


class IntelAgent:
    def __init__(self, event_bus: MemoryEventBus, audit: AuditLedger) -> None:
        self.event_bus = event_bus
        self.audit = audit

    def publish_brief(
        self,
        symbols: list[str],
        event_type: str,
        importance: str,
        bias: str,
        confidence: float,
        actionability: str,
        summary: str,
        evidence: list[dict],
        risk_flags: list[str] | None = None,
    ) -> IntelBrief:
        brief = IntelBrief(
            first_seen_at=datetime.now(timezone.utc),
            symbols=symbols,
            event_type=event_type,
            importance=importance,
            bias=bias,
            confidence=confidence,
            actionability=actionability,
            summary=summary,
            evidence=evidence,
            risk_flags=risk_flags or [],
        )
        self.event_bus.publish("intel.briefs", brief)
        self.audit.write("intel_brief_created", brief)
        return brief
