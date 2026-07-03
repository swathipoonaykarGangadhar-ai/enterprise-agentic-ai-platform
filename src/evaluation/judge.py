"""
LLM-as-Judge
==============
Uses Groq's LLM to evaluate whether an agent's answer correctly contains
the expected facts for a test case. This is the standard "LLM-as-judge"
pattern used in production eval pipelines, since exact string matching
is too brittle for natural-language answers.
"""
from __future__ import annotations

from groq import Groq

from src.common.config import settings
from src.common.logging import get_logger

logger = get_logger("evaluation.judge")

groq_client = Groq(api_key=settings.groq_api_key)


def judge_answer(question: str, answer: str, expected_facts: list[str]) -> dict:
    """Ask the LLM to judge whether an answer covers the expected facts.

    Returns:
        {"passed": bool, "reasoning": str}
    """
    facts_list = "\n".join(f"- {fact}" for fact in expected_facts)
    prompt = (
        "You are grading an AI agent's answer for correctness.\n\n"
        f"Question asked: {question}\n\n"
        f"Agent's answer: {answer}\n\n"
        f"Facts that MUST be present (in meaning, not exact wording) "
        f"for the answer to be correct:\n{facts_list}\n\n"
        "Respond in EXACTLY this format:\n"
        "PASS or FAIL\n"
        "Then a one-sentence reason.\n"
    )
    response = groq_client.chat.completions.create(
        model=settings.groq_model,
        messages=[{"role": "user", "content": prompt}],
    )
    content = response.choices[0].message.content.strip()
    passed = content.upper().startswith("PASS")
    return {"passed": passed, "reasoning": content}