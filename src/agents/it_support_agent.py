"""
IT Support Agent
==================
Specialist agent for IT support questions (ticket status, service
restarts). Thin wrapper around mcp_agent_runner.

Run it directly:
    python -m src.agents.it_support_agent "What's the status of TICKET-101?"
"""
from __future__ import annotations

import asyncio
import sys

from src.agents.mcp_agent_runner import run_mcp_agent
from src.common.logging import configure_logging

configure_logging()

SYSTEM_PROMPT = (
    "You are the IT Support Agent for an enterprise platform. You answer "
    "questions about ticket status and can restart internal services "
    "using the check_ticket_status and restart_service tools."
)


async def run(question: str, trace_id: str = "no-trace") -> str:
    return await run_mcp_agent(
        server_module="src.mcp_servers.it_support_server",
        user_question=question,
        system_prompt=SYSTEM_PROMPT,
        trace_id=trace_id,
    )


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What's the status of TICKET-101?"
    answer = asyncio.run(run(question))
    print("\n=== ANSWER ===")
    print(answer)