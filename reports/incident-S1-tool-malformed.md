# S1 — tool fault (`get_inventory`)

**SEV-3 ·** `session-s1-tool-failure`

## Summary

`TOOL_ERROR_MODE` drives `get_inventory`: `ok`, `malformed`, or `throw`.

## Repro

1. Repo at `<COMMIT_SHA>`
2. `.env` with `OPENROUTER_API_KEY`, `TRACEROOT_API_KEY`
3. `TOOL_ERROR_MODE=malformed python -m agent_incident_lab s1` (or `throw` / `ok`)

## TraceRoot

Filter `session_id=session-s1-tool-failure`, `user_id=agent-incident-lab`. Note tool vs generation spans on errors.

## Root cause

Injected in `injectable.create_inventory_tool`.

## Verification

`TOOL_ERROR_MODE=ok python -m agent_incident_lab s1` — tool path clean.
