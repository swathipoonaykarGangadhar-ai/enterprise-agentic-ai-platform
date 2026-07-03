"""
FastAPI Server
================
Wraps the supervisor in a persistent HTTP API, so the platform runs as
a real long-lived service instead of a one-shot script. This is what
lets Kubernetes properly manage it (health checks, restarts, scaling)
and what a frontend or other systems would actually call.

Run it directly (for local testing):
    uvicorn src.api.main:app --host 0.0.0.0 --port 8000

Endpoints:
    GET  /health          - liveness/readiness check for Kubernetes
    POST /ask              - ask the platform a question
"""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from src.common.logging import configure_logging, get_logger
from src.orchestration.supervisor import route

configure_logging()
logger = get_logger("api.main")

app = FastAPI(
    title="Enterprise Agentic AI Platform",
    description="MCP + GraphRAG + Multi-Agent Orchestration + Governance",
    version="1.0.0",
)


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str


@app.get("/health")
def health() -> dict:
    """Kubernetes liveness/readiness probe target."""
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest) -> AskResponse:
    """Ask the platform a question; it routes to the right agent and
    returns a governed, audited answer."""
    logger.info("api_request_received", question=request.question)
    answer = await route(request.question)
    return AskResponse(answer=answer)