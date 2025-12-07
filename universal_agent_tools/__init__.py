"""Shared utilities for Universal Agent examples."""

from .model_config import ModelConfig, ModelProvider
from .ollama_tools import (
    MCPTool,
    MCPToolLoader,
    create_llm_with_tools,
    parse_tool_calls_from_content,
)

# Try to import observability helper (may not be available in all environments)
try:
    from .observability_helper import setup_observability, trace_runtime_execution
    __all__ = [
        "ModelConfig",
        "ModelProvider",
        "MCPTool",
        "MCPToolLoader",
        "create_llm_with_tools",
        "parse_tool_calls_from_content",
        "setup_observability",
        "trace_runtime_execution",
    ]
except ImportError:
    __all__ = [
        "ModelConfig",
        "ModelProvider",
        "MCPTool",
        "MCPToolLoader",
        "create_llm_with_tools",
        "parse_tool_calls_from_content",
    ]
