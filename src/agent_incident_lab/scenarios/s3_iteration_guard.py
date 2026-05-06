from __future__ import annotations

SESSION_ID = "session-s3-iteration-guard"
USER_ID = "agent-incident-lab"


def run() -> None:
    from crewai import Agent, Crew, Task
    from traceroot import observe, using_attributes

    from agent_incident_lab.injectable import (
        create_calculator_tool,
        create_planet_fact_tool,
        s3_replay_tool_outcome,
    )
    from agent_incident_lab.llm import agent_llm_kwargs
    from agent_incident_lab.telemetry import flush

    llm = agent_llm_kwargs()
    facts = create_planet_fact_tool()
    calc = create_calculator_tool()

    researcher = Agent(
        role="Solar System Auditor",
        goal="Call get_planet_fact once per planet in the task list — no batching.",
        backstory="You must use the tool for each planet name separately.",
        tools=[facts, calc],
        verbose=True,
        max_iter=2,
        **llm,
    )
    writer = Agent(
        role="Mission Reporter",
        goal="Explain coverage vs requested planets honestly.",
        backstory="You state iteration limits if research was incomplete.",
        verbose=True,
        **llm,
    )

    research = Task(
        description=(
            "For EACH of these eight planets, call get_planet_fact exactly once in separate "
            "tool invocations: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune. "
            "Then calculate 2+2 with calculate. Do not invent facts without the tool."
        ),
        expected_output="Eight tool lines plus calculation",
        agent=researcher,
    )
    report = Task(
        description=(
            "Summarize how many planets were actually retrieved vs eight requested, "
            "and mention if iteration limits likely stopped the researcher."
        ),
        expected_output="Short honest summary",
        agent=writer,
        context=[research],
    )

    crew = Crew(
        agents=[researcher, writer],
        tasks=[research, report],
        verbose=True,
        tracing=False,
    )

    @observe(name="scenario_s3_crew", type="agent")
    def _kickoff() -> str:
        return str(crew.kickoff())

    with using_attributes(user_id=USER_ID, session_id=SESSION_ID):
        print(f"session_id={SESSION_ID}", flush=True)
        try:
            print(_kickoff(), flush=True)
        finally:
            truth = s3_replay_tool_outcome()
            print(
                "\n=== GROUND_TRUTH (deterministic replay, no LLM) ===\n"
                f"Mercury:               {truth['Mercury']}\n"
                f"Venus:                 {truth['Venus']}\n"
                f"Earth:                 {truth['Earth']}\n"
                f"Mars:                  {truth['Mars']}\n"
                f"Jupiter:               {truth['Jupiter']}\n"
                f"Saturn:                {truth['Saturn']}\n"
                f"Uranus:                {truth['Uranus']}\n"
                f"Neptune:               {truth['Neptune']}\n"
                f"calculate(2+2):        {truth['calculate_2_plus_2']}\n"
                "=== Canonical tool facts (use if iteration limits or model output are messy). ===\n",
                flush=True,
            )
    flush()
