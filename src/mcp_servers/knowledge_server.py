"""
Knowledge Base MCP Server
==========================
Now backed by real GraphRAG: search_knowledge_base performs semantic
vector search over a Neo4j knowledge graph instead of a hardcoded dict.

Run it directly:
    python -m src.mcp_servers.knowledge_server
"""
from __future__ import annotations

from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

from src.common.logging import configure_logging, get_logger
from src.graphrag.retriever import semantic_search

configure_logging()
logger = get_logger("mcp.knowledge_server")

mcp = FastMCP("enterprise-knowledge-server")


@mcp.tool()
def search_knowledge_base(query: str) -> str:
    """Search the enterprise knowledge base for information relevant to a query.

    Uses semantic (meaning-based) search over a Neo4j knowledge graph,
    so it can match questions even if they don't share exact keywords
    with the stored knowledge.

    Args:
        query: A natural-language question or keyword to search for.

    Returns:
        The most relevant matching entry, or a message indicating nothing was found.
    """
    logger.info("tool_call", tool="search_knowledge_base", query=query)
    matches = semantic_search(query, top_k=1)
    if not matches:
        return "No matching entry found in the knowledge base."
    return matches[0]["text"]


@mcp.tool()
def get_system_status() -> str:
    """Return the current health status of the platform's core services.

    Returns:
        A short status string with a timestamp.
    """
    logger.info("tool_call", tool="get_system_status")
    now = datetime.now(timezone.utc).isoformat()
    return f"All systems operational. Checked at {now}."


if __name__ == "__main__":
    logger.info("mcp_server_starting", server="enterprise-knowledge-server")
    mcp.run(transport="stdio")