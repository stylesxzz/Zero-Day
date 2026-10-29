"""Read-only exchange adapter.

This release intentionally does not contain a live order submission path.
Use only a dedicated exchange API key with withdrawals disabled.
"""
from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class ExchangeSettings:
    exchange_id: str
    api_key: str
    secret: str
    max_order_quote: float
    allowed_symbols: tuple[str, ...]

def settings_from_env() -> ExchangeSettings:
    return ExchangeSettings(
        exchange_id=os.getenv("ZERO_DAY_EXCHANGE_ID", "kraken").strip().lower(),
        api_key=os.getenv("ZERO_DAY_EXCHANGE_API_KEY", "").strip(),
        secret=os.getenv("ZERO_DAY_EXCHANGE_SECRET", "").strip(),
        max_order_quote=max(0.0, float(os.getenv("ZERO_DAY_MAX_ORDER_QUOTE", "10"))),
        allowed_symbols=tuple(s.strip() for s in os.getenv("ZERO_DAY_ALLOWED_SYMBOLS", "BTC/USD").split(",") if s.strip()),
    )

class SpotExchange:
    """Read balances and tickers only; all order methods fail closed."""
    def __init__(self, settings: ExchangeSettings | None = None) -> None:
        self.settings = settings or settings_from_env()
        try:
            import ccxt
        except ImportError as exc:
            raise RuntimeError("Install dependencies with: pip install -r requirements.txt") from exc
        exchange_class = getattr(ccxt, self.settings.exchange_id, None)
        if exchange_class is None:
            raise ValueError("Unsupported exchange identifier.")
        options: dict[str, Any] = {"enableRateLimit": True, "timeout": 20000, "options": {"defaultType": "spot"}}
        if self.settings.api_key and self.settings.secret:
            options.update({"apiKey": self.settings.api_key, "secret": self.settings.secret})
        self.client = exchange_class(options)

    def fetch_balance(self) -> dict[str, Any]:
        if not self.settings.api_key or not self.settings.secret:
            raise RuntimeError("Exchange credentials are required to query a private account balance.")
        return self.client.fetch_balance()

    def fetch_ticker(self, symbol: str) -> dict[str, Any]:
        self._check_symbol(symbol)
        return self.client.fetch_ticker(symbol)

    def submit_market_order(self, symbol: str, side: str, amount_base: float,
                            estimated_quote_value: float) -> dict[str, Any]:
        raise RuntimeError("LIVE ORDER EXECUTION IS DISABLED IN THIS RELEASE. No order was sent.")

    def _check_symbol(self, symbol: str) -> None:
        if symbol not in self.settings.allowed_symbols:
            raise ValueError("Symbol is not in ZERO_DAY_ALLOWED_SYMBOLS.")
