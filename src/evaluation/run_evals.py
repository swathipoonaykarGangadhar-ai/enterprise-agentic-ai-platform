"""
Evaluation Runner
====================
Runs every case in the eval dataset through the real supervisor
(agent routing + tool use), scores each answer with the LLM judge,
and prints a pass/fail report.

Run it directly:
    python -m src.evaluation.run_evals
"""
from __future__ import annotations

import asyncio

from src.common.logging import configure_logging, get_logger
from src.evaluation.dataset import EVAL_CASES
from src.evaluation.judge import judge_answer
from src.orchestration.supervisor import route

configure_logging()
logger = get_logger("evaluation.run_evals")


async def run_all_evals() -> None:
    results = []

    for case in EVAL_CASES:
        print(f"\nRunning: {case['id']}")
        answer = await route(case["question"])
        verdict = judge_answer(
            question=case["question"],
            answer=answer,
            expected_facts=case["expected_facts"],
        )
        results.append({**case, "answer": answer, **verdict})

        status = "✅ PASS" if verdict["passed"] else "❌ FAIL"
        print(f"  {status} — {verdict['reasoning']}")

    passed_count = sum(1 for r in results if r["passed"])
    total = len(results)
    print(f"\n{'=' * 50}")
    print(f"RESULTS: {passed_count}/{total} passed")
    print(f"{'=' * 50}")

    for r in results:
        if not r["passed"]:
            print(f"\nFAILED: {r['id']}")
            print(f"  Question: {r['question']}")
            print(f"  Answer:   {r['answer']}")
            print(f"  Reason:   {r['reasoning']}")


if __name__ == "__main__":
    asyncio.run(run_all_evals())