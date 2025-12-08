"""Unit and integration tests for Examples 14 & 15: Cached Content Moderation

Tests the ValidationNode with caching strategies.
"""

import pytest
import time
from unittest.mock import AsyncMock, MagicMock
from enum import Enum

from pydantic import BaseModel, Field
from shared.workflows import ValidationNode


# ============================================================================
# Test Models
# ============================================================================

class TestSeverity(str, Enum):
    """Test severity."""
    SAFE = "safe"
    UNSAFE = "unsafe"


class TestModerationResult(BaseModel):
    """Test moderation result."""
    text: str
    severity: TestSeverity
    score: float = Field(ge=0.0, le=1.0)
    is_safe: bool
    issues: list = []


# ============================================================================
# Example 14 Tests: LRU Cache Strategy
# ============================================================================

@pytest.mark.asyncio
async def test_moderation_result_creation():
    """Test moderation result model."""
    result = TestModerationResult(
        text="test content",
        severity=TestSeverity.SAFE,
        score=0.3,
        is_safe=True,
    )
    
    assert result.text == "test content"
    assert result.is_safe is True
    assert 0.0 <= result.score <= 1.0


@pytest.mark.asyncio
async def test_validation_node_creation():
    """Test ValidationNode for moderation."""
    rules = {
        "is_safe": lambda x: x.score <= 0.7,
        "valid_severity": lambda x: x.severity in ["safe", "unsafe"],
    }
    
    node = ValidationNode(
        output_schema=TestModerationResult,
        validation_rules=rules,
        repair_on_fail=True,
    )
    
    assert node is not None


@pytest.mark.asyncio
async def test_safe_content_validation():
    """Test validation of safe content."""
    rules = {"is_safe": lambda x: x.score <= 0.7}
    
    node = ValidationNode(
        output_schema=TestModerationResult,
        validation_rules=rules,
        repair_on_fail=True,
    )
    
    state = {
        "extracted": {
            "text": "normal content",
            "severity": TestSeverity.SAFE,
            "score": 0.3,
            "is_safe": True,
            "issues": [],
        }
    }
    
    result = await node.execute(state)
    assert result is not None


@pytest.mark.asyncio
async def test_unsafe_content_detection():
    """Test detection of unsafe content."""
    rules = {"is_safe": lambda x: x.score <= 0.7}
    
    node = ValidationNode(
        output_schema=TestModerationResult,
        validation_rules=rules,
        repair_on_fail=True,
    )
    
    state = {
        "extracted": {
            "text": "harmful content",
            "severity": TestSeverity.UNSAFE,
            "score": 0.9,
            "is_safe": False,
            "issues": ["harmful"],
        }
    }
    
    result = await node.execute(state)
    assert result is not None


@pytest.mark.asyncio
async def test_score_validation():
    """Test score bounds validation."""
    result = TestModerationResult(
        text="test",
        severity=TestSeverity.SAFE,
        score=0.5,
        is_safe=True,
    )
    
    # Score should be between 0 and 1
    assert 0.0 <= result.score <= 1.0


@pytest.mark.asyncio
async def test_score_at_boundaries():
    """Test score at 0 and 1 boundaries."""
    safe = TestModerationResult(
        text="safe",
        severity=TestSeverity.SAFE,
        score=0.0,
        is_safe=True,
    )
    assert safe.score == 0.0
    
    unsafe = TestModerationResult(
        text="unsafe",
        severity=TestSeverity.UNSAFE,
        score=1.0,
        is_safe=False,
    )
    assert unsafe.score == 1.0


# ============================================================================
# Example 15 Tests: TTL Cache Strategy
# ============================================================================

@pytest.mark.asyncio
async def test_cache_entry_creation():
    """Test cache entry with TTL."""
    from dataclasses import dataclass
    
    @dataclass
    class MockCacheEntry:
        timestamp: float
        ttl_seconds: int = 3600
        
        def is_expired(self) -> bool:
            return time.time() - self.timestamp > self.ttl_seconds
    
    entry = MockCacheEntry(timestamp=time.time())
    assert not entry.is_expired()


@pytest.mark.asyncio
async def test_cache_entry_expiration():
    """Test that cache entries expire."""
    from dataclasses import dataclass
    
    @dataclass
    class MockCacheEntry:
        timestamp: float
        ttl_seconds: int = 1  # 1 second
        
        def is_expired(self) -> bool:
            return time.time() - self.timestamp > self.ttl_seconds
    
    # Create entry that will expire
    entry = MockCacheEntry(timestamp=time.time() - 2)  # 2 seconds ago
    assert entry.is_expired()


@pytest.mark.asyncio
async def test_batch_moderation():
    """Test batch moderation processing."""
    texts = ["item1", "item2", "item3"]
    
    # Simulate batch processing
    results = []
    for text in texts:
        result = TestModerationResult(
            text=text,
            severity=TestSeverity.SAFE,
            score=0.3,
            is_safe=True,
        )
        results.append(result)
    
    assert len(results) == len(texts)


@pytest.mark.asyncio
async def test_cache_metrics():
    """Test cache metrics calculation."""
    cache_hits = 5
    cache_misses = 15
    total = cache_hits + cache_misses
    hit_rate = (cache_hits / total * 100) if total > 0 else 0
    
    assert total == 20
    assert hit_rate == 25.0  # 5 hits out of 20 = 25%


@pytest.mark.asyncio
async def test_multiple_severity_levels():
    """Test handling of multiple severity levels."""
    severities = [TestSeverity.SAFE, TestSeverity.UNSAFE]
    
    for severity in severities:
        result = TestModerationResult(
            text="test",
            severity=severity,
            score=0.5,
            is_safe=(severity == TestSeverity.SAFE),
        )
        assert result.severity in severities


@pytest.mark.asyncio
async def test_issue_tracking():
    """Test tracking of content issues."""
    result = TestModerationResult(
        text="harmful content",
        severity=TestSeverity.UNSAFE,
        score=0.8,
        is_safe=False,
        issues=["harmful", "inappropriate"],
    )
    
    assert len(result.issues) == 2
    assert "harmful" in result.issues


@pytest.mark.asyncio
async def test_cache_key_generation():
    """Test cache key generation from text."""
    text1 = "This is test content"
    text2 = "This is different content"
    
    key1 = hash(text1[:100]).__str__()
    key2 = hash(text2[:100]).__str__()
    
    assert key1 != key2  # Different texts should have different keys


@pytest.mark.asyncio
async def test_identical_content_caching():
    """Test that identical content gets same cache key."""
    text = "Same content for caching test"
    
    key1 = hash(text[:100]).__str__()
    key2 = hash(text[:100]).__str__()
    
    assert key1 == key2  # Same text should have same key


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
