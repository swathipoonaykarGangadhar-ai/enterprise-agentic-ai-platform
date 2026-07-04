import asyncio
from src.agents.streaming_runner import stream_mcp_agent

async def main():
    async for chunk in stream_mcp_agent(
        "src.mcp_servers.knowledge_server",
        "What is our vacation policy?",
        "You are a helpful knowledge agent.",
        "test-trace",
    ):
        print(chunk, end="", flush=True)
    print()

asyncio.run(main())