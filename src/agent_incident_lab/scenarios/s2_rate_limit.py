from __future__ import annotations

SESSION_ID = "session-s2-rate-limit"
USER_ID = "agent-incident-lab"


def run() -> None:
    import os

    from crewai import Agent, Crew, Task
    from traceroot import observe, using_attributes

    from agent_incident_lab.injectable import (
        create_calculator_tool,
        create_rate_limited_lookup,
        s2_replay_tool_outcome,
    )
    from agent_incident_lab.llm import agent_llm_kwargs
    from agent_incident_lab.telemetry import flush

    fails = os.environ.get("RATE_LIMIT_FAIL_COUNT", "2")
    llm = agent_llm_kwargs()
    lookup = create_rate_limited_lookup()
    calc = create_calculator_tool()

    # Single agent: the second LLM step was a major source of hallucinations on small models.
    researcher = Agent(
        role="Catalog Analyst",
        goal="Retrieve catalog entries with tools; retry sensibly on transient errors.",
        backstory=(
            "You call lookup_entry and calculate only via tools. You copy Observations verbatim "
            "into your answer, including the full demo_marker value (a string starting with "
            "agent-incident-lab-). Do not put code identifiers or ALL_CAPS tokens inside JSON. "
            "The calculate tool returns a plain numeric string (e.g. 42.0), not JSON."
        ),
        tools=[lookup, calc],
        verbose=True,
        **llm,
    )

    research = Task(
        description=(
            "Call lookup_entry for id 'item-42'. If the tool errors, retry until it succeeds "
            "or you exhaust reasonable attempts. Then call calculate with expression 7*6 "
            "(plain tool observation will look like 42.0, not JSON). "
            "Finish with a short bullet list quoting each tool Observation verbatim."
        ),
        expected_output="Bullets match Observation text only; calculate line is a number string.",
        agent=researcher,
    )

    crew = Crew(
        agents=[researcher],
        tasks=[research],
        verbose=True,
        tracing=False,
    )

    @observe(name="scenario_s2_crew", type="agent")
    def _kickoff() -> str:
        return str(crew.kickoff())

    with using_attributes(user_id=USER_ID, session_id=SESSION_ID):
        print(f"session_id={SESSION_ID} RATE_LIMIT_FAIL_COUNT={fails}", flush=True)
        try:
            print(_kickoff(), flush=True)
        finally:
            truth = s2_replay_tool_outcome("item-42")
            print(
                "\n=== GROUND_TRUTH (deterministic replay, no LLM) ===\n"
                f"first_lookup_error: {truth['first_lookup_error']!r}\n"
                f"final_lookup_json:  {truth['final_lookup_json']}\n"
                f"calculate(7*6):     {truth['calculate_7x6']}\n"
                "=== Canonical tool facts (use if the crew failed or the model drifted). ===\n",
                flush=True,
            )
    flush()
