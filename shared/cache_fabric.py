"""Cache Fabric Layer - Communication layer between Nexus compilation and Agent runtime.

This fabric enables:
- Live context evolution (system prompts, tool definitions)
- Semantic caching (LLM response caching)
- Execution state persistence
- Feedback loop integration
- Hot-reload capability without recompilation
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum


class ContextScope(Enum):
    """Scope for context entries."""
    GLOBAL = "global"  # Shared across all executions
    EXECUTION = "execution"  # Per-execution context
    TENANT = "tenant"  # Per-tenant context


class CacheFabric(ABC):
    """Abstract base class for Cache Fabric implementations.
    
    The Cache Fabric sits between Nexus (compilation) and Agent (runtime),
    enabling live context updates, semantic caching, and feedback loops.
    """
    
    @abstractmethod
    async def set_context(
        self,
        key: str,
        value: Any,
        scope: ContextScope = ContextScope.GLOBAL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Store context entry (system prompt, tool definition, etc.).
        
        Args:
            key: Context key (e.g., 'system_prompt', 'tool_definitions')
            value: Context value (string, dict, etc.)
            scope: Context scope (GLOBAL, EXECUTION, TENANT)
            metadata: Optional metadata (version, timestamp, etc.)
        
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def get_context(
        self,
        key: str,
        default: Any = None,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve context entry.
        
        Args:
            key: Context key
            default: Default value if not found
        
        Returns:
            Context entry dict with keys: key, value, scope, metadata, version, timestamp
        """
        pass
    
    @abstractmethod
    async def update_context(
        self,
        key: str,
        value: Any,
        merge: bool = False,
    ) -> bool:
        """Update existing context entry (increments version).
        
        Args:
            key: Context key
            value: New value
            merge: If True, merge with existing value (for dicts)
        
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def track_execution(
        self,
        execution_id: str,
        graph_name: str,
        state: Dict[str, Any],
    ) -> bool:
        """Track execution state for analysis and feedback.
        
        Args:
            execution_id: Unique execution identifier
            graph_name: Graph name
            state: Execution state (input, output, nodes executed, etc.)
        
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def record_feedback(
        self,
        execution_id: str,
        feedback: Dict[str, Any],
    ) -> bool:
        """Record feedback for an execution (for feedback loops).
        
        Args:
            execution_id: Execution identifier
            feedback: Feedback data (status, classification, user_rating, etc.)
        
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def get_metrics(self) -> Dict[str, Any]:
        """Get cache fabric metrics.
        
        Returns:
            Dict with: hit_rate, avg_latency, cost_saved, speedup, etc.
        """
        pass
    
    @abstractmethod
    async def search_similar(
        self,
        query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Semantic search for similar cached contexts (vector DB only).
        
        Args:
            query: Search query
            limit: Max results
        
        Returns:
            List of similar context entries
        """
        pass


class InMemoryFabric(CacheFabric):
    """In-memory Cache Fabric (for development/testing).
    
    Fast, no dependencies, but data lost on restart.
    """
    
    def __init__(self):
        self.contexts: Dict[str, Dict[str, Any]] = {}
        self.executions: List[Dict[str, Any]] = []
        self.feedback: List[Dict[str, Any]] = []
        self.metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "total_latency": 0,
            "latencies": [],
        }
        self._version_counter: Dict[str, int] = {}
    
    async def set_context(
        self,
        key: str,
        value: Any,
        scope: ContextScope = ContextScope.GLOBAL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        if key not in self._version_counter:
            self._version_counter[key] = 0
        self._version_counter[key] += 1
        
        self.contexts[key] = {
            "key": key,
            "value": value,
            "scope": scope.value,
            "metadata": metadata or {},
            "version": self._version_counter[key],
            "timestamp": datetime.utcnow().isoformat(),
        }
        return True
    
    async def get_context(
        self,
        key: str,
        default: Any = None,
    ) -> Optional[Dict[str, Any]]:
        entry = self.contexts.get(key)
        if entry:
            self.metrics["cache_hits"] += 1
            return entry
        return default
    
    async def update_context(
        self,
        key: str,
        value: Any,
        merge: bool = False,
    ) -> bool:
        if key not in self.contexts:
            return False
        
        if merge and isinstance(value, dict) and isinstance(self.contexts[key]["value"], dict):
            self.contexts[key]["value"] = {**self.contexts[key]["value"], **value}
        else:
            self.contexts[key]["value"] = value
        
        self._version_counter[key] += 1
        self.contexts[key]["version"] = self._version_counter[key]
        self.contexts[key]["timestamp"] = datetime.utcnow().isoformat()
        return True
    
    async def track_execution(
        self,
        execution_id: str,
        graph_name: str,
        state: Dict[str, Any],
    ) -> bool:
        self.executions.append({
            "execution_id": execution_id,
            "graph_name": graph_name,
            "state": state,
            "timestamp": datetime.utcnow().isoformat(),
        })
        return True
    
    async def record_feedback(
        self,
        execution_id: str,
        feedback: Dict[str, Any],
    ) -> bool:
        self.feedback.append({
            "execution_id": execution_id,
            "feedback": feedback,
            "timestamp": datetime.utcnow().isoformat(),
        })
        return True
    
    async def get_metrics(self) -> Dict[str, Any]:
        hit_rate = (
            (self.metrics["cache_hits"] / self.metrics["total_requests"] * 100)
            if self.metrics["total_requests"] > 0
            else 0.0
        )
        
        avg_latency = (
            sum(self.metrics["latencies"]) / len(self.metrics["latencies"])
            if self.metrics["latencies"]
            else 0.0
        )
        
        cost_saved = self.metrics["cache_hits"] * 0.001  # $0.001 per cache hit
        
        # Calculate speedup (cache hit latency vs miss latency)
        if self.metrics["latencies"]:
            avg_miss = 150.0  # Typical LLM latency
            avg_hit = 50.0   # Typical cache hit latency
            speedup = avg_miss / (avg_latency if avg_latency > 0 else avg_hit)
        else:
            speedup = 1.0
        
        return {
            "total_requests": self.metrics["total_requests"],
            "cache_hits": self.metrics["cache_hits"],
            "hit_rate": round(hit_rate, 1),
            "avg_latency": round(avg_latency, 0),
            "cost_saved": round(cost_saved, 3),
            "speedup": round(speedup, 1),
        }
    
    async def search_similar(
        self,
        query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        # Simple substring matching for in-memory (not semantic)
        results = []
        query_lower = query.lower()
        
        for key, entry in self.contexts.items():
            value_str = str(entry["value"]).lower()
            if query_lower in value_str or value_str in query_lower:
                results.append(entry)
                if len(results) >= limit:
                    break
        
        return results


# Factory function
def create_cache_fabric(backend: str = "memory", **kwargs) -> CacheFabric:
    """Create a Cache Fabric instance.
    
    Args:
        backend: Backend type ('memory', 'redis', 'vector')
        **kwargs: Backend-specific configuration
    
    Returns:
        CacheFabric instance
    """
    if backend == "memory":
        return InMemoryFabric()
    elif backend == "redis":
        # TODO: Implement RedisFabric
        raise NotImplementedError("Redis backend not yet implemented")
    elif backend == "vector":
        # TODO: Implement VectorFabric (Qdrant/Pinecone)
        raise NotImplementedError("Vector DB backend not yet implemented")
    else:
        raise ValueError(f"Unknown backend: {backend}")

