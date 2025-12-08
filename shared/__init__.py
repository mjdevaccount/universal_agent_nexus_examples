"""Shared utilities for Universal Agent Nexus examples."""

from .cache_fabric import (
    CacheFabric,
    ContextScope,
    ContextEntry,
    InMemoryFabric,
    RedisFabric,
    VectorFabric,
    create_cache_fabric,
)

# Integration helpers
from .cache_fabric.nexus_integration import (
    store_manifest_contexts,
    get_router_prompt_from_fabric,
)

from .cache_fabric.runtime_integration import (
    FabricAwareRuntime,
    track_execution_with_fabric,
    record_feedback_to_fabric,
)

# Runtime base classes
from .runtime_base import (
    NexusRuntime,
    ResultExtractor,
    MessagesStateExtractor,
    ClassificationExtractor,
    JSONExtractor,
)

# Standard integration
from .standard_integration import StandardExample

# Output parsers
from .output_parsers import (
    get_parser,
    OutputParser,
    ParserResult,
    ClassificationParser,
    SentimentParser,
    ExtractionParser,
    BooleanParser,
    RegexParser,
)

__all__ = [
    # Core
    "CacheFabric",
    "ContextScope",
    "ContextEntry",
    # Backends
    "InMemoryFabric",
    "RedisFabric",
    "VectorFabric",
    # Factory
    "create_cache_fabric",
    # Nexus Integration
    "store_manifest_contexts",
    "get_router_prompt_from_fabric",
    # Runtime Integration
    "FabricAwareRuntime",
    "track_execution_with_fabric",
    "record_feedback_to_fabric",
    # Runtime Base
    "NexusRuntime",
    "ResultExtractor",
    "MessagesStateExtractor",
    "ClassificationExtractor",
    "JSONExtractor",
    # Standard Integration
    "StandardExample",
    # Output Parsers
    "get_parser",
    "OutputParser",
    "ParserResult",
    "ClassificationParser",
    "SentimentParser",
    "ExtractionParser",
    "BooleanParser",
    "RegexParser",
]

