"""
Streaming Agent Runner
=========================
Same tool-discovery and tool-call logic as mcp_agent_runner.py, but the
final answer generation streams tokens as they're produced instead of
waiting for the complete response. Used by the /ask-stream endpoint.
"""
from __future__ import annotations

import json
import os
from typing import AsyncGenerator

from groq import Groq
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from src.common.config import settings
from src.common.logging import get_logger
from src.governance.guardrails import GuardrailViolation, check_tool_call

logger = get_logger("agents.streaming_runner")
groq_client = Groq(api_key=settings.groq_api_key)


async def stream_mcp_agent(
    server_module: str,
    user_question: str,
    system_prompt: str | None,
    trace_id: str,
) -> AsyncGenerator[dict, None]:
    """Yield answer text chunks as they're generated."""
    server_params = StdioServerParameters(
        command="python", args=["-m", server_module], env=os.environ.copy()
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

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_question})

            choice = None
            last_error = None
            for attempt in range(5):
                try:
                    response = groq_client.chat.completions.create(
                        model=settings.groq_model,
                        messages=messages,
                        tools=tools,
                        tool_choice="auto",
                    )
                    choice = response.choices[0].message
                    break
                except Exception as e:
                    last_error = e
                    logger.warning("groq_call_failed_retrying", attempt=attempt + 1, error=str(e))
            if choice is None:
                yield {"type": "chunk", "text": "Sorry, something went wrong reaching the model."}
                return

            if choice.tool_calls:
                messages.append({
                    "role": "assistant",
                    "content": choice.content or "",
                    "tool_calls": [
                        {"id": tc.id, "type": "function",
                         "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                        for tc in choice.tool_calls
                    ],
                })
                for call in choice.tool_calls:
                    args = json.loads(call.function.arguments)
                    logger.info("agent_calling_tool", server=server_module, tool=call.function.name, args=args)
                    yield {"type": "tool_call", "tool": call.function.name, "args": args}
                    try:
                        check_tool_call(call.function.name, args, trace_id)
                        result = await session.call_tool(call.function.name, args)
                        result_text = result.content[0].text if result.content else ""
                        yield {"type": "tool_result", "tool": call.function.name}
                    except GuardrailViolation as e:
                        result_text = f"BLOCKED BY GOVERNANCE POLICY: {e}"
                        yield {"type": "tool_blocked", "tool": call.function.name}
                    messages.append({"role": "tool", "tool_call_id": call.id, "content": result_text})

                stream = groq_client.chat.completions.create(
                    model=settings.groq_model,
                    messages=messages,
                    stream=True,
                )
                for chunk in stream:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield {"type": "chunk", "text": delta}
            else:
                if choice.content:
                    yield {"type": "chunk", "text": choice.content}