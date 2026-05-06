from __future__ import annotations

import argparse
import importlib
import os
import sys


def _load_dotenv() -> None:
    from dotenv import find_dotenv, load_dotenv

    # Avoid CrewAI unicode rendering failures on Windows consoles.
    os.environ.setdefault("PYTHONUTF8", "1")
    p = find_dotenv()
    if p:
        load_dotenv(p)


def main(argv: list[str] | None = None) -> int:
    _load_dotenv()
    p = argparse.ArgumentParser(prog="agent-incident-lab")
    p.add_argument(
        "scenario",
        nargs="?",
        default="happy",
        choices=["happy", "s1", "s2", "s3"],
    )
    args = p.parse_args(argv)

    from agent_incident_lab.telemetry import init_traceroot

    init_traceroot()
    mod = importlib.import_module(
        {
            "happy": "agent_incident_lab.scenarios.happy",
            "s1": "agent_incident_lab.scenarios.s1_tool_failure",
            "s2": "agent_incident_lab.scenarios.s2_rate_limit",
            "s3": "agent_incident_lab.scenarios.s3_iteration_guard",
        }[args.scenario]
    )
    try:
        mod.run()
    except BaseException as exc:
        msg = _llm_side_failure_message(exc)
        if msg is not None:
            if _looks_like_auth_failure(msg):
                print(
                    "\n--- OpenRouter / API authentication ---\n"
                    f"{msg}\n"
                    "Verify OPENROUTER_API_KEY in `.env` and run from `agent-incident-lab` so "
                    "dotenv loads, or export the key in your shell.\n",
                    file=sys.stderr,
                )
            elif _looks_like_rate_limit(msg):
                print(
                    "\n--- LLM-side failure: rate limit or quota ---\n"
                    f"{msg}\n"
                    "OpenRouter (or your model route) refused the call due to quota, not demo "
                    "tools. Typical fixes: add credits, switch OPENROUTER_MODEL to a tier you "
                    "still have quota for, or wait until limits reset.\n"
                    "The deterministic GROUND_TRUTH block above is still valid for the demo "
                    "without a live LLM.\n",
                    file=sys.stderr,
                )
            else:
                print(
                    "\n--- LLM-side failure (not your demo tool) ---\n"
                    f"{msg}\n"
                    "Crew could not get a usable model reply after tool output (empty body, "
                    "provider error, or parse failure).\n"
                    "Try: rerun, raise OPENROUTER_NUM_RETRIES, or switch OPENROUTER_MODEL "
                    "to a steadier route.\n",
                    file=sys.stderr,
                )
            return 1
        raise
    return 0


def _llm_side_failure_message(exc: BaseException) -> str | None:
    """LiteLLM/OpenRouter errors or CrewAI 'empty LLM response' after a bad completion."""

    def walk(e: BaseException, seen: set[int]) -> str | None:
        if id(e) in seen:
            return None
        seen.add(id(e))
        mod = getattr(type(e), "__module__", "")
        if type(e).__name__ == "APIError" and mod.startswith("litellm"):
            return str(e).strip() or "litellm.APIError"
        if type(e).__name__ == "AuthenticationError" and mod.startswith("litellm"):
            return str(e).strip() or "litellm.AuthenticationError"
        if type(e).__name__ == "RateLimitError" and mod.startswith("litellm"):
            return str(e).strip() or "litellm.RateLimitError"
        if isinstance(e, ValueError):
            text = str(e)
            if "Invalid response from LLM call" in text or "None or empty" in text:
                return text.strip() or "Invalid response from LLM call - None or empty."
        if e.__cause__ is not None:
            inner = walk(e.__cause__, seen)
            if inner is not None:
                return inner
        if e.__context__ is not None and e.__context__ is not e.__cause__:
            inner = walk(e.__context__, seen)
            if inner is not None:
                return inner
        return None

    return walk(exc, set())


def _looks_like_auth_failure(msg: str) -> bool:
    m = msg.lower()
    return (
        "authenticationerror" in m.replace(" ", "")
        or "401" in m
        or "missing authentication" in m
        or "unauthorized" in m
    )


def _looks_like_rate_limit(msg: str) -> bool:
    m = msg.lower().replace(" ", "")
    return (
        "ratelimiterror" in m
        or '"code":429' in msg
        or "429" in msg
        or "rate limit" in m
        or "free-models-per-day" in m
    )


if __name__ == "__main__":
    sys.exit(main())
