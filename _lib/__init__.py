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
from .tools.universal_agent_tools import ModelConfig, setup_observability

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

