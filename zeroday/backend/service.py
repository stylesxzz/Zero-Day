"""Agent analysis orchestration. Decisions are proposals, never executable commands."""
from __future__ import annotations
import json
import os
import uuid
from typing import Any
from urllib.parse import urlsplit
from zeroday.providers.llm import ModelConfig, OpenAICompatibleModel
from . import store
from .market_data import ticker

SYSTEM_PROMPT = """You are a cautious crypto market research agent. Return ONLY a JSON object with keys action, confidence, rationale. action must be BUY, SELL, or HOLD. confidence must be a number from 0 to 1. rationale must be a short string. Do not request credentials or claim to execute trades. Prefer HOLD when data is insufficient. This is research only; every proposal requires separate deterministic validation."""

def provider_registry() -> list[dict[str, Any]]:
    """Return sanitized provider profiles; secrets are referenced by env var name only."""
    raw = os.getenv("ZERO_DAY_AI_PROVIDERS_JSON", "").strip()
    profiles: list[dict[str, Any]] = []
    if raw:
        try:
            parsed = json.loads(raw)
            if not isinstance(parsed, list): raise ValueError("Provider config must be a JSON list.")
            for item in parsed:
                if not isinstance(item, dict): continue
                profile = {
                    "id": str(item.get("id", "")).strip(),
                    "name": str(item.get("name", item.get("id", ""))).strip(),
                    "base_url": str(item.get("base_url", "")).strip(),
                    "model": str(item.get("model", "")).strip(),
                    "api_key_env": str(item.get("api_key_env", "")).strip(),
                }
                if profile["id"] and profile["base_url"] and profile["model"] and profile["api_key_env"]:
                    parsed_url = urlsplit(profile["base_url"])
                    if (parsed_url.scheme not in {"https", "http"} or not parsed_url.hostname
                            or parsed_url.username or parsed_url.password or parsed_url.query or parsed_url.fragment):
                        raise ValueError("Provider base_url must be an HTTP(S) URL without embedded credentials, query or fragment.")
                    profile["configured"] = bool(os.getenv(profile["api_key_env"], "").strip())
                    profiles.append(profile)
        except (json.JSONDecodeError, ValueError):
            raise RuntimeError("ZERO_DAY_AI_PROVIDERS_JSON must be a valid JSON list of provider profiles.")
    if not profiles:
        base = os.getenv("ZERO_DAY_AI_BASE_URL", "").strip()
        model = os.getenv("ZERO_DAY_AI_MODEL", "").strip()
        key_env = "ZERO_DAY_AI_API_KEY"
        if base and model:
            parsed_url = urlsplit(base)
            if (parsed_url.scheme not in {"https", "http"} or not parsed_url.hostname
                    or parsed_url.username or parsed_url.password or parsed_url.query or parsed_url.fragment):
                raise RuntimeError("ZERO_DAY_AI_BASE_URL must be an HTTP(S) URL without embedded credentials, query or fragment.")
            profiles.append({"id":"default","name":"Default OpenAI-compatible","base_url":base,
                             "model":model,"api_key_env":key_env,
                             "configured":bool(os.getenv(key_env,"").strip())})
    return profiles

def _model_for_agent(agent: dict[str, Any]) -> OpenAICompatibleModel:
    profiles = provider_registry()
    provider_id = agent.get("provider_id") or "default"
    profile = next((p for p in profiles if p["id"] == provider_id), None)
    if profile is None:
        raise RuntimeError(f"Provider '{provider_id}' is not configured.")
    key = os.getenv(profile["api_key_env"], "").strip()
    model = agent.get("model") or profile["model"]
    if not (profile["base_url"] and key and model):
        raise RuntimeError("Configure the selected provider URL, model and API key environment variable in local .env.")
    return OpenAICompatibleModel(ModelConfig(profile["base_url"], key, model))

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
