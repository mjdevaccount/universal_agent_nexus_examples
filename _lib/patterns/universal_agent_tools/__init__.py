"""
Patterns Module - Backward Compatibility Shim

⚠️ DEPRECATED: This module is deprecated and will be removed in Q2 2026.
Patterns have been promoted to universal-agent-tools@1.1.0

Please update your imports:

Old (deprecated):
    from _lib.patterns.universal_agent_tools import RouteDefinition
    from tools.universal_agent_tools import RouteDefinition

New (recommended):
    from universal_agent_tools.patterns import RouteDefinition
"""

import warnings

warnings.warn(
    "_lib.patterns.universal_agent_tools is deprecated. "
    "Use 'from universal_agent_tools.patterns import ...' instead. "
    "This shim will be removed in Q2 2026. "
    "Requires universal-agent-tools>=1.1.0",
    DeprecationWarning,
    stacklevel=2
)

# Re-export promoted patterns
try:
    from universal_agent_tools.patterns import (
        RouteDefinition,
        build_decision_agent_manifest,
        OrganizationAgentFactory,
        build_organization_manifest,
        TenantIsolationHandler,
        VectorDBIsolationHandler,
        create_tenant_agent,
        SelfModifyingAgent,
        deterministic_tool_from_error,
    )
except ImportError:
    raise ImportError(
        "universal-agent-tools>=1.1.0 is required. "
        "Install with: pip install 'universal-agent-tools>=1.1.0'"
    )

# Keep non-promoted modules available
from .dynamic_tools import DynamicCSVToolInjector, DynamicToolInjector
from .mcp_stub import DictToolServer, ToolHandler

__all__ = [
    # Promoted patterns (re-exported)
    "RouteDefinition",
    "build_decision_agent_manifest",
    "OrganizationAgentFactory",
    "build_organization_manifest",
    "TenantIsolationHandler",
    "VectorDBIsolationHandler",
    "create_tenant_agent",
    "SelfModifyingAgent",
    "deterministic_tool_from_error",
    # Non-promoted (still in _lib)
    "DynamicCSVToolInjector",
    "DynamicToolInjector",
    "DictToolServer",
    "ToolHandler",
]
