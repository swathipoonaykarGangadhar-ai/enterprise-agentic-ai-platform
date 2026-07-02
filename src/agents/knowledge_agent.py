"""
Knowledge Agent
================
Specialist agent for company knowledge base questions (HR policy,
onboarding, incident response). Thin wrapper around mcp_agent_runner.

Run it directly:
    python -m src.agents.knowledge_agent "What is our vacation policy?"
"""
from __future__ import annotations

import asyncio
import sys

from src.agents.mcp_agent_runner import run_mcp_agent
from src.common.logging import configure_logging

configure_logging()

SYSTEM_PROMPT = (
    "You are the Knowledge Agent for an enterprise platform. You answer "
    "questions about company policy, onboarding, and internal procedures "
    "using the search_knowledge_base and get_system_status tools."
)


async def run(question: str) -> str:
    return await run_mcp_agent(
        server_module="src.mcp_servers.knowledge_server",
        user_question=question,
        system_prompt=SYSTEM_PROMPT,
    )


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What is our vacation policy?"
    answer = asyncio.run(run(question))
    print("\n=== ANSWER ===")
    print(answer)