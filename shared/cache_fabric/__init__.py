"""Cache Fabric Layer - Communication between Nexus and Agent runtime."""

from .base import CacheFabric, ContextScope, ContextEntry
from .backends import InMemoryFabric, RedisFabric, VectorFabric
from .factory import create_cache_fabric

__all__ = [
    "CacheFabric",
    "ContextScope",
    "ContextEntry",
    "InMemoryFabric",
    "RedisFabric",
    "VectorFabric",
    "create_cache_fabric",
]

