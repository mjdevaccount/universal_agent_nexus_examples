"""
Tool Utilities

Promotion target: universal-agent-tools
"""

# Tools import is optional (may not be installed)
try:
    from .universal_agent_tools import (
        ModelConfig,
        ModelProvider,
        setup_observability,
        trace_runtime_execution,
        MCPTool,
        MCPToolLoader,
        create_llm_with_tools,
        parse_tool_calls_from_content,
    )
except ImportError:
    # Tools not available, that's okay
    ModelConfig = None
    ModelProvider = None
    setup_observability = None
    trace_runtime_execution = None
    MCPTool = None
    MCPToolLoader = None
    create_llm_with_tools = None
    parse_tool_calls_from_content = None

__all__ = [
    "ModelConfig",
    "ModelProvider",
    "setup_observability",
    "trace_runtime_execution",
    "MCPTool",
    "MCPToolLoader",
    "create_llm_with_tools",
    "parse_tool_calls_from_content",
]

