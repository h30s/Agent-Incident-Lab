from __future__ import annotations

SESSION_ID = "session-happy-path"
USER_ID = "agent-incident-lab"


def run() -> None:
    import os

    from crewai import Agent, Crew, Task
    from traceroot import observe, using_attributes

    from agent_incident_lab.injectable import (
        create_calculator_tool,
        create_inventory_tool,
        happy_replay_tool_outcome,
    )
    from agent_incident_lab.llm import agent_llm_kwargs
    from agent_incident_lab.telemetry import flush

    os.environ["TOOL_ERROR_MODE"] = "ok"
    llm = agent_llm_kwargs()
    calc = create_calculator_tool()
    inv = create_inventory_tool()

    researcher = Agent(
        role="Inventory Analyst",
        goal="Use tools to resolve SKU inventory and calculations accurately.",
        backstory="You always call tools instead of guessing numbers.",
        tools=[inv, calc],
        verbose=True,
        max_iter=3,
        **llm,
    )
    research = Task(
        description=(
            "Use get_inventory for SKU-A and SKU-B. "
            "If SKU-A units exist and exceed 5, calculate (units - 5) with calculate. "
            "List raw tool outputs."
        ),
        expected_output="Bullet list of tool results",
        agent=researcher,
    )
    crew = Crew(
        agents=[researcher],
        tasks=[research],
        verbose=True,
        tracing=False,
    )

    @observe(name="scenario_happy_crew", type="agent")
    def _kickoff() -> str:
        return str(crew.kickoff())

    with using_attributes(user_id=USER_ID, session_id=SESSION_ID):
        print(f"session_id={SESSION_ID}", flush=True)
        try:
            print(_kickoff(), flush=True)
        finally:
            truth = happy_replay_tool_outcome()
            print(
                "\n=== GROUND_TRUTH (deterministic replay, no LLM) ===\n"
                f"sku_a:               {truth['sku_a']}\n"
                f"sku_b:               {truth['sku_b']}\n"
                f"calculate(12-5):     {truth['calculate_12_minus_5']}\n"
                "=== Canonical tool facts (use if the model drifted). ===\n",
                flush=True,
            )
    flush()
