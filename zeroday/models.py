"""Domain models. No rendering or exchange integration lives here."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Action(str, Enum):
    BUY = "COMPRAR"
    SELL = "VENDER"
    HOLD = "ESPERAR"


class RobotStatus(str, Enum):
    ACTIVE = "ativo"
    DEAD = "desativado"


@dataclass
class MarketSnapshot:
    symbol: str
    price: float
    ema_fast: float
    ema_slow: float
    rsi: float
    momentum: float
    volatility: float

    @property
    def trend(self) -> str:
        if self.ema_fast > self.ema_slow and self.momentum > 0:
            return "alta"
        if self.ema_fast < self.ema_slow and self.momentum < 0:
            return "baixa"
        return "lateral"


@dataclass
class Robot:
    robot_id: int
    symbol: str
    cash: float
    birth_capital: float
    risk_name: str = "moderado"
    generation: int = 0
    quantity: float = 0.0
    average_entry: float = 0.0
    status: RobotStatus = RobotStatus.ACTIVE
    floor: int = 6
    cooldown: int = 0
    peak_equity: float = 0.0
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    created_at_tick: int = 0
    parent_id: Optional[int] = None
    death_reason: str = ""

    def equity(self, market_price: float) -> float:
        return max(0.0, self.cash + self.quantity * market_price)

    def unrealized_pnl(self, market_price: float) -> float:
        if self.quantity <= 0 or self.average_entry <= 0:
            return 0.0
        return (market_price - self.average_entry) * self.quantity

    def return_pct(self, market_price: float) -> float:
        if self.birth_capital <= 0:
            return 0.0
        return (self.equity(market_price) / self.birth_capital - 1.0) * 100.0


@dataclass
class FeedEvent:
    tick: int
    message: str
    kind: str = "info"


@dataclass
class BuildingState:
    branch_count: int = 1
    expansion_unlocked: bool = False
    selected_floor: int | None = None
    floor_capacity: int = 18
