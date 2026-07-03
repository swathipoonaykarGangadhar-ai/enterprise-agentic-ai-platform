"""
Guardrails
============
Policy checks that can block a tool call before it executes. This is
the enforcement layer of governance — audit logging records what
happened, guardrails prevent certain things from happening at all.
"""
from __future__ import annotations

from src.common.logging import get_logger

logger = get_logger("governance.guardrails")

# Services that must never be restarted automatically by an agent
# without explicit human approval — a stand-in for real production
# safety rules.
PROTECTED_SERVICES = {"auth-service", "payment-service", "database-primary"}


class GuardrailViolation(Exception):
    """Raised when a requested action violates a governance policy."""


def check_tool_call(tool_name: str, args: dict, trace_id: str) -> None:
    """Raise GuardrailViolation if this tool call should be blocked.

    Args:
        tool_name: Name of the tool being called.
        args: Arguments being passed to the tool.
        trace_id: The request's trace ID, for logging.

    Raises:
        GuardrailViolation: if the call is not permitted.
    """
    if tool_name == "restart_service":
        service = args.get("service_name", "")
        if service in PROTECTED_SERVICES:
            logger.warning(
                "guardrail_blocked",
                trace_id=trace_id,
                tool=tool_name,
                service=service,
            )
            raise GuardrailViolation(
                f"Restarting '{service}' requires human approval and "
                f"cannot be performed by an autonomous agent."
            )