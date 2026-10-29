"""Deterministic pre-trade risk checks; baseline only, not a guarantee."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class OrderProposal:
    symbol: str
    side: str
    amount_base: float
    estimated_quote_value: float

@dataclass(frozen=True)
class RiskLimits:
    max_order_quote: float = 10.0
    max_daily_loss_quote: float = 25.0
    max_open_positions: int = 3

def validate_order(proposal: OrderProposal, limits: RiskLimits, *,
                   daily_realized_pnl: float, open_positions: int,
                   allowed_symbols: set[str]) -> None:
    if proposal.side not in {"buy", "sell"}:
        raise ValueError("Invalid order side.")
    if proposal.symbol not in allowed_symbols:
        raise ValueError("Symbol is not allowlisted.")
    if proposal.amount_base <= 0 or proposal.estimated_quote_value <= 0:
        raise ValueError("Order quantities must be positive.")
    if proposal.estimated_quote_value > limits.max_order_quote:
        raise ValueError("Order exceeds per-order exposure limit.")
    if daily_realized_pnl <= -abs(limits.max_daily_loss_quote):
        raise ValueError("Daily loss limit reached; trading must halt.")
    if proposal.side == "buy" and open_positions >= limits.max_open_positions:
        raise ValueError("Maximum open positions reached.")
