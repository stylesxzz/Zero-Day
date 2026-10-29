"""Deterministic-friendly synthetic crypto market; never connects to an exchange."""

from __future__ import annotations

import math
import random
from collections import deque
from typing import Deque

from .config import ASSETS
from .models import MarketSnapshot


class SimulatedMarket:
    def __init__(self, seed: int | None = None, history_size: int = 180) -> None:
        self.rng = random.Random(seed)
        self.prices: dict[str, float] = {"BTC": 64000.0, "ETH": 3200.0, "SOL": 145.0, "NOVA": 22.0}
        self.history: dict[str, Deque[float]] = {
            symbol: deque([price] * 25, maxlen=history_size)
            for symbol, price in self.prices.items()
        }
        self.tick_count = 0
        self._phase = {symbol: self.rng.random() * math.tau for symbol in ASSETS}

    def step(self) -> None:
        self.tick_count += 1
        for symbol in ASSETS:
            old = self.prices[symbol]
            phase = self._phase[symbol]
            cycle = math.sin(self.tick_count / 34.0 + phase) * 0.0018
            drift = math.sin(self.tick_count / 180.0 + phase / 2) * 0.00035
            shock = self.rng.gauss(0.0, 0.009 if symbol == "NOVA" else 0.0045)
            log_return = max(-0.12, min(0.12, cycle + drift + shock))
            self.prices[symbol] = max(0.01, old * math.exp(log_return))
            self.history[symbol].append(self.prices[symbol])

    @staticmethod
    def _ema(values: list[float], period: int) -> float:
        if not values:
            return 0.0
        alpha = 2.0 / (period + 1.0)
        value = values[0]
        for sample in values[1:]:
            value = alpha * sample + (1.0 - alpha) * value
        return value

    @staticmethod
    def _rsi(values: list[float], period: int = 14) -> float:
        if len(values) < 2:
            return 50.0
        changes = [values[i] - values[i - 1] for i in range(1, len(values))][-period:]
        gains = sum(change for change in changes if change > 0) / max(1, period)
        losses = -sum(change for change in changes if change < 0) / max(1, period)
        if losses == 0:
            return 100.0 if gains > 0 else 50.0
        rs = gains / losses
        return 100.0 - (100.0 / (1.0 + rs))

    def snapshot(self, symbol: str) -> MarketSnapshot:
        values = list(self.history[symbol])
        price = self.prices[symbol]
        ema_fast = self._ema(values[-24:], 8)
        ema_slow = self._ema(values[-60:], 21)
        rsi = self._rsi(values[-16:], 14)
        reference = values[-6] if len(values) >= 6 else values[0]
        momentum = (price / reference - 1.0) if reference else 0.0
        returns = [values[i] / values[i - 1] - 1.0 for i in range(1, len(values)) if values[i - 1] > 0]
        recent = returns[-20:]
        volatility = (sum(value * value for value in recent) / max(1, len(recent))) ** 0.5
        return MarketSnapshot(symbol, price, ema_fast, ema_slow, rsi, momentum, volatility)

    def all_snapshots(self) -> dict[str, MarketSnapshot]:
        return {symbol: self.snapshot(symbol) for symbol in ASSETS}
