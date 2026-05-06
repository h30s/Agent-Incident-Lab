from __future__ import annotations

import ast
import json
import operator
import os

# Success JSON for S2 rate-limit demo; prompts require this marker verbatim.
S2_LOOKUP_SUCCESS_DEMO_MARKER = "agent-incident-lab-s2-lookup-v1"


def create_calculator_tool():
    from crewai.tools import tool

    @tool
    def calculate(expression: str) -> str:
        """Evaluate a numeric expression (int/float, + - * /) via AST."""
        ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
        }

        def _eval(node: ast.AST) -> float:
            if isinstance(node, ast.Expression):
                return _eval(node.body)
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return float(node.value)
            if isinstance(node, ast.BinOp) and type(node.op) in ops:
                return float(ops[type(node.op)](_eval(node.left), _eval(node.right)))
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
                return float(-_eval(node.operand))
            raise ValueError(f"Unsupported expression: {ast.dump(node)}")

        try:
            tree = ast.parse(expression, mode="eval")
            return str(_eval(tree))
        except Exception as e:
            return f"Error: {e}"

    return calculate


def create_inventory_tool():
    from crewai.tools import tool

    mode = os.environ.get("TOOL_ERROR_MODE", "ok").strip().lower()

    @tool
    def get_inventory(sku: str) -> str:
        """Return stock JSON for a SKU, or fault per TOOL_ERROR_MODE."""
        if mode == "throw":
            raise RuntimeError("inventory service unavailable (synthetic S1 fault)")
        if mode == "malformed":
            return f"<<<RAW_DB_DUMP sku={sku} bytes=\\xff\\xfe NOT_JSON>>>"
        stock = {"SKU-A": 12, "SKU-B": 0, "SKU-C": 44}
        return json.dumps({"sku": sku, "units": stock.get(sku)})

    return get_inventory


def create_rate_limited_lookup():
    from crewai.tools import tool

    fails = max(0, int(os.environ.get("RATE_LIMIT_FAIL_COUNT", "2")))
    state = {"count": 0}

    @tool
    def lookup_entry(entry_id: str) -> str:
        """Fetch catalog entry; first N calls simulate 429 (RATE_LIMIT_FAIL_COUNT).

        On success returns JSON with id, title, ok, and demo_marker.
        The demo_marker field value is always exactly agent-incident-lab-s2-lookup-v1 — copy it
        verbatim from the Observation (never replace it with a placeholder or identifier name).
        Title value is always the string Recovered after backoff, never Sample Title or placeholders.
        """
        if isinstance(entry_id, dict):
            entry_id = str(entry_id.get("entry_id", ""))
        elif not isinstance(entry_id, str):
            entry_id = str(entry_id)
        state["count"] += 1
        if state["count"] <= fails:
            raise RuntimeError("rate_limit exceeded (429) - synthetic S2 backoff demo")
        return json.dumps(
            {
                "id": entry_id,
                "title": "Recovered after backoff",
                "ok": True,
                "demo_marker": S2_LOOKUP_SUCCESS_DEMO_MARKER,
            },
            separators=(",", ":"),
        )

    return lookup_entry


def s2_replay_tool_outcome(entry_id: str = "item-42") -> dict[str, str | None]:
    """Replay S2 lookup + calculate with a fresh rate-limit counter (no LLM).

    Used by tests and printed after the crew so demos always have a canonical tool trace.
    """
    lookup = create_rate_limited_lookup()
    first_error: str | None = None
    final_json: str | None = None
    while True:
        try:
            final_json = lookup._run(entry_id)
            break
        except RuntimeError as e:
            if first_error is None:
                first_error = str(e)
    calc = create_calculator_tool()
    calc_out = calc._run("7*6")
    return {
        "first_lookup_error": first_error,
        "final_lookup_json": final_json,
        "calculate_7x6": calc_out,
    }


def happy_replay_tool_outcome() -> dict[str, str]:
    """Replay happy-path tools deterministically (no LLM)."""
    prev = os.environ.get("TOOL_ERROR_MODE")
    os.environ["TOOL_ERROR_MODE"] = "ok"
    try:
        inv = create_inventory_tool()
        calc = create_calculator_tool()
        sku_a = inv._run("SKU-A")
        sku_b = inv._run("SKU-B")
        calc_out = calc._run("12-5")
        return {"sku_a": sku_a, "sku_b": sku_b, "calculate_12_minus_5": calc_out}
    finally:
        if prev is None:
            os.environ.pop("TOOL_ERROR_MODE", None)
        else:
            os.environ["TOOL_ERROR_MODE"] = prev


def s1_replay_tool_outcome() -> dict[str, str]:
    """Replay S1 inventory behavior based on current TOOL_ERROR_MODE (no LLM)."""
    inv = create_inventory_tool()
    calc = create_calculator_tool()
    a = _safe_tool_call(inv, "SKU-A")
    d = _safe_tool_call(inv, "SKU-D")
    calc_out = "n/a"
    try:
        parsed = json.loads(a)
        units = parsed.get("units")
        if isinstance(units, (int, float)):
            calc_out = calc._run(f"{units}+1")
    except Exception:
        pass
    return {"sku_a": a, "sku_d": d, "calculate_units_plus_1": calc_out}


def s3_replay_tool_outcome() -> dict[str, str]:
    """Replay all eight planet facts and 2+2 deterministically (no LLM)."""
    facts = create_planet_fact_tool()
    calc = create_calculator_tool()
    planets = ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]
    out: dict[str, str] = {}
    for p in planets:
        out[p] = facts._run(p)
    out["calculate_2_plus_2"] = calc._run("2+2")
    return out


def _safe_tool_call(tool_obj: object, arg: str) -> str:
    """Run CrewAI tool and stringify errors for stable ground-truth blocks."""
    try:
        return getattr(tool_obj, "_run")(arg)
    except Exception as e:
        return f"Error: {e}"


def create_planet_fact_tool():
    from crewai.tools import tool

    facts = {
        "mercury": "smallest planet, no atmosphere",
        "venus": "hottest surface, thick CO2",
        "earth": "liquid water, one moon",
        "mars": "red dust, two moons",
        "jupiter": "gas giant, great red spot",
        "saturn": "prominent rings",
        "uranus": "ice giant, tilted axis",
        "neptune": "strongest winds",
    }

    @tool
    def get_planet_fact(name: str) -> str:
        """Return a one-line fact for a planet name."""
        key = name.strip().lower()
        fact = facts.get(key, "unknown object — use a major planet name")
        return f"{name}: {fact}"

    return get_planet_fact
