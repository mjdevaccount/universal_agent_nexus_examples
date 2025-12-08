"""
Standard Integration Template

Base class for all standardized examples.
Provides cache fabric + output parser setup.
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from cache_fabric.factory import CacheFabricFactory
from output_parsers import get_parser, OutputParser

logger = logging.getLogger(__name__)


class StandardExample:
    """
    Base class for all standardized examples.
    
    Provides:
    - Cache fabric initialization (memory/redis/vector)
    - Output parser integration
    - Manifest compilation and loading
    - Execution state tracking
    - Feedback recording
    
    Usage:
        class MyExample(StandardExample):
            def __init__(self):
                super().__init__(
                    cache_backend="memory",
                    output_parser="classification",
                    manifest_path="manifest.yaml"
                )
            
            async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
                # Implementation
                pass
    """
    
    def __init__(
        self,
        cache_backend: str = "memory",
        output_parser: Optional[str] = None,
        manifest_path: str = "manifest.yaml",
        parser_config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize standard example.
        
        Args:
            cache_backend: 'memory', 'redis', or 'vector'
            output_parser: Parser type ('classification', 'sentiment', etc)
            manifest_path: Path to manifest.yaml
            parser_config: Parser-specific configuration
        """
        self.cache_backend = cache_backend
        self.manifest_path = manifest_path
        self.parser_config = parser_config or {}
        
        # Initialize cache fabric
        self.fabric = CacheFabricFactory.create(
            backend_type=cache_backend,
            config={"default_ttl": 3600}
        )
        logger.info(f"Initialized cache fabric: {cache_backend}")
        
        # Initialize output parser
        self.parser = None
        if output_parser:
            self.parser = get_parser(output_parser, **self.parser_config)
            logger.info(f"Initialized parser: {output_parser}")
        
        # Load and compile manifest
        self.ir = None
        self._load_manifest()
    
    def _load_manifest(self):
        """Load and compile manifest."""
        try:
            # This would use universal-agent-nexus compiler
            # For now, just placeholder
            logger.info(f"Loading manifest from {self.manifest_path}")
            # from universal_agent_nexus.compiler import parse
            # self.ir = parse(self.manifest_path, source_type="uaa")
        except Exception as e:
            logger.warning(f"Could not load manifest: {e}")
    
    async def _cache_system_prompts(self):
        """Extract and cache system prompts from compiled IR."""
        if not self.ir:
            return
        
        # Cache system prompts for each router
        # Depends on IR structure
        logger.info("Cached system prompts to fabric")
    
    async def execute(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute graph with caching + parsing.
        
        To implement in subclass:
            1. Get system prompt from fabric
            2. Execute graph/agent
            3. Parse output if parser configured
            4. Track execution state
            5. Record feedback
        
        Args:
            input_data: Input to graph
        
        Returns:
            Parsed output
        """
        raise NotImplementedError("Subclass must implement execute()")
    
    async def get_system_prompt(self, key: str) -> Optional[str]:
        """Get system prompt from cache fabric.
        
        Args:
            key: Prompt key (e.g., 'router:main:system_message')
        
        Returns:
            System prompt or None
        """
        try:
            context = await self.fabric.get_context(key=key, scope="GLOBAL")
            return context.value if context else None
        except Exception as e:
            logger.warning(f"Error getting prompt {key}: {e}")
            return None
    
    async def track_execution(
        self,
        execution_id: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
    ):
        """Track execution state in fabric.
        
        Args:
            execution_id: Unique execution identifier
            input_data: Input to execution
            output_data: Output from execution
        """
        try:
            await self.fabric.set_context(
                key=f"execution:{execution_id}",
                value={
                    "timestamp": datetime.now().isoformat(),
                    "input": input_data,
                    "output": output_data,
                },
                scope="EXECUTION"
            )
        except Exception as e:
            logger.warning(f"Error tracking execution: {e}")
    
    async def record_feedback(
        self,
        execution_id: str,
        feedback: Dict[str, Any]
    ):
        """Record feedback for execution.
        
        Args:
            execution_id: Execution identifier
            feedback: Feedback data (rating, corrections, etc)
        """
        try:
            await self.fabric.set_context(
                key=f"feedback:{execution_id}",
                value=feedback,
                scope="FEEDBACK"
            )
        except Exception as e:
            logger.warning(f"Error recording feedback: {e}")
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get execution metrics from fabric.
        
        Returns:
            Metrics dict with execution counts, latencies, etc
        """
        try:
            # Would query fabric for metrics
            return {
                "executions": 0,
                "avg_latency_ms": 0,
                "feedback_count": 0,
                "cache_hits": 0,
            }
        except Exception as e:
            logger.warning(f"Error getting metrics: {e}")
            return {}
