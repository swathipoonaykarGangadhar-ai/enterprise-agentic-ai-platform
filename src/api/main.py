"""
FastAPI Server
================
Wraps the supervisor in a persistent HTTP API and exposes dashboard
endpoints for the audit log, evaluation results, and agent registry.
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

from src.common.logging import configure_logging, get_logger
from src.orchestration.supervisor import AGENTS, route

configure_logging()
logger = get_logger("api.main")

app = FastAPI(
    title="Enterprise Agentic AI Platform",
    description="MCP + GraphRAG + Multi-Agent Orchestration + Governance",
    version="1.0.0",
)

# Allow the React dev server (different port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest) -> AskResponse:
    logger.info("api_request_received", question=request.question)
    try:
        answer = await route(request.question)
    except Exception as e:
        logger.error("ask_failed", error=str(e))
        answer = "Sorry, something went wrong processing that question. Please try again."
    return AskResponse(answer=answer)


@app.post("/ask-stream")
async def ask_stream(request: AskRequest):
    """Same as /ask, but streams the final answer token-by-token via SSE."""
    from src.agents import it_support_agent, knowledge_agent
    from src.governance.audit import new_trace_id, record_event
    from src.governance.pii import redact_pii
    from src.orchestration.supervisor import _classify
    from src.agents.streaming_runner import stream_mcp_agent

    trace_id = new_trace_id()
    question = request.question
    redacted_question, pii_found = redact_pii(question)

    agent_name = _classify(question)
    record_event(
        trace_id=trace_id,
        event_type="routing_decision",
        agent="supervisor",
        detail={"question": redacted_question, "routed_to": agent_name, "pii_detected": pii_found},
    )

    if agent_name == "it_support":
        server_module = "src.mcp_servers.it_support_server"
        system_prompt = it_support_agent.SYSTEM_PROMPT
    else:
        server_module = "src.mcp_servers.knowledge_server"
        system_prompt = knowledge_agent.SYSTEM_PROMPT

    async def event_stream():
        full_answer = ""
        async for chunk in stream_mcp_agent(server_module, question, system_prompt, trace_id):
            full_answer += chunk
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"

        redacted_answer, answer_pii = redact_pii(full_answer)
        record_event(
            trace_id=trace_id,
            event_type="final_answer",
            agent=agent_name,
            detail={"answer": redacted_answer, "pii_detected": answer_pii},
        )
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")




@app.get("/audit-log")
def audit_log(limit: int = 50) -> list[dict]:
    """Return the most recent audit log entries, newest first."""
    path = Path("audit_log.jsonl")
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    entries = [json.loads(line) for line in lines if line.strip()]
    return list(reversed(entries))[:limit]


@app.get("/agents")
def agents() -> list[dict]:
    """Return the registered agents and what they handle."""
    return [
        {"name": name, "description": info["description"]}
        for name, info in AGENTS.items()
    ]


@app.get("/eval-results")
async def eval_results() -> dict:
    """Run the full evaluation suite live and return results as JSON.
    Each case is isolated — one failing case is reported as a failure,
    not allowed to crash the whole endpoint."""
    from src.evaluation.dataset import EVAL_CASES
    from src.evaluation.judge import judge_answer

    results = []
    for case in EVAL_CASES:
        try:
            answer = await route(case["question"])
            verdict = judge_answer(
                question=case["question"],
                answer=answer,
                expected_facts=case["expected_facts"],
            )
            results.append({
                "id": case["id"],
                "question": case["question"],
                "answer": answer,
                "passed": verdict["passed"],
                "reasoning": verdict["reasoning"],
            })
        except Exception as e:
            logger.error("eval_case_failed", case_id=case["id"], error=str(e))
            results.append({
                "id": case["id"],
                "question": case["question"],
                "answer": f"ERROR: {e}",
                "passed": False,
                "reasoning": "This case failed to run (see server logs).",
            })

    passed = sum(1 for r in results if r["passed"])
    return {"passed": passed, "total": len(results), "results": results}