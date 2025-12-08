"""
⚠️ DEPRECATED: This module has been deprecated.

Please update your imports to use the new package locations:

Old: from shared import NexusRuntime
New: from universal_agent_nexus.runtime import NexusRuntime

Old: from shared import create_cache_fabric
New: from universal_agent_nexus.cache_fabric import create_cache_fabric

Old: from shared import get_parser
New: from universal_agent_nexus.output_parsers import get_parser

Old: from shared import setup_observability
New: from universal_agent_tools.observability import setup_observability
"""

import warnings

warnings.warn(
    "shared module is deprecated. "
    "Please update imports to use universal_agent_nexus and universal_agent_tools packages directly. "
    "See module docstring for migration guide.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new package locations
try:
    from universal_agent_nexus.runtime import NexusRuntime, StandardExample, ResultExtractor
    from universal_agent_nexus.cache_fabric import CacheFabric, create_cache_fabric
    from universal_agent_nexus.output_parsers import get_parser, OutputParser
    from universal_agent_tools import ModelConfig
    from universal_agent_tools.observability import setup_observability
    
    __all__ = [
        "NexusRuntime",
        "StandardExample",
        "ResultExtractor",
        "CacheFabric",
        "create_cache_fabric",
        "get_parser",
        "OutputParser",
        "ModelConfig",
        "setup_observability",
    ]
except ImportError as e:
    import warnings
    warnings.warn(
        f"Failed to import from new packages: {e}. "
        "Please update imports to use universal_agent_nexus and universal_agent_tools directly.",
        DeprecationWarning
    )
    __all__ = []
