"""FastAPI application for Zéro Day. Live order execution is deliberately unavailable."""
from __future__ import annotations
import os
import re
import uuid
from contextlib import asynccontextmanager
from typing import Literal
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from . import store
from .market_data import ticker
from .service import analyze_agent
from .wallets import exchange_balance, evm_native_balance

@asynccontextmanager
async def lifespan(app: FastAPI):
    store.init_db()
    store.event("system","Backend iniciado; execução de ordens reais está bloqueada.")
    yield

app = FastAPI(title="Zéro Day API", version="0.2.0",
              description="Real market data, AI trade proposals, read-only wallet connectors. Live order execution is disabled.",
              lifespan=lifespan)
WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

class AgentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    strategy: Literal["trend","mean_reversion","momentum","research"] = "trend"
    model: str = Field(default="", max_length=120)
    risk_profile: Literal["conservative","moderate","aggressive"] = "conservative"
    allocation: float = Field(default=0, ge=0, le=1_000_000)

class AnalyzeRequest(BaseModel):
    exchange: str = Field(default="kraken", pattern=r"^[a-zA-Z0-9_-]{2,40}$")
    symbol: str = Field(default="BTC/USD", min_length=3, max_length=30)

class OnchainRequest(BaseModel):
    chain: Literal["ethereum","base","polygon","arbitrum","optimism","bsc"] = "ethereum"
    address: str = Field(min_length=42, max_length=42, pattern=r"^0x[a-fA-F0-9]{40}$")

@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(os.path.join(WEB_DIR, "index.html"))

@app.get("/api/health")
def health():
    return {"status":"ok","live_orders_enabled":False,"database":"sqlite","version":"0.2.0"}

@app.get("/api/status")
def status():
    agents = store.list_agents()
    proposals = store.list_proposals(100)
    return {"live_orders_enabled":False,"agents_total":len(agents),
            "proposals_total":len(proposals),"pending_proposals":sum(p["status"]=="pending_validation" for p in proposals),
            "agents":agents[:20],"recent_events":store.list_events(12)}

@app.get("/api/agents")
def agents_list():
    return {"agents":store.list_agents()}

@app.post("/api/agents", status_code=201)
def agents_create(body: AgentCreate):
    agent = body.model_dump()
    agent.update({"id":str(uuid.uuid4())})
    try: return store.create_agent(agent)
    except Exception as exc: raise HTTPException(400, f"Could not create agent: {type(exc).__name__}") from exc

@app.post("/api/agents/{agent_id}/analyze")
def agents_analyze(agent_id: str, body: AnalyzeRequest):
    try: return analyze_agent(agent_id, body.exchange, body.symbol)
    except KeyError as exc: raise HTTPException(404, str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(503, str(exc)) from exc
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
    except Exception as exc: raise HTTPException(502, f"Market/model request failed: {type(exc).__name__}") from exc

@app.get("/api/proposals")
def proposals(limit: int = Query(default=50, ge=1, le=300)):
    return {"proposals":store.list_proposals(limit)}

@app.get("/api/events")
def events(limit: int = Query(default=50, ge=1, le=200)):
    return {"events":store.list_events(limit)}

@app.get("/api/market/ticker")
def market_ticker(exchange: str = "kraken", symbol: str = "BTC/USD"):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{2,40}", exchange): raise HTTPException(422,"Invalid exchange id.")
    if len(symbol)>30 or len(symbol)<3: raise HTTPException(422,"Invalid symbol.")
    try: return ticker(exchange, symbol)
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc
    except Exception as exc: raise HTTPException(502,f"Market request failed: {type(exc).__name__}") from exc

@app.get("/api/wallet/exchange")
def wallet_exchange():
    return exchange_balance()

@app.post("/api/wallet/onchain")
def wallet_onchain(body: OnchainRequest):
    try: return evm_native_balance(body.chain, body.address)
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc

@app.get("/api/providers")
def providers():
    # Never return API keys. Values are names of environment variables only.
    return {"configured":bool(os.getenv("ZERO_DAY_AI_BASE_URL") and os.getenv("ZERO_DAY_AI_API_KEY") and os.getenv("ZERO_DAY_AI_MODEL")),
            "base_url":os.getenv("ZERO_DAY_AI_BASE_URL",""),
            "model":os.getenv("ZERO_DAY_AI_MODEL",""),
            "api_key_env":"ZERO_DAY_AI_API_KEY" if os.getenv("ZERO_DAY_AI_API_KEY") else "",
            "compatible_protocol":"OpenAI Chat Completions"}

@app.post("/api/orders/execute", status_code=423)
def execute_order_blocked():
    raise HTTPException(423, "Live order execution is disabled until security, accounting, exchange sandbox and risk validation are complete. No order was sent.")
