from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .base import BaseStrategy
from .builtin_strategies import BreakoutV1


@dataclass
class StrategyConfig:
    strategy_id: str
    version: str
    enabled: bool = True
    mode: str = "paper"
    allowed_symbols: list[str] = field(default_factory=lambda: ["*"])
    allowed_sides: list[str] = field(default_factory=lambda: ["buy", "sell"])
    max_confidence_cap: float = 1.0
    requires_intel_confirmation: bool = False
    blocked_risk_flags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StrategyConfig":
        return cls(
            strategy_id=data["strategy_id"],
            version=str(data.get("version", "1.0.0")),
            enabled=bool(data.get("enabled", True)),
            mode=str(data.get("mode", "paper")),
            allowed_symbols=list(data.get("allowed_symbols", ["*"])),
            allowed_sides=list(data.get("allowed_sides", ["buy", "sell"])),
            max_confidence_cap=float(data.get("max_confidence_cap", 1.0)),
            requires_intel_confirmation=bool(data.get("requires_intel_confirmation", False)),
            blocked_risk_flags=list(data.get("blocked_risk_flags", [])),
        )


class StrategyRegistry:
    def __init__(self, strategy_configs: list[StrategyConfig], strategies: list[BaseStrategy] | None = None) -> None:
        self.strategy_configs = {config.strategy_id: config for config in strategy_configs}
        self.strategies = {strategy.strategy_id: strategy for strategy in (strategies or [BreakoutV1()])}

    @classmethod
    def from_config(cls, data: dict[str, Any]) -> "StrategyRegistry":
        configs = [StrategyConfig.from_dict(item) for item in data.get("strategies", [])]
        return cls(configs)

    def enabled_for_symbol(self, symbol: str, side: str | None = None) -> list[tuple[BaseStrategy, StrategyConfig]]:
        enabled: list[tuple[BaseStrategy, StrategyConfig]] = []
        for strategy_id, config in self.strategy_configs.items():
            strategy = self.strategies.get(strategy_id)
            if not strategy or not config.enabled:
                continue
            if "*" not in config.allowed_symbols and symbol not in config.allowed_symbols:
                continue
            if side and side not in config.allowed_sides:
                continue
            enabled.append((strategy, config))
        return enabled
