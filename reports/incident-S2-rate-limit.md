# S2 — synthetic 429 on `lookup_entry`

**SEV-3 ·** `session-s2-rate-limit`

## Summary

First `RATE_LIMIT_FAIL_COUNT` calls raise a 429-style error, then succeed. The CLI prints a deterministic **`GROUND_TRUTH`** tool replay after the crew (single analyst agent for reliability).

## Repro

1. `<COMMIT_SHA>`
2. `.env` populated
3. `RATE_LIMIT_FAIL_COUNT=2 python -m agent_incident_lab s2`

## TraceRoot

`session_id=session-s2-rate-limit`. Compare retries vs happy path latency.

## Root cause

Counter in `create_rate_limited_lookup`.

## Verification

`RATE_LIMIT_FAIL_COUNT=0 python -m agent_incident_lab s2`
