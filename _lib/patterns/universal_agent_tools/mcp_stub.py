"""Tiny, reusable helpers for quick MCP stub servers."""

import asyncio
import json
import inspect
from typing import Awaitable, Callable, Dict, Iterable, Union

from mcp.server import Server
from mcp.types import TextContent


ToolHandler = Callable[[dict], Union[str, dict, Iterable[str], Awaitable[Union[str, dict, Iterable[str]]]]]


class DictToolServer:
    """Dictionary-dispatched MCP server for lightweight demos.

    Example
    -------
    >>> server = DictToolServer(
    ...     name="billing-mcp",
    ...     tools={
    ...         "get_balance": lambda args: {"balance": 100.0},
    ...     },
    ... )
    >>> asyncio.run(server.run())
    """

    def __init__(self, name: str, tools: Dict[str, ToolHandler]):
        self.server = Server(name)
        self.tools = tools

        @self.server.call_tool()
        async def _dispatch(name: str, arguments: dict):
            handler = self.tools.get(name)
            if handler is None:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

            result = handler(arguments)
            if inspect.isawaitable(result):
                result = await result

            payload = self._normalize_result(result)
            return [TextContent(type="text", text=payload)]

    @staticmethod
    def _normalize_result(result: Union[str, dict, Iterable[str]]) -> str:
        if isinstance(result, str):
            return result
        if isinstance(result, dict):
            return json.dumps(result)
        if isinstance(result, Iterable):
            return "\n".join(str(item) for item in result)
        return json.dumps(result)

    async def run(self):
        async with self.server:
            await asyncio.Event().wait()

    def run_sync(self):
        asyncio.run(self.run())


__all__ = ["DictToolServer", "ToolHandler"]
