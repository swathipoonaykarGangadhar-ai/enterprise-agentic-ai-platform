"""
Supervisor
===========
The multi-agent orchestrator. Given a user question, it asks Groq to
classify which specialist agent should handle it, then routes the
question to that agent and returns its answer.

This is a simple "router" pattern — the most common, production-proven
starting point for multi-agent orchestration before adding more complex
patterns (parallel agents, hand-offs, shared memory, etc).

Run it directly:
    python -m src.orchestration.supervisor "What's the status of TICKET-101?"
"""
from __future__ import annotations

import asyncio
import sys

from groq import Groq

from src.agents import it_support_agent, knowledge_agent
from src.common.config import settings
from src.common.logging import configure_logging, get_logger

configure_logging()
logger = get_logger("orchestration.supervisor")

groq_client = Groq(api_key=settings.groq_api_key)

AGENTS = {
    "knowledge": {
        "description": (
            "Handles company policy, HR, onboarding, and internal "
            "procedure questions."
        ),
        "run": knowledge_agent.run,
    },
    "it_support": {
        "description": (
            "Handles IT support ticket status lookups and service "
            "restarts."
        ),
        "run": it_support_agent.run,
    },
}


def _classify(question: str) -> str:
    """Ask Groq which agent should handle this question."""
    agent_list = "\n".join(
        f"- {name}: {info['description']}" for name, info in AGENTS.items()
    )
    prompt = (
        "You are a routing supervisor. Given the user question below, "
        "respond with ONLY the single best agent name from this list "
        "(no explanation, just the name):\n\n"
        f"{agent_list}\n\n"
        f"User question: {question}\n\n"
        "Agent name:"
    )
    response = groq_client.chat.completions.create(
        model=settings.groq_model,
        messages=[{"role": "user", "content": prompt}],
    )
    choice = response.choices[0].message.content.strip().lower()
    for name in AGENTS:
        if name in choice:
            return name
    logger.warning("classification_fallback", raw_response=choice)
    return "knowledge"  # safe default


async def route(question: str) -> str:
    agent_name = _classify(question)
    logger.info("routing_decision", question=question, routed_to=agent_name)
    agent_fn = AGENTS[agent_name]["run"]
    return await agent_fn(question)


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What's the status of TICKET-101?"
    answer = asyncio.run(route(question))
    print("\n=== FINAL ANSWER ===")
    print(answer)