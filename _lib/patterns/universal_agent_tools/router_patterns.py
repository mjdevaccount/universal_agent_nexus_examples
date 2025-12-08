"""
Backward compatibility shim for router_patterns.

⚠️ DEPRECATED: This module is deprecated and will be removed in Q2 2026.
Please update your imports to use the new package location.

Old (deprecated):
    from _lib.patterns.universal_agent_tools import RouteDefinition

New (recommended):
    from universal_agent_tools.patterns import RouteDefinition
"""

import warnings

warnings.warn(
    "_lib.patterns.universal_agent_tools.router_patterns is deprecated. "
    "Use 'from universal_agent_tools.patterns import RouteDefinition, build_decision_agent_manifest' instead. "
    "This shim will be removed in Q2 2026.",
    DeprecationWarning,
    stacklevel=2
)

from universal_agent_tools.patterns.router import RouteDefinition, build_decision_agent_manifest

__all__ = ["RouteDefinition", "build_decision_agent_manifest"]
