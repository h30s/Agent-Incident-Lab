from __future__ import annotations

SESSION_ID = "session-s1-tool-failure"
USER_ID = "agent-incident-lab"


def run() -> None:
    import os

    from crewai import Agent, Crew, Task
    from traceroot import observe, using_attributes

    from agent_incident_lab.injectable import (
        create_calculator_tool,
        create_inventory_tool,
        s1_replay_tool_outcome,
    )
    from agent_incident_lab.llm import agent_llm_kwargs
    from agent_incident_lab.telemetry import flush

    mode = os.environ.get("TOOL_ERROR_MODE", "malformed").strip().lower()
    llm = agent_llm_kwargs()
    calc = create_calculator_tool()
    inv = create_inventory_tool()

    researcher = Agent(
        role="Inventory Analyst",
        goal="Use tools to resolve SKU inventory; surface errors faithfully.",
        backstory="If a tool fails, you quote the error and try safe fallbacks.",
        tools=[inv, calc],
        verbose=True,
        max_iter=3,
        **llm,
    )
    research = Task(
        description=(
            "Call get_inventory for SKU-A and SKU-D (unknown SKU). "
            "If you obtain numeric units for SKU-A, calculate (units + 1) using calculate. "
            "Quote each tool return string exactly as returned."
        ),
        expected_output="Tool transcript",
        agent=researcher,
    )
    crew = Crew(
        agents=[researcher],
        tasks=[research],
        verbose=True,
        tracing=False,
    )

    @observe(name="scenario_s1_crew", type="agent")
    def _kickoff() -> str:
        return str(crew.kickoff())

    with using_attributes(user_id=USER_ID, session_id=SESSION_ID):
        print(f"session_id={SESSION_ID} TOOL_ERROR_MODE={mode}", flush=True)
        try:
            print(_kickoff(), flush=True)
        finally:
            truth = s1_replay_tool_outcome()
            print(
                "\n=== GROUND_TRUTH (deterministic replay, no LLM) ===\n"
                f"sku_a:                  {truth['sku_a']}\n"
                f"sku_d:                  {truth['sku_d']}\n"
                f"calculate(units+1):     {truth['calculate_units_plus_1']}\n"
                "=== Canonical tool facts (use if the model drifted). ===\n",
                flush=True,
            )
    flush()
