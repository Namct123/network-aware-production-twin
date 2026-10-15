"""End-to-end smoke test: start the stdio MCP server and call a read-only tool."""

from __future__ import annotations

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def smoke_test() -> None:
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "factoryio_mcp.server"],
    )
    async with stdio_client(parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            status = await session.call_tool("factoryio_status", {})
            print("tools:", [tool.name for tool in tools.tools])
            print("status:", status.structuredContent)


if __name__ == "__main__":
    asyncio.run(smoke_test())

