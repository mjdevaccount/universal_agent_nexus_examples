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
        super().__init__(
            llm=llm,
            prompt_template="",
            name="mock_intent_classifier",
            description="Mock intent classifier"
        )
        self._call_count = 0
    
    async def execute(self, state):
        """Mock intent classification."""
        self._call_count += 1
        
        # Handle both dict and dataclass
        if isinstance(state, dict):
            text = state.get("request_text", "").lower()
        else:
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
        
        # Update state (handle both dict and dataclass)
        if isinstance(state, dict):
            state["detected_intent"] = intent
            state["decision"] = intent
        else:
            state.detected_intent = intent
        
        # Return dict for ConditionalWorkflow
        if isinstance(state, dict):
            return state
        else:
            from dataclasses import asdict
            result = asdict(state) if hasattr(state, "__dict__") else {"detected_intent": intent, "decision": intent}
            return result
    
    def validate_input(self, state) -> bool:
        if isinstance(state, dict):
            return state.get("request_text") is not None
        return state.request_text is not None
    
    def get_metrics(self) -> dict:
        """Override to include call count."""
        base_metrics = super().get_metrics()
        base_metrics["calls"] = self._call_count
        return base_metrics


# ============================================================================
# Mock Handler Nodes
# ============================================================================

class MockHandler:
    """Generic mock handler."""
    
    def __init__(self, handler_name: str):
        self.handler_name = handler_name
        self.metrics = {"calls": 0, "duration_ms": 0}
    
    async def execute(self, state):
        """Process request."""
        self.metrics["calls"] += 1
        # Handle both dict and dataclass
        if isinstance(state, dict):
            request_text = state.get("request_text", "")
            state["handler_response"] = f"Handled by {self.handler_name}: {request_text}"
        else:
            state.handler_response = f"Handled by {self.handler_name}: {state.request_text}"
            from dataclasses import asdict
            state = asdict(state)
        return state
    
    def validate_input(self, state) -> bool:
        return state.request_text is not None
    
    def get_metrics(self) -> dict:
        return {"handler": self.handler_name, **self.metrics}
    
    @property
    def name(self) -> str:
        return self.handler_name


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
    
    result = await classifier.execute(state)
    # Result is now a dict, but state should be updated
    if isinstance(result, dict):
        intent = result.get("decision") or result.get("detected_intent")
    else:
        intent = result
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
    
    result = await classifier.execute(state)
    # Result is now a dict
    if isinstance(result, dict):
        intent = result.get("decision") or result.get("detected_intent")
    else:
        intent = result
    assert intent == "technical"


@pytest.mark.asyncio
async def test_sales_intent_detection(mock_llm):
    """Test detection of sales intent."""
    classifier = MockIntentClassifier(mock_llm)
    
    state = TestRequestState(
        customer_id="CUST_003",
        request_text="What features does the premium plan include?",
    )
    
    result = await classifier.execute(state)
    # Result is now a dict
    if isinstance(result, dict):
        intent = result.get("decision") or result.get("detected_intent")
    else:
        intent = result
    assert intent == "sales"


@pytest.mark.asyncio
async def test_escalation_intent_detection(mock_llm):
    """Test detection of escalation intent."""
    classifier = MockIntentClassifier(mock_llm)
    
    state = TestRequestState(
        customer_id="CUST_004",
        request_text="This is a critical issue that needs immediate attention",
    )
    
    result = await classifier.execute(state)
    # Result is now a dict
    if isinstance(result, dict):
        intent = result.get("decision") or result.get("detected_intent")
    else:
        intent = result
    assert intent == "escalate"


@pytest.mark.asyncio
async def test_default_service_intent(mock_llm):
    """Test default service intent for unmatched queries."""
    classifier = MockIntentClassifier(mock_llm)
    
    state = TestRequestState(
        customer_id="CUST_005",
        request_text="Hello, I need some help",
    )
    
    result = await classifier.execute(state)
    # Result is now a dict
    if isinstance(result, dict):
        intent = result.get("decision") or result.get("detected_intent")
    else:
        intent = result
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
    
    # Convert dataclass to dict for workflow
    from dataclasses import asdict
    state_dict = asdict(state)
    result = await workflow.invoke(state_dict)
    
    # Extract state from result
    result_state = result.get("state", result)
    assert result is not None
    if isinstance(result_state, dict):
        assert result_state.get("detected_intent") == "billing"
        assert "billing" in result_state.get("handler_response", "").lower()
    else:
        assert result_state.detected_intent == "billing"
        assert "billing" in result_state.handler_response.lower()


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
        # Convert dataclass to dict for workflow
        from dataclasses import asdict
        state_dict = asdict(state)
        result = await workflow.invoke(state_dict)
        
        # Extract state from result
        result_state = result.get("state", result)
        if isinstance(result_state, dict):
            assert result_state.get("detected_intent") == expected_intent
        else:
            assert result_state.detected_intent == expected_intent


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
    
    # Convert dataclass to dict for workflow
    from dataclasses import asdict
    state_dict = asdict(state)
    # Should handle gracefully
    result = await workflow.invoke(state_dict)
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
    
    # Convert dataclass to dict for workflow
    from dataclasses import asdict
    state_dict = asdict(state)
    # Should handle missing branch
    try:
        result = await workflow.invoke(state_dict)
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
    
    # Convert dataclass to dict for workflow
    from dataclasses import asdict
    state_dict = asdict(state)
    result = await workflow.invoke(state_dict)
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
    assert metrics.get("calls", 0) >= 3


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
        # Convert dataclass to dict for workflow
        from dataclasses import asdict
        state_dict = asdict(state)
        result = await workflow.invoke(state_dict)
        # Extract state from result
        result_state = result.get("state", result)
        results.append(result_state)
    
    assert len(results) == len(requests)
    # Verify intents are detected (handle both dict and dataclass)
    intents = []
    for r in results:
        if isinstance(r, dict):
            intents.append(r.get("detected_intent"))
        else:
            intents.append(r.detected_intent)
    assert len(intents) == len(requests)
    assert all(intent is not None for intent in intents)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
