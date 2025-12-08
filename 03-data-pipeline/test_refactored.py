"""Comprehensive tests for Example 03 Data Pipeline - Refactored.

Test Coverage:
- Unit tests for intelligence/extraction/validation nodes
- Integration tests for full pipeline
- Schema validation and repair
- Sentiment/category/entities extraction
- Metrics and error handling
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
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
    """Create mock LLM."""
    return AsyncMock()


@pytest.fixture
def enriched_record_schema():
    """Mock schema for enriched records."""
    from pydantic import BaseModel, Field
    from typing import List
    
    class EnrichedRecord(BaseModel):
        sentiment: str
        entities: List[str]
        category: str
        confidence: float
        key_insights: str
    
    return EnrichedRecord


@pytest.fixture
def intelligence_node(mock_llm):
    """Create IntelligenceNode."""
    return IntelligenceNode(
        llm=mock_llm,
        prompt_template="Analyze: {raw_data}",
        required_state_keys=["raw_data"],
        name="test_intelligence",
    )


@pytest.fixture
def extraction_node(mock_llm, enriched_record_schema):
    """Create ExtractionNode."""
    return ExtractionNode(
        llm=mock_llm,
        prompt_template="Extract: {analysis}",
        output_schema=enriched_record_schema,
        name="test_extraction",
    )


@pytest.fixture
def validation_node(enriched_record_schema):
    """Create ValidationNode."""
    valid_sentiments = {"positive", "negative", "neutral"}
    valid_categories = {"customer_feedback", "bug_report", "feature_request", "other"}
    
    def valid_sentiment(data):
        return data.get("sentiment", "").lower() in valid_sentiments
    
    def valid_category(data):
        return data.get("category", "").lower() in valid_categories
    
    def valid_confidence(data):
        conf = data.get("confidence", 0.0)
        return 0.0 <= conf <= 1.0
    
    return ValidationNode(
        output_schema=enriched_record_schema,
        validation_rules={
            "valid_sentiment": valid_sentiment,
            "valid_category": valid_category,
            "confidence_range": valid_confidence,
        },
        name="test_validation",
    )


# ============================================================================
# INTELLIGENCE NODE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_intelligence_analyze_data(intelligence_node, mock_llm):
    """Test IntelligenceNode analyzes data."""
    mock_response = Mock()
    mock_response.content = "This is positive customer feedback about the dashboard."
    mock_llm.ainvoke.return_value = mock_response
    
    state = {"raw_data": "Customer loves the new dashboard feature!"}
    result = await intelligence_node.execute(state)
    
    assert "analysis" in result
    assert result["analysis"] == "This is positive customer feedback about the dashboard."
    assert intelligence_node.metrics.status == NodeStatus.SUCCESS


@pytest.mark.asyncio
async def test_intelligence_missing_data(intelligence_node):
    """Test IntelligenceNode validates input."""
    state = {}  # Missing raw_data
    
    with pytest.raises(NodeExecutionError):
        await intelligence_node.execute(state)


# ============================================================================
# EXTRACTION NODE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_extraction_valid_json(extraction_node, mock_llm):
    """Test ExtractionNode with valid JSON."""
    mock_response = Mock()
    mock_response.content = '''{"sentiment": "positive", "entities": ["John", "dashboard"], "category": "customer_feedback", "confidence": 0.95, "key_insights": "User loves new feature"}'''
    mock_llm.ainvoke.return_value = mock_response
    
    state = {"analysis": "Positive feedback..."}
    result = await extraction_node.execute(state)
    
    assert "extracted" in result
    assert result["extracted"]["sentiment"] == "positive"
    assert "John" in result["extracted"]["entities"]
    assert extraction_node.metrics.status == NodeStatus.SUCCESS


@pytest.mark.asyncio
async def test_extraction_with_repair(extraction_node, mock_llm):
    """Test ExtractionNode repairs broken JSON."""
    mock_response = Mock()
    mock_response.content = '{"sentiment": "negative", "entities": ["bug"], "category": "bug_report", "confidence": 0.8, "key_insights": "Critical issue"'
    mock_llm.ainvoke.return_value = mock_response
    
    state = {"analysis": "Bug in system..."}
    result = await extraction_node.execute(state)
    
    assert "extracted" in result
    assert "extraction_warnings" in result  # Had to repair
    assert extraction_node.metrics.status == NodeStatus.SUCCESS


# ============================================================================
# VALIDATION NODE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_validation_success(validation_node):
    """Test ValidationNode with valid data."""
    state = {
        "extracted": {
            "sentiment": "positive",
            "entities": ["user", "feature"],
            "category": "customer_feedback",
            "confidence": 0.95,
            "key_insights": "Customer satisfied"
        }
    }
    
    result = await validation_node.execute(state)
    
    assert "validated" in result
    assert result["validated"]["sentiment"] == "positive"
    assert validation_node.metrics.status == NodeStatus.SUCCESS


@pytest.mark.asyncio
async def test_validation_invalid_sentiment(validation_node):
    """Test ValidationNode catches invalid sentiment."""
    state = {
        "extracted": {
            "sentiment": "unknown",  # Invalid
            "entities": [],
            "category": "other",
            "confidence": 0.5,
            "key_insights": "Test"
        }
    }
    
    result = await validation_node.execute(state)
    
    # Should have warnings about invalid sentiment
    assert "validated" in result or "validation_warnings" in result


@pytest.mark.asyncio
async def test_validation_confidence_clamp(validation_node):
    """Test ValidationNode clamps confidence to [0,1]."""
    state = {
        "extracted": {
            "sentiment": "neutral",
            "entities": [],
            "category": "feature_request",
            "confidence": 1.5,  # Invalid - too high
            "key_insights": "Test"
        }
    }
    
    result = await validation_node.execute(state)
    
    assert "validated" in result
    assert 0.0 <= result["validated"]["confidence"] <= 1.0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_full_pipeline_positive_feedback(intelligence_node, extraction_node, validation_node, mock_llm):
    """Test full pipeline with positive feedback."""
    # Setup mocks
    analysis_response = Mock()
    analysis_response.content = "This is positive feedback about customer experience."
    
    extraction_response = Mock()
    extraction_response.content = '''{"sentiment": "positive", "entities": ["customer", "experience"], "category": "customer_feedback", "confidence": 0.92, "key_insights": "User satisfied with service"}'''
    
    mock_llm.ainvoke.side_effect = [analysis_response, extraction_response]
    
    # Run pipeline
    state = {"raw_data": "I love your product! Great customer support."}
    
    state = await intelligence_node.execute(state)
    assert "analysis" in state
    
    state = await extraction_node.execute(state)
    assert "extracted" in state
    assert state["extracted"]["sentiment"] == "positive"
    
    state = await validation_node.execute(state)
    assert "validated" in state
    assert state["validated"]["sentiment"] == "positive"


@pytest.mark.asyncio
async def test_full_pipeline_bug_report(intelligence_node, extraction_node, validation_node, mock_llm):
    """Test full pipeline with bug report."""
    # Setup mocks
    analysis_response = Mock()
    analysis_response.content = "This is a critical bug report about payment system."
    
    extraction_response = Mock()
    extraction_response.content = '''{"sentiment": "negative", "entities": ["payment", "system"], "category": "bug_report", "confidence": 0.98, "key_insights": "Critical issue affecting transactions"}'''
    
    mock_llm.ainvoke.side_effect = [analysis_response, extraction_response]
    
    # Run pipeline
    state = {"raw_data": "BUG: Payment processing fails on second submission, charges duplicate."}
    
    state = await intelligence_node.execute(state)
    state = await extraction_node.execute(state)
    state = await validation_node.execute(state)
    
    assert state["validated"]["sentiment"] == "negative"
    assert state["validated"]["category"] == "bug_report"
    assert state["validated"]["confidence"] >= 0.9


# ============================================================================
# METRICS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_metrics_collection(intelligence_node, mock_llm):
    """Test metrics are collected properly."""
    mock_response = Mock()
    mock_response.content = "Analysis result"
    mock_llm.ainvoke.return_value = mock_response
    
    state = {"raw_data": "test data"}
    await intelligence_node.execute(state)
    
    metrics = intelligence_node.get_metrics()
    
    assert metrics["name"] == "test_intelligence"
    assert metrics["status"] == "success"
    assert metrics["duration_ms"] > 0
    assert "raw_data" in metrics["input_keys"]


# ============================================================================
# TEST EXECUTION
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
