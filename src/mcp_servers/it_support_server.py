"""
IT Support MCP Server
=======================
Second MCP server in the platform, specializing in IT support tasks.
Uses in-memory stubs for now — same pattern as knowledge_server.py.

Run it directly:
    python -m src.mcp_servers.it_support_server
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from src.common.logging import configure_logging, get_logger

configure_logging()
logger = get_logger("mcp.it_support_server")

mcp = FastMCP("enterprise-it-support-server")

_TICKETS = {
    "TICKET-101": "Open - assigned to network team - laptop won't connect to VPN",
    "TICKET-102": "Resolved - password reset completed",
    "TICKET-103": "In progress - awaiting hardware replacement for monitor",
}


@mcp.tool()
def check_ticket_status(ticket_id: str) -> str:
    """Look up the current status of an IT support ticket by its ID.

    Args:
        ticket_id: The ticket identifier, e.g. "TICKET-101".

    Returns:
        The ticket's current status, or a message if not found.
    """
    logger.info("tool_call", tool="check_ticket_status", ticket_id=ticket_id)
    return _TICKETS.get(
        ticket_id.upper(), f"No ticket found with ID '{ticket_id}'."
    )


@mcp.tool()
def restart_service(service_name: str) -> str:
    """Restart a named internal service (simulated).

    Args:
        service_name: The name of the service to restart, e.g. "auth-service".

    Returns:
        A confirmation message.
    """
    logger.info("tool_call", tool="restart_service", service_name=service_name)
    return f"Service '{service_name}' restart initiated successfully."


if __name__ == "__main__":
    logger.info("mcp_server_starting", server="enterprise-it-support-server")
    mcp.run(transport="stdio")