"""Stub MCP server for document analysis."""

import asyncio
import json
from mcp.server import Server
from mcp.types import TextContent

server = Server("document-analyzer")


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "analyze_document":
        content = arguments.get("content", "")
        summary = content[:200] + "..." if len(content) > 200 else content
        return [TextContent(type="text", text=json.dumps({"summary": summary}))]

    return [TextContent(type="text", text="Unsupported tool call")]


if __name__ == "__main__":
    asyncio.run(server.run())
