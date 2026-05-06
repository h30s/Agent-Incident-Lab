"""Deterministic checks for injectable tools (no OpenRouter, no Crew run)."""

from __future__ import annotations

import json
import os
import sys


def main() -> int:
    errors: list[str] = []

    def register(msg: str) -> None:
        errors.append(msg)

    from agent_incident_lab.injectable import (
        S2_LOOKUP_SUCCESS_DEMO_MARKER,
        create_calculator_tool,
        create_inventory_tool,
        create_planet_fact_tool,
        create_rate_limited_lookup,
        s2_replay_tool_outcome,
    )

    calc = create_calculator_tool()
    seven_six = calc._run("7*6")
    if seven_six not in ("42", "42.0"):
        register(f"calculate 7*6: expected 42 or 42.0, got {seven_six!r}")

    os.environ["TOOL_ERROR_MODE"] = "ok"
    inv = create_inventory_tool()
    sku_a = inv._run("SKU-A")
    try:
        data_a = json.loads(sku_a)
    except json.JSONDecodeError:
        register(f"inventory SKU-A not JSON: {sku_a!r}")
    else:
        if data_a.get("sku") != "SKU-A" or data_a.get("units") != 12:
            register(f"inventory SKU-A wrong payload: {sku_a!r}")

    os.environ["TOOL_ERROR_MODE"] = "malformed"
    inv_m = create_inventory_tool()
    raw = inv_m._run("SKU-A")
    if "NOT_JSON" not in raw:
        register("malformed inventory should return NOT_JSON marker")

    os.environ["RATE_LIMIT_FAIL_COUNT"] = "2"
    out = s2_replay_tool_outcome("item-42")
    err1 = out["first_lookup_error"]
    if err1 is None or "429" not in err1:
        register(f"S2 first error should mention 429, got {err1!r}")
    fj = out["final_lookup_json"] or ""
    try:
        lj = json.loads(fj)
    except json.JSONDecodeError:
        register(f"S2 success not JSON: {fj!r}")
    else:
        if lj.get("demo_marker") != S2_LOOKUP_SUCCESS_DEMO_MARKER:
            register(f"S2 demo_marker mismatch: {lj.get('demo_marker')!r}")
        if lj.get("title") != "Recovered after backoff":
            register(f"S2 title mismatch: {lj.get('title')!r}")

    os.environ["RATE_LIMIT_FAIL_COUNT"] = "0"
    out0 = s2_replay_tool_outcome("item-42")
    if out0["first_lookup_error"] is not None:
        register(f"S2 with zero fails should have no first error, got {out0['first_lookup_error']!r}")

    facts = create_planet_fact_tool()
    mars = facts._run("Mars")
    if "mars" not in mars.lower() or "moon" not in mars.lower():
        register(f"planet fact Mars unexpected: {mars!r}")

    # Fresh lookup instance: first call should 429 when FAIL_COUNT >= 1
    os.environ["RATE_LIMIT_FAIL_COUNT"] = "1"
    lu = create_rate_limited_lookup()
    try:
        lu._run("item-42")
        register("RATE_LIMIT_FAIL_COUNT=1: first lookup should raise")
    except RuntimeError:
        pass
    ok_json = lu._run("item-42")
    try:
        okd = json.loads(ok_json)
    except json.JSONDecodeError:
        register(f"second lookup not JSON: {ok_json!r}")
    else:
        if okd.get("id") != "item-42":
            register(f"lookup id mismatch: {okd!r}")

    if errors:
        print("verify_tools: FAILED", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("verify_tools: OK (injectable tools + S2 replay)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
