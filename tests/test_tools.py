from __future__ import annotations

import json

import pytest


def test_verify_tools_main_exits_zero():
    from agent_incident_lab.verify_tools import main

    assert main() == 0


def test_s2_replay_json_shape(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_FAIL_COUNT", "2")
    from agent_incident_lab.injectable import S2_LOOKUP_SUCCESS_DEMO_MARKER, s2_replay_tool_outcome

    out = s2_replay_tool_outcome("item-42")
    assert out["first_lookup_error"] and "429" in out["first_lookup_error"]
    data = json.loads(out["final_lookup_json"] or "{}")
    assert data["demo_marker"] == S2_LOOKUP_SUCCESS_DEMO_MARKER
    assert data["title"] == "Recovered after backoff"
    assert data["id"] == "item-42"


def test_calculate_basic():
    from agent_incident_lab.injectable import create_calculator_tool

    c = create_calculator_tool()
    assert c._run("1+2") == "3.0"
