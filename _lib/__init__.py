"""
Experimental Abstractions Library

⚠️ INTERIM LOCATION - TO BE PROMOTED

This package contains abstractions being validated through examples
before promotion to production packages.

See _lib/README.md for promotion path and status.
"""

# Re-export for backward compatibility during transition
from .runtime import NexusRuntime, StandardExample, ResultExtractor
from .cache_fabric import CacheFabric, create_cache_fabric
from .output_parsers import get_parser, OutputParser
# Tools import is optional (may not be installed)
try:
    from .tools.universal_agent_tools import ModelConfig, setup_observability
except ImportError:
    # Tools not available, that's okay
    ModelConfig = None
    setup_observability = None

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

