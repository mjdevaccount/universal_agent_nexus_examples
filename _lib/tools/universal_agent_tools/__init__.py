"""
Tools Module - Backward Compatibility Shim

⚠️ DEPRECATED: This module is deprecated and will be removed in Q2 2026.
Tools have been promoted to universal-agent-tools@1.1.0

Please update your imports:

Old (deprecated):
    from _lib.tools.universal_agent_tools.observability_helper import setup_observability
    from _lib.tools.universal_agent_tools.model_config import ModelConfig

New (recommended):
    from universal_agent_tools.observability import setup_observability
    from universal_agent_tools import ModelConfig
"""

import warnings

warnings.warn(
    "_lib.tools.universal_agent_tools is deprecated. "
    "Use 'from universal_agent_tools import ...' instead. "
    "This shim will be removed in Q2 2026. "
    "Requires universal-agent-tools>=1.1.0",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from promoted package
try:
    from universal_agent_tools import (
        ModelConfig,
        ModelProvider,
        setup_observability,
        trace_runtime_execution,
    )
except ImportError as e:
    # Try alternative import paths
    try:
        from universal_agent_tools.model_config import ModelConfig, ModelProvider
        from universal_agent_tools.observability import setup_observability, trace_runtime_execution
    except ImportError:
        raise ImportError(
            f"universal-agent-tools>=1.1.0 is required. "
            f"Install with: pip install 'universal-agent-tools>=1.1.0'. "
            f"Original error: {e}"
        )

try:
    from universal_agent_tools.ollama_tools import (
        MCPTool,
        MCPToolLoader,
        create_llm_with_tools,
        parse_tool_calls_from_content,
    )
except ImportError:
    # Ollama tools might not be available, that's okay
    MCPTool = None
    MCPToolLoader = None
    create_llm_with_tools = None
    parse_tool_calls_from_content = None

# Backward compatibility aliases
observability_helper = None  # Module replaced by observability
model_config = ModelConfig  # Direct re-export

__all__ = [
    "ModelConfig",
    "ModelProvider",
    "setup_observability",
    "trace_runtime_execution",
    "MCPTool",
    "MCPToolLoader",
    "create_llm_with_tools",
    "parse_tool_calls_from_content",
    "observability_helper",  # For backward compat
    "model_config",  # For backward compat
]
