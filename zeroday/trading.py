"""Rule-based agent brain. Signals are educational, not investment advice."""

from __future__ import annotations

from dataclasses import dataclass

from .config import RISK_PROFILES
from .models import Action, MarketSnapshot, Robot


@dataclass(frozen=True)
class Decision:
    action: Action
    reason: str
    confidence: float


class TradingBrain:
    def decide(self, robot: Robot, market: MarketSnapshot) -> Decision:
        profile = RISK_PROFILES[robot.risk_name]
        has_position = robot.quantity > 0.0000001

        if has_position:
            change_from_entry = market.price / robot.average_entry - 1.0 if robot.average_entry else 0.0
            if change_from_entry <= -profile.stop_loss_pct:
                return Decision(Action.SELL, f"stop-loss acionado ({change_from_entry:.1%})", 0.98)
            if change_from_entry >= profile.take_profit_pct:
                return Decision(Action.SELL, f"alvo de lucro atingido ({change_from_entry:.1%})", 0.92)
            if market.rsi >= 77.0 or (market.trend == "baixa" and market.momentum < -0.012):
                return Decision(Action.SELL, "tendência perdeu força; protegendo o capital", 0.76)
            return Decision(Action.HOLD, "posição mantida; aguardando confirmação", 0.55)

        aligned_up = market.ema_fast > market.ema_slow and market.momentum > 0.001
        rsi_in_window = profile.buy_rsi_min <= market.rsi <= profile.buy_rsi_max
        if aligned_up and rsi_in_window and market.volatility < 0.055:
            confidence = min(0.95, 0.60 + abs(market.momentum) * 8.0)
            return Decision(Action.BUY, "tendência positiva com RSI em faixa de entrada", confidence)

        if market.rsi < 25.0 and market.ema_fast > market.ema_slow:
            return Decision(Action.BUY, "possível recuperação após sobrevenda", 0.62)

        if market.volatility >= 0.055:
            reason = "volatilidade elevada; preservando caixa"
        elif market.trend == "baixa":
            reason = "tendência de baixa; sem entrada"
        elif market.rsi > profile.buy_rsi_max:
            reason = "mercado esticado; evitando comprar no topo"
        else:
            reason = "sem sinal suficientemente forte"
        return Decision(Action.HOLD, reason, 0.35)
