from __future__ import annotations

from trading_agent_system.schemas import make_id

from ..schemas import AvoidItem, PreMarketWindow, ScenarioPlan, ThemeCandidate


class ScenarioBuilder:
    def build(
        self,
        window: PreMarketWindow,
        themes: list[ThemeCandidate],
        avoid_items: list[AvoidItem],
    ) -> list[ScenarioPlan]:
        scenarios: list[ScenarioPlan] = []
        for theme in themes[:5]:
            scenarios.append(
                ScenarioPlan(
                    scenario_id=make_id("pmscn"),
                    name=f"{theme.theme_name} 竞价验证",
                    condition="09:20-09:25 主题内代表标的竞价强于大盘且成交额放大",
                    watch_symbols=theme.related_symbols[:8],
                    watch_themes=[theme.theme_name],
                    valid_until=window.continuous_open,
                    action_for_intraday_agent="increase_attention",
                    evidence_event_ids=theme.evidence_event_ids,
                    risk_notes=theme.risk_flags,
                )
            )
        if avoid_items:
            scenarios.append(
                ScenarioPlan(
                    scenario_id=make_id("pmscn"),
                    name="风险约束优先",
                    condition="禁入/降权清单存在时，相关标的开盘前需要人工确认",
                    watch_symbols=[item.symbol for item in avoid_items[:8] if item.symbol != "ALL"],
                    valid_until=window.continuous_open,
                    action_for_intraday_agent="require_confirmation",
                    evidence_event_ids=[event_id for item in avoid_items for event_id in item.related_event_ids][:10],
                    risk_notes=[item.reason for item in avoid_items[:5]],
                )
            )
        return scenarios[:8]
