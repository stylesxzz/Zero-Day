"""Agent analysis orchestration. Decisions are proposals, never executable commands."""
from __future__ import annotations
import json
import os
import uuid
from typing import Any
from zeroday.providers.llm import ModelConfig, OpenAICompatibleModel
from . import store
from .market_data import ticker

SYSTEM_PROMPT = """You are a cautious crypto market research agent. Return ONLY a JSON object with keys action, confidence, rationale. action must be BUY, SELL, or HOLD. confidence must be a number from 0 to 1. rationale must be a short string. Do not request credentials or claim to execute trades. Prefer HOLD when data is insufficient. This is research only; every proposal requires separate deterministic validation."""

def _model_for_agent(agent: dict[str, Any]) -> OpenAICompatibleModel:
    base = os.getenv("ZERO_DAY_AI_BASE_URL","").strip()
    key = os.getenv("ZERO_DAY_AI_API_KEY","").strip()
    model = agent.get("model") or os.getenv("ZERO_DAY_AI_MODEL","").strip()
    if not (base and key and model):
        raise RuntimeError("Configure ZERO_DAY_AI_BASE_URL, ZERO_DAY_AI_API_KEY and ZERO_DAY_AI_MODEL in local .env.")
    return OpenAICompatibleModel(ModelConfig(base, key, model))

def analyze_agent(agent_id: str, exchange_id: str, symbol: str) -> dict[str, Any]:
    agent = store.get_agent(agent_id)
    if not agent: raise KeyError("Agent not found.")
    snapshot = ticker(exchange_id, symbol)
    response = _model_for_agent(agent).decide(SYSTEM_PROMPT, snapshot)
    try:
        raw = json.loads(response)
        action = str(raw["action"]).upper()
        confidence = float(raw["confidence"])
        rationale = str(raw["rationale"]).strip()
    except (ValueError, TypeError, KeyError) as exc:
        raise ValueError("Model response must be JSON with action, confidence and rationale.") from exc
    if action not in {"BUY","SELL","HOLD"}: raise ValueError("Model returned an unsupported action.")
    if not 0 <= confidence <= 1: raise ValueError("Model confidence must be between 0 and 1.")
    if not rationale or len(rationale)>500: raise ValueError("Model rationale is empty or too long.")
    proposal = {"id":str(uuid.uuid4()),"agent_id":agent_id,"symbol":symbol,"action":action,
                "confidence":confidence,"rationale":rationale,"snapshot":snapshot,
                "status":"pending_validation"}
    store.save_proposal(proposal)
    return proposal
