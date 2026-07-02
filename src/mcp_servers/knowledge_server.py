"""
Knowledge Base MCP Server
==========================
The platform's first MCP server. Exposes tools over the Model Context
Protocol that any MCP-compatible client (our agents, Claude Desktop,
Claude Code) can discover and call.

Uses an in-memory stub knowledge base for now. In the GraphRAG step
we swap the stub for real Neo4j-backed retrieval — tool signatures
agents call will not change, only what's inside them.

Run it directly:
    python -m src.mcp_servers.knowledge_server
"""
from __future__ import annotations

from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

from src.common.logging import configure_logging, get_logger

configure_logging()
logger = get_logger("mcp.knowledge_server")

mcp = FastMCP("enterprise-knowledge-server")

_KNOWLEDGE_BASE = {
    "onboarding": "New employees complete IT setup, HR paperwork, and a "
                  "security training within their first 5 business days.",
    "vacation_policy": "Full-time employees accrue 15 PTO days per year, "
                        "accrued monthly and capped at 30 days banked.",
    "incident_response": "Security incidents must be reported to the SOC "
                          "within 1 hour of detection via the #incidents channel.",
}


@mcp.tool()
def search_knowledge_base(query: str) -> str:
    """Search the enterprise knowledge base for information relevant to a query.

    Args:
        query: A natural-language question or keyword to search for.

    Returns:
        The most relevant matching entry, or a message indicating nothing was found.
    """
    logger.info("tool_call", tool="search_knowledge_base", query=query)
    query_lower = query.lower()
    for key, value in _KNOWLEDGE_BASE.items():
        if key.replace("_", " ") in query_lower or any(
            word in query_lower for word in key.split("_")
        ):
            return value
    return "No matching entry found in the knowledge base."


@mcp.tool()
def get_system_status() -> str:
    """Return the current health status of the platform's core services.

    Returns:
        A short status string with a timestamp.
    """
    logger.info("tool_call", tool="get_system_status")
    now = datetime.now(timezone.utc).isoformat()
    return f"All systems operational. Checked at {now}."


@mcp.resource("knowledge://topics")
def list_topics() -> str:
    """Expose the list of available knowledge base topics as an MCP resource."""
    return "\n".join(_KNOWLEDGE_BASE.keys())


if __name__ == "__main__":
    logger.info("mcp_server_starting", server="enterprise-knowledge-server")
    mcp.run(transport="stdio")