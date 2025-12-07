"""Ollama integration helpers shared across examples."""

from importlib import import_module, util
import json
import re
from typing import Any

import httpx
from langchain_core.tools import BaseTool


def _import_optional(module_name: str, attr_name: str):
    """Import an attribute if the module exists, otherwise return ``None``."""

    if util.find_spec(module_name) is None:
        return None

    module = import_module(module_name)
    return getattr(module, attr_name, None)


class MCPToolLoader:
    """Load tools from MCP servers using standardized introspection."""

    @staticmethod
    def load_from_server(server_url: str) -> list[BaseTool]:
        """Load tools from an MCP server via introspection."""

        try:
            response = httpx.get(f"{server_url}/tools", timeout=5)
            response.raise_for_status()

            tools_data = response.json()
            tools: list[BaseTool] = []

            for tool_def in tools_data.get("tools", []):
                tool = MCPTool(
                    server_url=server_url,
                    tool_name=tool_def["name"],
                    input_schema=tool_def.get("inputSchema", {}),
                    name=tool_def["name"],
                    description=tool_def.get("description", ""),
                )
                tools.append(tool)

            return tools
        except Exception as exc:  # noqa: BLE001
            print(f"Warning: Could not load tools from {server_url}: {exc}")
            return []


class MCPTool(BaseTool):
    """LangChain tool wrapper for MCP tools."""

    def __init__(self, server_url: str, tool_name: str, input_schema: dict, name: str | None = None, description: str = ""):
        from pydantic import create_model

        args_schema = None
        if input_schema and input_schema.get("properties"):
            fields: dict[str, tuple[type[Any], Any]] = {}
            for prop_name, prop_def in input_schema.get("properties", {}).items():
                prop_type: type[Any] = str
                if prop_def.get("type") == "integer":
                    prop_type = int
                elif prop_def.get("type") == "boolean":
                    prop_type = bool
                fields[prop_name] = (prop_type, ...)

            if fields:
                args_schema = create_model(f"{tool_name}_Args", **fields)

        super().__init__(name=name or tool_name, description=description, args_schema=args_schema)

        object.__setattr__(self, "_server_url", server_url)
        object.__setattr__(self, "_tool_name", tool_name)
        object.__setattr__(self, "_input_schema", input_schema)

    def _run(self, **kwargs) -> str:
        try:
            response = httpx.post(
                f"{self._server_url}/tools/{self._tool_name}",
                json=kwargs,
                timeout=10,
            )
            response.raise_for_status()
            result = response.json()
            return result.get("content", str(result))
        except Exception as exc:  # noqa: BLE001
            return f"Error executing tool: {exc}"

    async def _arun(self, **kwargs) -> str:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self._server_url}/tools/{self._tool_name}",
                    json=kwargs,
                    timeout=10,
                )
                response.raise_for_status()
                result = response.json()
                return result.get("content", str(result))
            except Exception as exc:  # noqa: BLE001
                return f"Error executing tool: {exc}"


def create_llm_with_tools(tools: list[BaseTool], model: str = "qwen3"):
    """Create an LLM client configured for Ollama tool calling."""

    chat_openai_cls = _import_optional("langchain_openai", "ChatOpenAI")
    chat_ollama_cls = _import_optional("langchain_ollama", "ChatOllama")

    llm = None
    if chat_openai_cls is not None:
        llm = chat_openai_cls(
            model=model,
            base_url="http://localhost:11434/v1",
            api_key="ollama",
            temperature=0,
        )
    elif chat_ollama_cls is not None:
        llm = chat_ollama_cls(model=model, temperature=0)

    if llm is None:
        print("❌ ERROR: No supported LLM client installed (langchain-openai or langchain-ollama)")
        return None, tools

    if tools:
        try:
            llm_with_tools = llm.bind_tools(tools)
            print(f"✅ Tools bound successfully to {model}")
            return llm_with_tools, tools
        except Exception as exc:  # noqa: BLE001
            print(f"⚠️  Warning: bind_tools failed: {exc}")
            print("   Using LLM without tool binding (manual tool calling)")
            return llm, tools

    return llm, []


def parse_tool_calls_from_content(content: str, tools: list[BaseTool]) -> list[dict[str, Any]]:
    """Parse tool calls when an LLM returns them inside the content field."""

    if not content or not isinstance(content, str):
        return []

    try:
        tool_call_data = json.loads(content.strip())
        if isinstance(tool_call_data, dict) and "name" in tool_call_data:
            tool_name = tool_call_data.get("name")
            tool_args = tool_call_data.get("arguments", {})
            tool = next((tool for tool in tools if tool.name == tool_name), None)
            if tool:
                return [
                    {
                        "name": tool_name,
                        "args": tool_args,
                        "id": f"call_{tool_name}_{hash(str(tool_args))}",
                    }
                ]
    except (json.JSONDecodeError, AttributeError):
        pass

    json_match = re.search(r"\{[^{}]*\"name\"[^{}]*\}", content)
    if json_match:
        try:
            tool_call_data = json.loads(json_match.group(0))
            if isinstance(tool_call_data, dict) and "name" in tool_call_data:
                tool_name = tool_call_data.get("name")
                tool_args = tool_call_data.get("arguments", {})
                tool = next((tool for tool in tools if tool.name == tool_name), None)
                if tool:
                    return [
                        {
                            "name": tool_name,
                            "args": tool_args,
                            "id": f"call_{tool_name}_{hash(str(tool_args))}",
                        }
                    ]
        except (json.JSONDecodeError, AttributeError):
            pass

    return []


__all__ = [
    "MCPToolLoader",
    "MCPTool",
    "create_llm_with_tools",
    "parse_tool_calls_from_content",
]
