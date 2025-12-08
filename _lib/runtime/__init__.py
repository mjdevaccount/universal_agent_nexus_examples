"""
Runtime Module - Backward Compatibility Shim

⚠️ DEPRECATED: This module is deprecated and will be removed in Q2 2026.
Runtime modules have been promoted to universal-agent-nexus@3.1.0

Please update your imports:

Old (deprecated):
    from _lib.runtime import NexusRuntime, StandardExample

New (recommended):
    from universal_agent_nexus.runtime import NexusRuntime, StandardExample
"""

import warnings

warnings.warn(
    "_lib.runtime is deprecated. "
    "Use 'from universal_agent_nexus.runtime import ...' instead. "
    "This shim will be removed in Q2 2026. "
    "Requires universal-agent-nexus>=3.1.0",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from promoted package
try:
    from universal_agent_nexus.runtime import (
        NexusRuntime,
        StandardExample,
        ResultExtractor,
        MessagesStateExtractor,
        ClassificationExtractor,
        JSONExtractor,
        ToolRegistry,
        ToolDefinition,
        get_registry,
    )
except ImportError:
    raise ImportError(
        "universal-agent-nexus>=3.1.0 is required. "
        "Install with: pip install 'universal-agent-nexus>=3.1.0'"
    )

__all__ = [
    "NexusRuntime",
    "StandardExample",
    "ResultExtractor",
    "MessagesStateExtractor",
    "ClassificationExtractor",
    "JSONExtractor",
    "ToolRegistry",
    "ToolDefinition",
    "get_registry",
]
