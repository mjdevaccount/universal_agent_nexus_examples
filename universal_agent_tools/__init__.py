"""Shared utilities for Universal Agent examples."""

from .model_config import ModelConfig, ModelProvider
from .ollama_tools import (
    MCPTool,
    MCPToolLoader,
    create_llm_with_tools,
    parse_tool_calls_from_content,
)

__all__ = [
    "ModelConfig",
    "ModelProvider",
    "MCPTool",
    "MCPToolLoader",
    "create_llm_with_tools",
    "parse_tool_calls_from_content",
]
