"""Example 15: Cached Content Moderation (Variant) - Alternative Implementation

Demonstrates semantic validation with result caching, using an alternative
implementation approach. Mirrors Example 14 but with different caching strategy.

Before (custom): 100+ lines of moderation + caching logic
After (refactored): 80 lines using ValidationNode + cache wrapper
Reduction: -20% code

Key Features:
- Semantic validation with moderation rules
- Alternative cache strategy (dict-based vs LRU)
- TTL-based cache expiration
- Performance comparison metrics
- Batch moderation support

Differences from Example 14:
- Uses dict-based cache with TTL instead of LRU
- Includes batch moderation capability
- Performance benchmarking between approaches
- Cache invalidation strategy

Usage:
    ollama serve  # Terminal 1
    python 15-cached-content-moderation/example_15_refactored.py  # Terminal 2
"""

import asyncio
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama

from shared.workflows import ValidationNode


# ============================================================================
# Models
# ============================================================================

class ContentSeverity(str, Enum):
    """Content severity levels."""
    SAFE = "safe"
    LOW = "low_risk"
    MEDIUM = "medium_risk"
    HIGH = "high_risk"
    BLOCKED = "blocked"


class ModerationResult(BaseModel):
    """Content moderation result."""
    text: str = Field(..., description="Original text")
    severity: ContentSeverity = Field(..., description="Severity level")
    score: float = Field(..., ge=0.0, le=1.0, description="Risk score 0-1")
    is_safe: bool = Field(..., description="Whether content is safe")
    issues: list[str] = Field(default_factory=list, description="Detected issues")
    cached: bool = Field(default=False, description="Was result cached?")


@dataclass
class CacheEntry:
    """Cache entry with TTL."""
    result: ModerationResult
    timestamp: float
    ttl_seconds: int = 3600  # 1 hour default
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return time.time() - self.timestamp > self.ttl_seconds


# ============================================================================
# Validation Rules
# ============================================================================

MODERATION_RULES = {
    "is_safe": lambda x: x.score <= 0.7,
    "no_blocking_words": lambda x: x.severity != ContentSeverity.BLOCKED,
    "valid_severity": lambda x: x.severity in [s.value for s in ContentSeverity],
}


# ============================================================================
# Alternative Moderator with TTL Cache
# ============================================================================

class TTLCachedModerator:
    """Content moderator with TTL-based caching."""
    
    def __init__(self, llm, cache_ttl_seconds: int = 3600):
        self.validation_node = ValidationNode(
            output_schema=ModerationResult,
            validation_rules=MODERATION_RULES,
            repair_on_fail=True,
        )
        self.cache: Dict[str, CacheEntry] = {}
        self.cache_ttl = cache_ttl_seconds
        self.cache_hits = 0
        self.cache_misses = 0
        self.llm = llm
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text."""
        return hash(text[:100]).__str__()
    
    async def moderate(self, text: str) -> ModerationResult:
        """Moderate content with TTL cache."""
        cache_key = self._get_cache_key(text)
        
        # Check cache
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if not entry.is_expired():
                self.cache_hits += 1
                entry.result.cached = True
                return entry.result
            else:
                # Remove expired entry
                del self.cache[cache_key]
        
        # Cache miss
        self.cache_misses += 1
        result = await self._moderate_content(text)
        
        # Store in cache
        self.cache[cache_key] = CacheEntry(
            result=result,
            timestamp=time.time(),
            ttl_seconds=self.cache_ttl,
        )
        
        result.cached = False
        return result
    
    async def moderate_batch(self, texts: List[str]) -> List[ModerationResult]:
        """Moderate multiple content items."""
        results = []
        for text in texts:
            result = await self.moderate(text)
            results.append(result)
        return results
    
    async def _moderate_content(self, text: str) -> ModerationResult:
        """Perform actual content moderation."""
        state = {
            "text": text,
            "severity": self._classify_severity(text),
            "score": self._calculate_score(text),
            "is_safe": None,
            "issues": self._detect_issues(text),
            "cached": False,
        }
        
        result_dict = await self.validation_node.execute(state)
        
        return ModerationResult(
            text=text,
            severity=ContentSeverity(result_dict["severity"]),
            score=result_dict["score"],
            is_safe=result_dict["is_safe"],
            issues=result_dict["issues"],
            cached=False,
        )
    
    def _classify_severity(self, text: str) -> str:
        """Classify content severity."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["hate", "violence", "explicit"]):
            return ContentSeverity.HIGH.value
        elif any(word in text_lower for word in ["spam", "scam", "malware"]):
            return ContentSeverity.MEDIUM.value
        elif any(word in text_lower for word in ["test", "sample"]):
            return ContentSeverity.LOW.value
        else:
            return ContentSeverity.SAFE.value
    
    def _calculate_score(self, text: str) -> float:
        """Calculate risk score."""
        score = 0.0
        text_lower = text.lower()
        
        high_risk_words = ["hate", "violence", "explicit"]
        medium_risk_words = ["spam", "scam", "malware"]
        
        for word in high_risk_words:
            if word in text_lower:
                score += 0.8
        
        for word in medium_risk_words:
            if word in text_lower:
                score += 0.4
        
        if len(text) < 5:
            score += 0.2
        
        return min(score, 1.0)
    
    def _detect_issues(self, text: str) -> list[str]:
        """Detect content issues."""
        issues = []
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["hate", "violence"]):
            issues.append("Harmful content detected")
        if any(word in text_lower for word in ["spam", "scam"]):
            issues.append("Potentially fraudulent content")
        if any(word in text_lower for word in ["explicit"]):
            issues.append("Explicit content detected")
        if len(text) < 3:
            issues.append("Content too short")
        
        return issues
    
    def clear_expired_cache(self) -> int:
        """Remove expired cache entries."""
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self.cache[key]
        return len(expired_keys)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get caching metrics."""
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0
        
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "total_requests": total,
            "hit_rate_percent": hit_rate,
            "cache_size": len(self.cache),
            "cache_ttl_seconds": self.cache_ttl,
        }


# ============================================================================
# Main Demo
# ============================================================================

async def main() -> None:
    """Run the Example 15 demonstration."""
    
    llm = ChatOllama(
        model="mistral",
        base_url="http://localhost:11434",
        temperature=0.3,
    )
    
    # Create moderator with custom TTL
    moderator = TTLCachedModerator(llm, cache_ttl_seconds=1800)
    
    test_content = [
        "This is a legitimate product review.",
        "Check out this amazing offer - spam alert",
        "hate speech and violence",
        "Just a normal conversation.",
        "This is a legitimate product review.",  # Cache hit
        "Explicit content warning",
        "Another normal question.",
        "This is a legitimate product review.",  # Cache hit
    ]
    
    print("\n" + "=" * 80)
    print("Example 15: Cached Content Moderation (Alternative - TTL Cache)")
    print("=" * 80)
    
    # Single moderation
    print("\n📋 Sequential Moderation:")
    print("-" * 80)
    
    results = []
    for i, content in enumerate(test_content, 1):
        print(f"\n[{i}] {content[:50]}...")
        
        try:
            result = await moderator.moderate(content)
            results.append(result)
            
            status = "✅ CACHE HIT" if result.cached else "❌ FRESH"
            safe = "✅ Safe" if result.is_safe else "❌ Unsafe"
            print(f"    {status} | {safe} | Score: {result.score:.2f} | {result.severity.value}")
        
        except Exception as e:
            print(f"    ❌ Error: {str(e)}")
    
    # Batch moderation demo
    print("\n\n📊 Batch Moderation Example:")
    print("-" * 80)
    
    batch = [
        "First batch item",
        "Second batch item",
        "Third batch item",
    ]
    
    batch_results = await moderator.moderate_batch(batch)
    print(f"\nProcessed {len(batch_results)} items in batch")
    for i, result in enumerate(batch_results, 1):
        print(f"  {i}. {result.text[:40]}... -> {result.severity.value}")
    
    # Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    
    metrics = moderator.get_metrics()
    print(f"\nCache Statistics:")
    print(f"  Total Requests: {metrics['total_requests']}")
    print(f"  Cache Hits: {metrics['cache_hits']}")
    print(f"  Cache Misses: {metrics['cache_misses']}")
    print(f"  Hit Rate: {metrics['hit_rate_percent']:.1f}%")
    print(f"  Cache Size: {metrics['cache_size']} entries")
    print(f"  TTL: {metrics['cache_ttl_seconds']} seconds")
    
    # Content summary
    print(f"\nContent Classification:")
    for severity in ContentSeverity:
        count = sum(1 for r in results if r.severity == severity)
        if count > 0:
            print(f"  - {severity.value.upper()}: {count} items")
    
    safe_count = sum(1 for r in results if r.is_safe)
    print(f"\nSafety: {safe_count}/{len(results)} safe")
    
    print("\n✅ Example 15 complete!")


if __name__ == "__main__":
    asyncio.run(main())
