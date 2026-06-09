from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from trading_agent_system.core.audit import AuditLedger
from trading_agent_system.core.event_bus import MemoryEventBus
from trading_agent_system.schemas import (
    AccountSnapshot,
    BrokerOrder,
    Fill,
    MarketBar,
    OrderInstruction,
    PositionSnapshot,
    utc_now,
)


@dataclass
class PaperBrokerState:
    cash: float
    positions: dict[str, int] = field(default_factory=dict)
    avg_cost: dict[str, float] = field(default_factory=dict)
    realized_pnl: float = 0
    open_orders: dict[str, BrokerOrder] = field(default_factory=dict)


class PaperBroker:
    def __init__(
        self,
        event_bus: MemoryEventBus,
        audit: AuditLedger,
        initial_cash: float = 1_000_000,
        commission_bps: float = 2,
        slippage_bps: float = 3,
        allow_partial_fill: bool = False,
    ) -> None:
        self.event_bus = event_bus
        self.audit = audit
        self.state = PaperBrokerState(cash=initial_cash)
        self.commission_bps = commission_bps
        self.slippage_bps = slippage_bps
        self.allow_partial_fill = allow_partial_fill

    def on_order_instruction(self, instruction: OrderInstruction) -> BrokerOrder:
        order = BrokerOrder(
            order_instruction_id=instruction.order_instruction_id,
            decision_id=instruction.decision_id,
            intent_id=instruction.intent_id,
            symbol=instruction.symbol,
            side=instruction.side,
            quantity=instruction.quantity,
            order_type=instruction.order_type,
            limit_price=instruction.limit_price,
            status="submitted",
            submitted_at=utc_now(),
            expires_at=utc_now() + timedelta(seconds=instruction.ttl_seconds),
        )
        self.state.open_orders[order.order_id] = order
        self.event_bus.publish("orders.submitted", order)
        self.audit.write("order_submitted", order)
        return order

    def on_market_bar(self, bar: MarketBar) -> list[Fill]:
        fills: list[Fill] = []
        for order_id, order in list(self.state.open_orders.items()):
            if order.symbol != bar.symbol:
                continue
            if order.expires_at and bar.ts > order.expires_at:
                expired = order.model_copy(update={"status": "expired"})
                self.state.open_orders.pop(order_id, None)
                self.event_bus.publish("orders.cancelled", expired)
                self.audit.write("order_expired", expired)
                continue
            fill_price = self._fill_price(order, bar)
            if fill_price is None:
                continue
            fill = self._fill(order, fill_price)
            fills.append(fill)
            filled = order.model_copy(update={"status": "filled", "filled_quantity": order.quantity})
            self.state.open_orders.pop(order_id, None)
            self.event_bus.publish("orders.filled", fill)
            self.audit.write("order_filled", fill)
            self.audit.write("order_status_filled", filled)
        if fills:
            self.publish_snapshots(last_prices={bar.symbol: bar.close})
        return fills

    def publish_snapshots(self, last_prices: dict[str, float] | None = None) -> tuple[PositionSnapshot, AccountSnapshot]:
        last_prices = last_prices or {}
        position_snapshot = PositionSnapshot(
            positions=dict(self.state.positions),
            avg_cost=dict(self.state.avg_cost),
        )
        gross_exposure = sum(abs(qty) * last_prices.get(symbol, self.state.avg_cost.get(symbol, 0)) for symbol, qty in self.state.positions.items())
        nav = self.state.cash + sum(qty * last_prices.get(symbol, self.state.avg_cost.get(symbol, 0)) for symbol, qty in self.state.positions.items())
        account_snapshot = AccountSnapshot(
            cash=self.state.cash,
            nav=nav,
            gross_exposure=gross_exposure,
            realized_pnl=self.state.realized_pnl,
            unrealized_pnl=nav - self.state.cash - self.state.realized_pnl,
        )
        self.event_bus.publish("positions.snapshots", position_snapshot)
        self.event_bus.publish("account.snapshots", account_snapshot)
        self.audit.write("position_snapshot", position_snapshot)
        self.audit.write("account_snapshot", account_snapshot)
        return position_snapshot, account_snapshot

    def _fill_price(self, order: BrokerOrder, bar: MarketBar) -> float | None:
        if order.order_type == "marketable_limit":
            base = bar.close
        elif order.side == "buy" and order.limit_price is not None and bar.low <= order.limit_price:
            base = order.limit_price
        elif order.side == "sell" and order.limit_price is not None and bar.high >= order.limit_price:
            base = order.limit_price
        else:
            return None
        if order.side == "buy":
            return base * (1 + self.slippage_bps / 10000)
        return base * (1 - self.slippage_bps / 10000)

    def _fill(self, order: BrokerOrder, price: float) -> Fill:
        commission = price * order.quantity * self.commission_bps / 10000
        if order.side == "buy":
            total_cost = price * order.quantity + commission
            self.state.cash -= total_cost
            previous_qty = self.state.positions.get(order.symbol, 0)
            previous_cost = self.state.avg_cost.get(order.symbol, 0)
            next_qty = previous_qty + order.quantity
            if next_qty > 0:
                self.state.avg_cost[order.symbol] = (
                    previous_qty * previous_cost + order.quantity * price
                ) / next_qty
            self.state.positions[order.symbol] = next_qty
        else:
            current_qty = self.state.positions.get(order.symbol, 0)
            sell_qty = min(order.quantity, current_qty)
            avg_cost = self.state.avg_cost.get(order.symbol, price)
            proceeds = price * sell_qty - commission
            self.state.cash += proceeds
            self.state.positions[order.symbol] = current_qty - sell_qty
            self.state.realized_pnl += (price - avg_cost) * sell_qty - commission
            if self.state.positions[order.symbol] <= 0:
                self.state.positions.pop(order.symbol, None)
                self.state.avg_cost.pop(order.symbol, None)
        return Fill(
            order_id=order.order_id,
            order_instruction_id=order.order_instruction_id,
            decision_id=order.decision_id,
            intent_id=order.intent_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=price,
            commission=commission,
            slippage_bps=self.slippage_bps,
        )
