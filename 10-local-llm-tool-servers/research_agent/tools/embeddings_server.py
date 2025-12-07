"""Simple embeddings MCP server placeholder."""

import asyncio
import json

from mcp.server import Server
from mcp.types import TextContent

server = Server("embeddings-server")


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "embed_text":
        text = arguments.get("text", "")
        # Placeholder embedding: length-based vector
        embedding = [len(text)]
        return [TextContent(type="text", text=json.dumps({"embedding": embedding}))]

    return [TextContent(type="text", text="Unsupported tool call")]


if __name__ == "__main__":
    asyncio.run(server.run())
