"""
Supervisor
===========
The multi-agent orchestrator, now with governance built in: every
request gets a trace ID, every routing decision and final answer is
recorded to the audit log, and PII is redacted before logging.

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
from src.governance.audit import new_trace_id, record_event
from src.governance.pii import redact_pii

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
    return "knowledge"


async def route(question: str, trace_id: str | None = None) -> str:
    trace_id = trace_id or new_trace_id()

    redacted_question, pii_found = redact_pii(question)
    if pii_found:
        logger.warning("pii_detected_in_question", trace_id=trace_id, types=pii_found)

    agent_name = _classify(question)
    logger.info("routing_decision", question=redacted_question, routed_to=agent_name)
    record_event(
        trace_id=trace_id,
        event_type="routing_decision",
        agent="supervisor",
        detail={
            "question": redacted_question,
            "routed_to": agent_name,
            "pii_detected": pii_found,
        },
    )

    agent_fn = AGENTS[agent_name]["run"]
    answer = await agent_fn(question, trace_id=trace_id)

    redacted_answer, answer_pii = redact_pii(answer)
    record_event(
        trace_id=trace_id,
        event_type="final_answer",
        agent=agent_name,
        detail={
            "answer": redacted_answer,
            "pii_detected": answer_pii,
        },
    )

    return answer


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What's the status of TICKET-101?"
    answer = asyncio.run(route(question))
    print("\n=== FINAL ANSWER ===")
    print(answer)