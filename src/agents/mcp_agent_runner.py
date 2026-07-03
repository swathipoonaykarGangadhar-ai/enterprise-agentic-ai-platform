"""
Shared MCP Agent Runner
=========================
Reusable logic for "connect to one MCP server as a client, let Groq decide
whether to call its tools, execute tool calls, return a final answer."

Both knowledge_agent.py and it_support_agent.py are now thin wrappers
around this function, pointed at their own MCP server. This avoids
duplicating the tool-discovery / tool-call loop in every agent file.
"""
from __future__ import annotations

import json

from groq import Groq
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from src.common.config import settings
from src.common.logging import get_logger
from src.governance.guardrails import GuardrailViolation, check_tool_call

logger = get_logger("agents.mcp_agent_runner")

groq_client = Groq(api_key=settings.groq_api_key)


async def run_mcp_agent(
    server_module: str,
    user_question: str,
    system_prompt: str | None = None,
    trace_id: str = "no-trace",
) -> str:
    """Run a single question through an MCP-tool-using agent.

    Args:
        server_module: Python module path to run as the MCP server,
            e.g. "src.mcp_servers.knowledge_server".
        user_question: The question to answer.
        system_prompt: Optional system prompt to steer this agent's behavior.

    Returns:
        The agent's final natural-language answer.
    """
    server_params = StdioServerParameters(
        command="python", args=["-m", server_module]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description or "",
                        "parameters": t.inputSchema,
                    },
                }
                for t in tools_result.tools
            ]
            logger.info(
                "tools_discovered",
                server=server_module,
                tools=[t["function"]["name"] for t in tools],
            )

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_question})

            response = groq_client.chat.completions.create(
                model=settings.groq_model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
            choice = response.choices[0].message

            if choice.tool_calls:
                messages.append(
                    {
                        "role": "assistant",
                        "content": choice.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in choice.tool_calls
                        ],
                    }
                )

                for call in choice.tool_calls:
                    args = json.loads(call.function.arguments)
                    logger.info(
                        "agent_calling_tool",
                        server=server_module,
                        tool=call.function.name,
                        args=args,
                    )

                    try:
                        check_tool_call(call.function.name, args, trace_id)
                        result = await session.call_tool(call.function.name, args)
                        result_text = (
                            result.content[0].text if result.content else ""
                        )
                    except GuardrailViolation as e:
                        result_text = f"BLOCKED BY GOVERNANCE POLICY: {e}"

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.id,
                            "content": result_text,
                        }
                    )

                final = groq_client.chat.completions.create(
                    model=settings.groq_model,
                    messages=messages,
                )
                return final.choices[0].message.content

            return choice.content