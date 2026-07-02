"""
Knowledge Agent
================
The first real agent in the platform. It:
  1. Starts the knowledge_server MCP server as a subprocess
  2. Connects to it as an MCP client and discovers its tools
  3. Sends the user's question + tool list to Groq's LLM
  4. If the LLM decides to call a tool, actually executes it against
     the real MCP server and feeds the result back to the LLM
  5. Returns the LLM's final, informed answer

Run it directly:
    python -m src.agents.knowledge_agent "What is our vacation policy?"
"""
from __future__ import annotations

import asyncio
import json
import sys

from groq import Groq
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from src.common.config import settings
from src.common.logging import configure_logging, get_logger

configure_logging()
logger = get_logger("agents.knowledge_agent")

groq_client = Groq(api_key=settings.groq_api_key)

SERVER_PARAMS = StdioServerParameters(
    command="python",
    args=["-m", "src.mcp_servers.knowledge_server"],
)


async def run_agent(user_question: str) -> str:
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Step 1: discover what tools this MCP server offers
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
                tools=[t["function"]["name"] for t in tools],
            )

            messages = [{"role": "user", "content": user_question}]

            # Step 2: ask Groq what to do, giving it the tool menu
            response = groq_client.chat.completions.create(
                model=settings.groq_model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
            choice = response.choices[0].message

            # Step 3: if the LLM wants to call a tool, actually call it
            if choice.tool_calls:
                assistant_message = {
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
                messages.append(assistant_message)

                for call in choice.tool_calls:
                    args = json.loads(call.function.arguments)
                    logger.info(
                        "agent_calling_tool",
                        tool=call.function.name,
                        args=args,
                    )
                    result = await session.call_tool(call.function.name, args)
                    result_text = result.content[0].text if result.content else ""
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.id,
                            "content": result_text,
                        }
                    )

                # Step 4: give the LLM the real tool result, get a final answer
                final = groq_client.chat.completions.create(
                    model=settings.groq_model,
                    messages=messages,
                )
                return final.choices[0].message.content

            # LLM answered directly without needing a tool
            return choice.content


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What is our vacation policy?"
    answer = asyncio.run(run_agent(question))
    print("\n=== ANSWER ===")
    print(answer)