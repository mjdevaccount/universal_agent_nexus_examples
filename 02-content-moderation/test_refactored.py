"""Comprehensive tests for Example 02 Content Moderation - Refactored.

Test Coverage:
- Unit tests for each node
- Integration tests for workflow
- Edge cases and error handling
- Metrics validation
- Repair strategy verification
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pydantic import BaseModel
from typing import Dict, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.workflows.common_nodes import (
    IntelligenceNode,
    ExtractionNode,
    ValidationNode,
)
from shared.workflows.nodes import NodeExecutionError, NodeStatus


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_llm():
    """Create mock LLM for testing."""
    llm = AsyncMock()
    return llm


@pytest.fixture
def intelligence_node(mock_llm):
    """Create IntelligenceNode for testing."""
    return IntelligenceNode(
        llm=mock_llm,
        prompt_template="Analyze: {content}",
        required_state_keys=["content"],
        name="test_intelligence",
    )


@pytest.fixture
def mock_schema():
    """Mock Pydantic schema."""
    class TestSchema(BaseModel):
        severity_level: str
        risk_category: str
        confidence: float
    return TestSchema


@pytest.fixture
def extraction_node(mock_llm, mock_schema):
    """Create ExtractionNode for testing."""
    return ExtractionNode(
        llm=mock_llm,
        prompt_template="Extract: {analysis}",
        output_schema=mock_schema,
        name="test_extraction",
    )


@pytest.fixture
def validation_node(mock_schema):
    """Create ValidationNode for testing."""
    def valid_severity(data):
        return data.get("severity_level") in ["safe", "low", "medium", "high", "critical"]
    
    return ValidationNode(
        output_schema=mock_schema,
        validation_rules={"valid_severity": valid_severity},
        name="test_validation",
    )


# ============================================================================
# INTELLIGENCE NODE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_intelligence_node_execute_success(intelligence_node, mock_llm):
    """Test IntelligenceNode successful execution."""
    # Setup
    mock_response = Mock()
    mock_response.content = "Analysis: Content is safe"
    mock_llm.ainvoke.return_value = mock_response
    
    state = {"content": "test content"}
    
    # Execute
    result = await intelligence_node.execute(state)
    
    # Verify
    assert "analysis" in result
    assert result["analysis"] == "Analysis: Content is safe"
    assert intelligence_node.metrics.status == NodeStatus.SUCCESS
    assert intelligence_node.metrics.duration_ms > 0


@pytest.mark.asyncio
async def test_intelligence_node_validate_input(intelligence_node):
    """Test IntelligenceNode input validation."""
    # Missing required key
    assert not intelligence_node.validate_input({})
    
    # Has required key
    assert intelligence_node.validate_input({"content": "test"})


@pytest.mark.asyncio
async def test_intelligence_node_missing_key(intelligence_node):
    """Test IntelligenceNode raises error on missing required key."""
    state = {}  # Missing content
    
    with pytest.raises(NodeExecutionError) as exc_info:
        await intelligence_node.execute(state)
    
    assert "Missing required keys" in str(exc_info.value)


# ============================================================================
# EXTRACTION NODE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_extraction_node_direct_parse(extraction_node, mock_llm):
    """Test ExtractionNode with valid JSON (direct parse)."""
    # Setup
    mock_response = Mock()
    mock_response.content = '{"severity_level": "medium", "risk_category": "spam", "confidence": 0.8}'
    mock_llm.ainvoke.return_value = mock_response
    
    state = {"analysis": "This looks like spam"}
    
    # Execute
    result = await extraction_node.execute(state)
    
    # Verify
    assert "extracted" in result
    assert result["extracted"]["severity_level"] == "medium"
    assert result["extracted"]["confidence"] == 0.8
    assert extraction_node.metrics.status == NodeStatus.SUCCESS
    assert "extraction_warnings" not in result  # No repairs needed


@pytest.mark.asyncio
async def test_extraction_node_json_repair(extraction_node, mock_llm):
    """Test ExtractionNode with broken JSON (incremental repair)."""
    # Setup - broken JSON
    mock_response = Mock()
    mock_response.content = '{"severity_level": "high", "risk_category": "hate", "confidence": 0.9'
    mock_llm.ainvoke.return_value = mock_response
    
    state = {"analysis": "Hateful content detected"}
    
    # Execute
    result = await extraction_node.execute(state)
    
    # Verify - should repair and succeed
    assert "extracted" in result
    assert "extraction_warnings" in result
    assert "repair" in result["extraction_warnings"][0].lower()
    assert extraction_node.metrics.status == NodeStatus.SUCCESS


@pytest.mark.asyncio
async def test_extraction_node_missing_analysis(extraction_node):
    """Test ExtractionNode raises error on missing analysis."""
    state = {}  # Missing analysis
    
    with pytest.raises(NodeExecutionError) as exc_info:
        await extraction_node.execute(state)
    
    assert "analysis" in str(exc_info.value)


# ============================================================================
# VALIDATION NODE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_validation_node_success(validation_node):
    """Test ValidationNode with valid data."""
    state = {
        "extracted": {
            "severity_level": "medium",
            "risk_category": "spam",
            "confidence": 0.75
        }
    }
    
    # Execute
    result = await validation_node.execute(state)
    
    # Verify
    assert "validated" in result
    assert result["validated"]["severity_level"] == "medium"
    assert validation_node.metrics.status == NodeStatus.SUCCESS


@pytest.mark.asyncio
async def test_validation_node_confidence_bounds(validation_node):
    """Test ValidationNode clamps confidence to [0,1]."""
    state = {
        "extracted": {
            "severity_level": "safe",
            "risk_category": "none",
            "confidence": 1.5  # Invalid - too high
        }
    }
    
    # Execute - should repair
    result = await validation_node.execute(state)
    
    # Verify - confidence clamped
    assert "validated" in result
    assert 0 <= result["validated"]["confidence"] <= 1.0
    assert "validation_warnings" in result


@pytest.mark.asyncio
async def test_validation_node_invalid_severity(validation_node):
    """Test ValidationNode with invalid severity level."""
    state = {
        "extracted": {
            "severity_level": "unknown",  # Invalid
            "risk_category": "other",
            "confidence": 0.5
        }
    }
    
    # Execute - should attempt repair
    result = await validation_node.execute(state)
    
    # Verify
    assert "validated" in result or "validation_warnings" in result


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_node_pipeline_success(intelligence_node, extraction_node, validation_node, mock_llm):
    """Test full pipeline: Intelligence -> Extraction -> Validation."""
    # Setup mocks
    analysis_response = Mock()
    analysis_response.content = "This content appears to be spam based on excessive capitalization and urgency markers."
    
    extraction_response = Mock()
    extraction_response.content = '{"severity_level": "high", "risk_category": "spam", "confidence": 0.85}'
    
    mock_llm.ainvoke.side_effect = [analysis_response, extraction_response]
    
    # Run pipeline
    state = {"content": "BUY NOW!! LIMITED TIME OFFER!!"}
    
    state = await intelligence_node.execute(state)
    assert "analysis" in state
    
    state = await extraction_node.execute(state)
    assert "extracted" in state
    
    state = await validation_node.execute(state)
    assert "validated" in state
    
    # Verify final state
    assert state["validated"]["severity_level"] == "high"
    assert state["validated"]["risk_category"] == "spam"
    assert 0 <= state["validated"]["confidence"] <= 1.0


# ============================================================================
# METRICS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_intelligence_node_metrics(intelligence_node, mock_llm):
    """Test IntelligenceNode metrics collection."""
    mock_response = Mock()
    mock_response.content = "Analysis result"
    mock_llm.ainvoke.return_value = mock_response
    
    state = {"content": "test"}
    await intelligence_node.execute(state)
    
    metrics = intelligence_node.get_metrics()
    
    assert metrics["name"] == "test_intelligence"
    assert metrics["status"] == "success"
    assert metrics["duration_ms"] >= 0
    assert "content" in metrics["input_keys"]
    assert "analysis" in metrics["output_keys"]


@pytest.mark.asyncio
async def test_extraction_node_metrics_with_warnings(extraction_node, mock_llm):
    """Test ExtractionNode metrics with repair warnings."""
    # Broken JSON that will be repaired
    mock_response = Mock()
    mock_response.content = '{"severity_level": "low", "risk_category": "low", "confidence": 0.6'
    mock_llm.ainvoke.return_value = mock_response
    
    state = {"analysis": "test analysis"}
    result = await extraction_node.execute(state)
    
    metrics = extraction_node.get_metrics()
    
    assert metrics["status"] == "success"
    assert len(metrics["warnings"]) > 0
    assert "repair" in metrics["warnings"][0].lower()


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_extraction_node_llm_failure(extraction_node, mock_llm):
    """Test ExtractionNode handles LLM failures gracefully."""
    mock_llm.ainvoke.side_effect = Exception("LLM error")
    
    state = {"analysis": "test"}
    
    with pytest.raises(Exception):
        await extraction_node.execute(state)
    
    assert extraction_node.metrics.status == NodeStatus.FAILED
    assert extraction_node.metrics.error_message is not None


# ============================================================================
# REPAIR STRATEGY TESTS
# ============================================================================

def test_extraction_node_incremental_repair():
    """Test incremental JSON repair strategy."""
    # Create node without full initialization
    from shared.workflows.common_nodes import ExtractionNode
    from pydantic import BaseModel
    
    class DummySchema(BaseModel):
        test: str
    
    node = ExtractionNode(
        llm=Mock(),
        prompt_template="test",
        output_schema=DummySchema,
    )
    
    # Test repair
    broken = '{"test": "value"'
    repaired = node._repair_json_incremental(broken)
    
    # Should close the brace
    import json
    try:
        json.loads(repaired)
        assert True  # Successfully parsed
    except json.JSONDecodeError:
        assert False  # Should be repairable


# ============================================================================
# TEST EXECUTION
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
