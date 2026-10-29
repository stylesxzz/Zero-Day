"""Guarded spot-exchange adapter. Live orders are disabled by default."""
from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class ExchangeSettings:
    exchange_id: str
    api_key: str
    secret: str
    live_enabled: bool
    max_order_quote: float
    allowed_symbols: tuple[str, ...]

def settings_from_env() -> ExchangeSettings:
    return ExchangeSettings(
        exchange_id=os.getenv("ZERO_DAY_EXCHANGE_ID", "kraken").strip().lower(),
        api_key=os.getenv("ZERO_DAY_EXCHANGE_API_KEY", "").strip(),
        secret=os.getenv("ZERO_DAY_EXCHANGE_SECRET", "").strip(),
        live_enabled=(os.getenv("ZERO_DAY_LIVE_TRADING", "false").lower() == "true"
                      and os.getenv("ZERO_DAY_LIVE_ACK", "") == "I_UNDERSTAND_REAL_FUNDS"),
        max_order_quote=max(0.0, float(os.getenv("ZERO_DAY_MAX_ORDER_QUOTE", "10"))),
        allowed_symbols=tuple(s.strip() for s in os.getenv("ZERO_DAY_ALLOWED_SYMBOLS", "BTC/USDT").split(",") if s.strip()),
    )

class SpotExchange:
    """CCXT wrapper. Use a dedicated subaccount and API keys with withdrawals disabled."""
    def __init__(self, settings: ExchangeSettings | None = None) -> None:
        self.settings = settings or settings_from_env()
        if not self.settings.api_key or not self.settings.secret:
            raise RuntimeError("Configure exchange API credentials in your local .env.")
        try:
            import ccxt
        except ImportError as exc:
            raise RuntimeError("Install dependencies with: pip install -r requirements.txt") from exc
        exchange_class = getattr(ccxt, self.settings.exchange_id, None)
        if exchange_class is None:
            raise ValueError(f"Unsupported CCXT exchange id: {self.settings.exchange_id}")
        self.client: Any = exchange_class({
            "apiKey": self.settings.api_key, "secret": self.settings.secret,
            "enableRateLimit": True, "timeout": 20000, "options": {"defaultType": "spot"},
        })

    def fetch_balance(self) -> dict[str, Any]:
        return self.client.fetch_balance()

    def fetch_ticker(self, symbol: str) -> dict[str, Any]:
        self._check_symbol(symbol)
        return self.client.fetch_ticker(symbol)

    def submit_market_order(self, symbol: str, side: str, amount_base: float,
                            estimated_quote_value: float) -> dict[str, Any]:
        self._check_symbol(symbol)
        if side not in {"buy", "sell"}:
            raise ValueError("side must be 'buy' or 'sell'")
        if amount_base <= 0 or estimated_quote_value <= 0:
            raise ValueError("order quantities must be positive")
        if not self.settings.live_enabled:
            raise RuntimeError("LIVE ORDER BLOCKED: explicitly configure both live-trading flags after risk review.")
        if self.settings.max_order_quote <= 0 or estimated_quote_value > self.settings.max_order_quote:
            raise RuntimeError("Order exceeds ZERO_DAY_MAX_ORDER_QUOTE.")
        return self.client.create_order(symbol, "market", side, amount_base)

    def _check_symbol(self, symbol: str) -> None:
        if symbol not in self.settings.allowed_symbols:
            raise ValueError(f"{symbol} is not in ZERO_DAY_ALLOWED_SYMBOLS.")
