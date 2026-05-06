# Agent Incident Lab

Simple CrewAI demo with TraceRoot tracing. Uses OpenRouter (LiteLLM). Includes 3 failure scenarios.

## Requirements

* Python 3.11/3.12
* Add `OPENROUTER_API_KEY` and `TRACEROOT_API_KEY` in `.env`
* Install: `pip install -e .`

(Disable tracing if needed: `TRACEROOT_ENABLED=false`)

## Run

```bash
python -m agent_incident_lab happy
python -m agent_incident_lab s1
TOOL_ERROR_MODE=throw python -m agent_incident_lab s1
python -m agent_incident_lab s2
python -m agent_incident_lab s3
```

## Scenarios

* **happy** – normal run
* **s1** – tool errors
* **s2** – rate limit + replay (`GROUND_TRUTH`)
* **s3** – iteration limit

## Notes

* LLM errors = retry or switch model
* 401 = missing API key
* On Windows, enable UTF-8 if encoding breaks