from __future__ import annotations

import os
from typing import Any


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def agent_llm_kwargs() -> dict[str, Any]:
    from crewai import LLM

    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set.")

    raw = os.environ.get("OPENROUTER_MODEL", "google/gemma-2-9b-it:free").strip()
    model = raw if raw.startswith("openrouter/") else f"openrouter/{raw}"
    base = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip()
    num_retries = max(0, _int_env("OPENROUTER_NUM_RETRIES", 3))
    return {
        "llm": LLM(
            model=model,
            api_key=key,
            base_url=base,
            num_retries=num_retries,
        )
    }
