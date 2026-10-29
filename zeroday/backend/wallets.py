"""Read-only wallet connectors for exchange accounts and EVM on-chain addresses."""
from __future__ import annotations
import os
from typing import Any
import httpx

def exchange_balance() -> dict[str, Any]:
    exchange_id = os.getenv("ZERO_DAY_EXCHANGE_ID", "kraken").strip().lower()
    api_key = os.getenv("ZERO_DAY_EXCHANGE_API_KEY", "").strip()
    secret = os.getenv("ZERO_DAY_EXCHANGE_SECRET", "").strip()
    if not api_key or not secret:
        return {"connected":False,"mode":"read_only_connector","message":"Exchange credentials not configured; balances unavailable."}
    try:
        import ccxt
        cls = getattr(ccxt, exchange_id, None)
        if cls is None: raise ValueError("Unsupported exchange identifier.")
        client = cls({"apiKey":api_key,"secret":secret,"enableRateLimit":True,"timeout":15000,
                      "options":{"defaultType":"spot"}})
        result = client.fetch_balance()
        totals = result.get("total", {}) or {}
        balances = [{"asset":asset,"total":float(amount)} for asset,amount in totals.items()
                    if amount is not None and float(amount) > 0]
        return {"connected":True,"exchange":exchange_id,"balances":balances,"read_only":True}
    except Exception as exc:
        return {"connected":False,"exchange":exchange_id,"message":f"Balance query failed: {type(exc).__name__}"}

def evm_native_balance(chain: str, address: str) -> dict[str, Any]:
    """Query public EVM native balance only; no seed/private key/signing support."""
    endpoints = {
        "ethereum":os.getenv("ZERO_DAY_RPC_ETHEREUM",""),
        "base":os.getenv("ZERO_DAY_RPC_BASE",""),
        "polygon":os.getenv("ZERO_DAY_RPC_POLYGON",""),
        "arbitrum":os.getenv("ZERO_DAY_RPC_ARBITRUM",""),
        "optimism":os.getenv("ZERO_DAY_RPC_OPTIMISM",""),
        "bsc":os.getenv("ZERO_DAY_RPC_BSC",""),
    }
    chain = chain.strip().lower()
    if chain not in endpoints: raise ValueError("Unsupported EVM chain.")
    if not address.startswith("0x") or len(address) != 42:
        raise ValueError("Expected a 0x-prefixed 20-byte EVM address.")
    endpoint = endpoints[chain]
    if not endpoint: return {"connected":False,"chain":chain,"address":address,"message":"Public RPC URL is not configured."}
    try:
        response = httpx.post(endpoint, json={"jsonrpc":"2.0","id":1,"method":"eth_getBalance",
                              "params":[address,"latest"]}, timeout=12)
        response.raise_for_status()
        payload = response.json()
        if payload.get("error") or not payload.get("result"):
            raise RuntimeError("RPC response contained an error.")
        wei = int(payload["result"],16)
        return {"connected":True,"chain":chain,"address":address,"native_balance":str(wei / 10**18),
                "unit":{"ethereum":"ETH","base":"ETH","polygon":"POL","arbitrum":"ETH","optimism":"ETH","bsc":"BNB"}[chain],
                "block_tag":"latest","read_only":True}
    except Exception as exc:
        return {"connected":False,"chain":chain,"address":address,"message":f"RPC query failed: {type(exc).__name__}"}
