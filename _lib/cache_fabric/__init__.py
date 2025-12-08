"""
Cache Fabric Module - Backward Compatibility Shim

⚠️ DEPRECATED: This module is deprecated and will be removed in Q2 2026.
Cache Fabric has been promoted to universal-agent-nexus@3.1.0

Please update your imports:

Old (deprecated):
    from _lib.cache_fabric import create_cache_fabric

New (recommended):
    from universal_agent_nexus.cache_fabric import create_cache_fabric
"""

import warnings

warnings.warn(
    "_lib.cache_fabric is deprecated. "
    "Use 'from universal_agent_nexus.cache_fabric import ...' instead. "
    "This shim will be removed in Q2 2026. "
    "Requires universal-agent-nexus>=3.1.0",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from promoted package
try:
    from universal_agent_nexus.cache_fabric import (
        CacheFabric,
        ContextScope,
        ContextEntry,
        InMemoryFabric,
        RedisFabric,
        VectorFabric,
        create_cache_fabric,
        resolve_fabric_from_env,
    )
    from universal_agent_nexus.cache_fabric.nexus_integration import (
        store_manifest_contexts,
        get_router_prompt_from_fabric,
    )
    from universal_agent_nexus.cache_fabric.runtime_integration import (
        track_execution_with_fabric,
        record_feedback_to_fabric,
    )
except ImportError:
    raise ImportError(
        "universal-agent-nexus>=3.1.0 is required. "
        "Install with: pip install 'universal-agent-nexus>=3.1.0'"
    )

__all__ = [
    "CacheFabric",
    "ContextScope",
    "ContextEntry",
    "InMemoryFabric",
    "RedisFabric",
    "VectorFabric",
    "create_cache_fabric",
    "resolve_fabric_from_env",
    "store_manifest_contexts",
    "get_router_prompt_from_fabric",
    "track_execution_with_fabric",
    "record_feedback_to_fabric",
]
