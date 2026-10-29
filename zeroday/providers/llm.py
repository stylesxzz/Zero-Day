"""Provider-agnostic chat adapter for OpenAI-compatible model APIs."""
from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class ModelConfig:
    base_url: str
    api_key: str
    model: str
    timeout_seconds: float = 45.0

def config_from_env() -> ModelConfig:
    base_url = os.getenv("ZERO_DAY_AI_BASE_URL", "").strip()
    api_key = os.getenv("ZERO_DAY_AI_API_KEY", "").strip()
    model = os.getenv("ZERO_DAY_AI_MODEL", "").strip()
    if not base_url or not api_key or not model:
        raise RuntimeError("Configure ZERO_DAY_AI_BASE_URL, ZERO_DAY_AI_API_KEY and ZERO_DAY_AI_MODEL locally.")
    return ModelConfig(base_url, api_key, model)

class OpenAICompatibleModel:
    """Model output is advice only; it is never a direct exchange command."""
    def __init__(self, config: ModelConfig | None = None) -> None:
        self.config = config or config_from_env()

    def decide(self, system_prompt: str, market_snapshot: dict[str, Any]) -> str:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install dependencies with: pip install -r requirements.txt") from exc
        client = OpenAI(base_url=self.config.base_url, api_key=self.config.api_key,
                        timeout=self.config.timeout_seconds, max_retries=1)
        response = client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Return a proposed trading action; do not claim to execute orders. Snapshot: " + repr(market_snapshot)},
            ],
            temperature=0.1,
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("The configured model returned an empty response.")
        return content
