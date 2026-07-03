"""
Audit Trail
=============
Records every tool call made by any agent, with a unique trace ID so a
full request can be reconstructed after the fact. This is the backbone
of AI governance: nothing gets called without being logged.

In this stage we log to a local JSONL file (one JSON object per line) —
simple, human-readable, and easy to swap for a real database later
without changing the calling code.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.common.logging import get_logger

logger = get_logger("governance.audit")

AUDIT_LOG_PATH = Path("audit_log.jsonl")


def new_trace_id() -> str:
    """Generate a unique ID to tie together every event in one request."""
    return str(uuid.uuid4())


def record_event(
    trace_id: str,
    event_type: str,
    agent: str,
    detail: dict,
) -> None:
    """Append one audit event to the audit log.

    Args:
        trace_id: Shared ID linking all events in a single user request.
        event_type: e.g. "routing_decision", "tool_call", "final_answer".
        agent: Which agent/component generated this event.
        detail: Arbitrary structured detail about the event.
    """
    entry = {
        "trace_id": trace_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "agent": agent,
        "detail": detail,
    }
    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    logger.info("audit_event_recorded", trace_id=trace_id, event_type=event_type)