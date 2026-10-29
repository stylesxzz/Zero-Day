"""Public market-data adapter; no account credentials required."""
from __future__ import annotations
from typing import Any

def ticker(exchange_id: str, symbol: str) -> dict[str, Any]:
    try:
        import ccxt
    except ImportError as exc:
        raise RuntimeError("Install dependencies with pip install -r requirements.txt") from exc
    exchange_id = exchange_id.strip().lower()
    exchange_cls = getattr(ccxt, exchange_id, None)
    if exchange_cls is None or exchange_id.startswith("_"):
        raise ValueError("Unsupported exchange identifier.")
    exchange = exchange_cls({"enableRateLimit": True, "timeout": 15000})
    try:
        result = exchange.fetch_ticker(symbol)
        if result.get("last") is None:
            raise RuntimeError("Exchange returned no last price.")
        return {"exchange":exchange_id,"symbol":symbol,"last":result["last"],
                "bid":result.get("bid"),"ask":result.get("ask"),
                "percentage":result.get("percentage"),"timestamp":result.get("timestamp"),
                "datetime":result.get("datetime")}
    finally:
        close = getattr(exchange, "close", None)
        if callable(close):
            try: close()
            except Exception: pass
