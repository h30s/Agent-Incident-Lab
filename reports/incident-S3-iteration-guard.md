# S3 — iteration cap vs eight tool calls

**SEV-3 ·** `session-s3-iteration-guard`

## Summary

Researcher `max_iter=2`; task asks for eight separate `get_planet_fact` calls. Expect partial completion and an honest writer summary.

## Repro

1. `<COMMIT_SHA>`
2. `.env` populated
3. `python -m agent_incident_lab s3`

## TraceRoot

`session_id=session-s3-iteration-guard`.

## Root cause

By design (`s3_iteration_guard.py`).

## Verification

Raise `max_iter` locally if you need a full eight-call run for comparison.
