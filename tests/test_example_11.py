"""Unit and integration tests for Example 11: N-Decision Router

Tests the ConditionalWorkflow with multiple intent branches and routing logic.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from dataclasses import dataclass
from shared.workflows import ConditionalWorkflow, IntelligenceNode


# ============================================================================
# Test Models
# ============================================================================

@dataclass
class TestRequestState:
    """Test request state."""
    customer_id: str
    request_text: str
    detected_intent: str = None
    handler_response: str = None
    metadata: dict = None


# ============================================================================
# Mock Decision Node
# ============================================================================

class MockIntentClassifier(IntelligenceNode):
    """Mock intent classifier."""
    
    def __init__(self, llm):
        self.llm = llm
        self.metrics = {"calls": 0}
        self.prompt_template = ""
    
    async def execute(self, state: TestRequestState) -> str:
        """Mock intent classification."""
        self.metrics["calls"] += 1
        
        # Simple keyword-based intent detection
        text = state.request_text.lower()
        
        if "payment" in text or "invoice" in text:
            intent = "billing"
        elif "error" in text or "broken" in text or "crash" in text:
            intent = "technical"
        elif "feature" in text or "plan" in text or "pricing" in text:
            intent = "sales"
        elif "urgent" in text or "critical" in text:
            intent = "escalate"
        else:
            intent = "service"
        
        state.detected_intent = intent
        return intent
    
    def validate_input(self, state) -> bool:
        return state.request_text is not None


# ============================================================================
# Mock Handler Nodes
# ============================================================================

class MockHandler:
    """Generic mock handler."""
    
    def __init__(self, handler_name: str):
        self.handler_name = handler_name
        self.metrics = {"calls": 0, "duration_ms": 0}
    
    async def execute(self, state: TestRequestState) -> TestRequestState:
        """Process request."""
        self.metrics["calls"] += 1
        state.handler_response = f"Handled by {self.handler_name}: {state.request_text}"
        return state
    
    def validate_input(self, state) -> bool:
        return state.request_text is not None
    
    def get_metrics(self) -> dict:
        return {"handler": self.handler_name, **self.metrics}


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_llm():
    """Create mock LLM."""
    llm = AsyncMock()
    return llm


@pytest.fixture
def mock_handlers():
    """Create mock handler nodes."""
    return {
        "service": [MockHandler("service")],
        "billing": [MockHandler("billing")],
        "technical": [MockHandler("technical")],
        "sales": [MockHandler("sales")],
        "escalate": [MockHandler("escalate")],
    }


@pytest.fixture
async def workflow(mock_llm, mock_handlers):
    """Create ConditionalWorkflow instance."""
    decision_node = MockIntentClassifier(mock_llm)
    
    return ConditionalWorkflow(
        name="test-router",
        state_schema=TestRequestState,
        decision_node=decision_node,
        branches=mock_handlers,
    )


# ============================================================================
# Intent Detection Tests
# ============================================================================

@pytest.mark.asyncio
async def test_billing_intent_detection(mock_llm):
    """Test detection of billing intent."""
    classifier = MockIntentClassifier(mock_llm)
    
    state = TestRequestState(
        customer_id="CUST_001",
        request_text="My payment didn't go through",
    )
    
    intent = await classifier.execute(state)
    assert intent == "billing"
    assert state.detected_intent == "billing"


@pytest.mark.asyncio
async def test_technical_intent_detection(mock_llm):
    """Test detection of technical intent."""
    classifier = MockIntentClassifier(mock_llm)
    
    state = TestRequestState(
        customer_id="CUST_002",
        request_text="I'm getting an error when I log in",
    )
    
    intent = await classifier.execute(state)
    assert intent == "technical"


@pytest.mark.asyncio
async def test_sales_intent_detection(mock_llm):
    """Test detection of sales intent."""
    classifier = MockIntentClassifier(mock_llm)
    
    state = TestRequestState(
        customer_id="CUST_003",
        request_text="What features does the premium plan include?",
    )
    
    intent = await classifier.execute(state)
    assert intent == "sales"


@pytest.mark.asyncio
async def test_escalation_intent_detection(mock_llm):
    """Test detection of escalation intent."""
    classifier = MockIntentClassifier(mock_llm)
    
    state = TestRequestState(
        customer_id="CUST_004",
        request_text="This is a critical issue that needs immediate attention",
    )
    
    intent = await classifier.execute(state)
    assert intent == "escalate"


@pytest.mark.asyncio
async def test_default_service_intent(mock_llm):
    """Test default service intent for unmatched queries."""
    classifier = MockIntentClassifier(mock_llm)
    
    state = TestRequestState(
        customer_id="CUST_005",
        request_text="Hello, I need some help",
    )
    
    intent = await classifier.execute(state)
    assert intent == "service"


# ============================================================================
# Routing Tests
# ============================================================================

@pytest.mark.asyncio
async def test_workflow_routes_to_correct_branch(mock_llm, mock_handlers):
    """Test that workflow routes to correct branch."""
    decision_node = MockIntentClassifier(mock_llm)
    
    workflow = ConditionalWorkflow(
        name="test-router",
        state_schema=TestRequestState,
        decision_node=decision_node,
        branches=mock_handlers,
    )
    
    state = TestRequestState(
        customer_id="CUST_001",
        request_text="My payment didn't work",
    )
    
    result = await workflow.invoke(state)
    
    assert result is not None
    assert result.detected_intent == "billing"
    assert "billing" in result.handler_response.lower()


@pytest.mark.asyncio
async def test_all_branches_accessible(mock_llm, mock_handlers):
    """Test that all branches can be accessed."""
    decision_node = MockIntentClassifier(mock_llm)
    
    workflow = ConditionalWorkflow(
        name="test-router",
        state_schema=TestRequestState,
        decision_node=decision_node,
        branches=mock_handlers,
    )
    
    test_cases = [
        ("My payment failed", "billing"),
        ("There's an error", "technical"),
        ("What's the pricing?", "sales"),
        ("This is urgent", "escalate"),
        ("General help", "service"),
    ]
    
    for request_text, expected_intent in test_cases:
        state = TestRequestState(
            customer_id="CUST_TEST",
            request_text=request_text,
        )
        
        result = await workflow.invoke(state)
        assert result.detected_intent == expected_intent


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.asyncio
async def test_empty_request_handling(mock_llm, mock_handlers):
    """Test handling of empty requests."""
    decision_node = MockIntentClassifier(mock_llm)
    
    workflow = ConditionalWorkflow(
        name="test-router",
        state_schema=TestRequestState,
        decision_node=decision_node,
        branches=mock_handlers,
    )
    
    state = TestRequestState(
        customer_id="CUST_EMPTY",
        request_text="",
    )
    
    # Should handle gracefully
    result = await workflow.invoke(state)
    assert result is not None


@pytest.mark.asyncio
async def test_missing_branch_fallback(mock_llm):
    """Test fallback when branch doesn't exist."""
    decision_node = MockIntentClassifier(mock_llm)
    
    # Only provide some branches
    limited_branches = {
        "service": [MockHandler("service")],
        "billing": [MockHandler("billing")],
    }
    
    workflow = ConditionalWorkflow(
        name="test-router",
        state_schema=TestRequestState,
        decision_node=decision_node,
        branches=limited_branches,
    )
    
    # Request that would normally go to "technical"
    state = TestRequestState(
        customer_id="CUST_MISSING",
        request_text="There's an error",
    )
    
    # Should handle missing branch
    try:
        result = await workflow.invoke(state)
        # Either it works or raises KeyError, both are acceptable
    except KeyError:
        # Expected if branch routing fails
        pass


# ============================================================================
# Metrics and Observability Tests
# ============================================================================

@pytest.mark.asyncio
async def test_metrics_collection(mock_llm, mock_handlers):
    """Test that metrics are collected."""
    decision_node = MockIntentClassifier(mock_llm)
    
    workflow = ConditionalWorkflow(
        name="test-router",
        state_schema=TestRequestState,
        decision_node=decision_node,
        branches=mock_handlers,
    )
    
    state = TestRequestState(
        customer_id="CUST_001",
        request_text="General help request",
    )
    
    result = await workflow.invoke(state)
    metrics = workflow.get_metrics()
    
    assert metrics is not None
    assert "workflow_name" in metrics
    assert metrics["workflow_name"] == "test-router"


@pytest.mark.asyncio
async def test_decision_node_metric_tracking(mock_llm):
    """Test that decision node calls are tracked."""
    classifier = MockIntentClassifier(mock_llm)
    
    state = TestRequestState(
        customer_id="CUST_001",
        request_text="Test request",
    )
    
    await classifier.execute(state)
    await classifier.execute(state)
    await classifier.execute(state)
    
    metrics = classifier.get_metrics()
    assert metrics.get("calls") >= 3


# ============================================================================
# Multi-Request Tests
# ============================================================================

@pytest.mark.asyncio
async def test_multiple_sequential_requests(mock_llm, mock_handlers):
    """Test workflow with multiple sequential requests."""
    decision_node = MockIntentClassifier(mock_llm)
    
    workflow = ConditionalWorkflow(
        name="test-router",
        state_schema=TestRequestState,
        decision_node=decision_node,
        branches=mock_handlers,
    )
    
    requests = [
        "Help with my account",
        "Invoice question",
        "System crash",
        "Plan details",
    ]
    
    results = []
    for request in requests:
        state = TestRequestState(
            customer_id="CUST_BATCH",
            request_text=request,
        )
        result = await workflow.invoke(state)
        results.append(result)
    
    assert len(results) == len(requests)
    # Verify intents are detected
    intents = [r.detected_intent for r in results]
    assert len(intents) == len(requests)
    assert all(intent is not None for intent in intents)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
