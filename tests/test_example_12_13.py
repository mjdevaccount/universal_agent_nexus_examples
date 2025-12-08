"""Unit and integration tests for Examples 12 & 13

Example 12: Self-modifying agent with adaptive behavior
Example 13: Practical quickstart with SimpleQAWorkflow
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from dataclasses import dataclass

from shared.workflows import ConditionalWorkflow, SimpleQAWorkflow, IntelligenceNode, BaseNode


# ============================================================================
# Example 12 Tests: Self-Modifying Agent
# ============================================================================

@dataclass
class MockTaskState:
    """Mock task state."""
    task_description: str
    complexity_level: str = None
    result: str = None
    execution_steps: list = None
    adaptations_made: int = 0
    
    def __post_init__(self):
        if self.execution_steps is None:
            self.execution_steps = []


class MockTaskAnalyzer(IntelligenceNode):
    """Mock task analyzer for testing."""
    
    def __init__(self, llm):
        self.llm = llm
        self.prompt_template = ""
        self.metrics = {"calls": 0}
    
    async def execute(self, state: MockTaskState) -> str:
        """Analyze and classify task."""
        self.metrics["calls"] += 1
        
        text = state.task_description.lower()
        
        # Simple keyword-based classification
        if any(word in text for word in ["design", "create", "plan", "evaluate"]):
            complexity = "adaptive"
        elif any(word in text for word in ["explain", "describe", "list", "breakdown"]):
            complexity = "complex"
        else:
            complexity = "simple"
        
        state.complexity_level = complexity
        return complexity
    
    def validate_input(self, state: MockTaskState) -> bool:
        return state.task_description is not None


class MockSimpleExecutor(BaseNode):
    """Mock simple executor."""
    async def execute(self, state: MockTaskState) -> MockTaskState:
        state.result = f"Simple solution for: {state.task_description}"
        state.execution_steps.append("execution")
        return state
    
    def validate_input(self, state: MockTaskState) -> bool:
        return True


class MockComplexExecutor(BaseNode):
    """Mock complex executor."""
    async def execute(self, state: MockTaskState) -> MockTaskState:
        state.execution_steps.append("breakdown")
        state.execution_steps.append("execution")
        state.execution_steps.append("verification")
        state.result = f"Complex solution with steps for: {state.task_description}"
        return state
    
    def validate_input(self, state: MockTaskState) -> bool:
        return True


class MockAdaptiveExecutor(BaseNode):
    """Mock adaptive executor."""
    async def execute(self, state: MockTaskState) -> MockTaskState:
        state.execution_steps.append("planning")
        state.execution_steps.append("review")
        state.execution_steps.append("adaptation")
        state.execution_steps.append("execution")
        state.adaptations_made = 1
        state.result = f"Adaptive solution with self-modification for: {state.task_description}"
        return state
    
    def validate_input(self, state: MockTaskState) -> bool:
        return True


@pytest.mark.asyncio
async def test_example_12_simple_task_classification():
    """Test classification of simple tasks."""
    llm = AsyncMock()
    analyzer = MockTaskAnalyzer(llm)
    
    state = MockTaskState(task_description="What is 2 + 2?")
    result = await analyzer.execute(state)
    
    assert result == "simple"
    assert state.complexity_level == "simple"


@pytest.mark.asyncio
async def test_example_12_complex_task_classification():
    """Test classification of complex tasks."""
    llm = AsyncMock()
    analyzer = MockTaskAnalyzer(llm)
    
    state = MockTaskState(task_description="Explain how photosynthesis works with detailed breakdown.")
    result = await analyzer.execute(state)
    
    assert result == "complex"


@pytest.mark.asyncio
async def test_example_12_adaptive_task_classification():
    """Test classification of adaptive tasks."""
    llm = AsyncMock()
    analyzer = MockTaskAnalyzer(llm)
    
    state = MockTaskState(task_description="Design a system and evaluate potential improvements.")
    result = await analyzer.execute(state)
    
    assert result == "adaptive"


@pytest.mark.asyncio
async def test_example_12_simple_executor():
    """Test simple executor execution."""
    executor = MockSimpleExecutor()
    state = MockTaskState(task_description="Quick math problem")
    
    result = await executor.execute(state)
    
    assert result.result is not None
    assert "Quick math problem" in result.result


@pytest.mark.asyncio
async def test_example_12_complex_executor():
    """Test complex executor with multiple steps."""
    executor = MockComplexExecutor()
    state = MockTaskState(task_description="Complex problem")
    
    result = await executor.execute(state)
    
    assert len(result.execution_steps) == 3
    assert "breakdown" in result.execution_steps
    assert "verification" in result.execution_steps


@pytest.mark.asyncio
async def test_example_12_adaptive_executor():
    """Test adaptive executor with self-modification."""
    executor = MockAdaptiveExecutor()
    state = MockTaskState(task_description="Adaptive task")
    
    result = await executor.execute(state)
    
    assert result.adaptations_made > 0
    assert "adaptation" in result.execution_steps


@pytest.mark.asyncio
async def test_example_12_workflow_routing():
    """Test workflow routes to correct executor."""
    llm = AsyncMock()
    analyzer = MockTaskAnalyzer(llm)
    
    branches = {
        "simple": [MockSimpleExecutor()],
        "complex": [MockComplexExecutor()],
        "adaptive": [MockAdaptiveExecutor()],
    }
    
    workflow = ConditionalWorkflow(
        name="test-agent",
        state_schema=MockTaskState,
        decision_node=analyzer,
        branches=branches,
    )
    
    # Test simple routing
    state = MockTaskState(task_description="What is 2 + 2?")
    result = await workflow.invoke(state)
    
    assert result.complexity_level == "simple"
    assert result.result is not None


# ============================================================================
# Example 13 Tests: SimpleQAWorkflow
# ============================================================================

@pytest.mark.asyncio
async def test_example_13_workflow_creation():
    """Test SimpleQAWorkflow can be created."""
    llm = AsyncMock()
    
    workflow = SimpleQAWorkflow(
        name="test-qa",
        llm=llm,
        system_prompt="You are helpful.",
    )
    
    assert workflow is not None
    assert workflow.name == "test-qa"


@pytest.mark.asyncio
async def test_example_13_simple_question():
    """Test simple Q&A execution."""
    llm = AsyncMock()
    llm.ainvoke = AsyncMock(return_value=MagicMock(
        content="The answer is 4."
    ))
    
    workflow = SimpleQAWorkflow(
        name="test-qa",
        llm=llm,
        system_prompt="You are a math tutor.",
    )
    
    result = await workflow.invoke("What is 2 + 2?")
    
    assert result is not None
    assert "answer" in result or "response" in result


@pytest.mark.asyncio
async def test_example_13_metrics_collection():
    """Test that metrics are collected."""
    llm = AsyncMock()
    llm.ainvoke = AsyncMock(return_value=MagicMock(
        content="Sample answer."
    ))
    
    workflow = SimpleQAWorkflow(
        name="test-qa",
        llm=llm,
    )
    
    result = await workflow.invoke("Test question?")
    metrics = workflow.get_metrics()
    
    assert metrics is not None


@pytest.mark.asyncio
async def test_example_13_multiple_questions():
    """Test workflow with multiple sequential questions."""
    llm = AsyncMock()
    llm.ainvoke = AsyncMock(return_value=MagicMock(
        content="Sample answer."
    ))
    
    workflow = SimpleQAWorkflow(
        name="test-qa",
        llm=llm,
    )
    
    questions = ["Q1?", "Q2?", "Q3?"]
    results = []
    
    for q in questions:
        result = await workflow.invoke(q)
        results.append(result)
    
    assert len(results) == 3


@pytest.mark.asyncio
async def test_example_13_system_prompt_usage():
    """Test that system prompt is used."""
    llm = AsyncMock()
    llm.ainvoke = AsyncMock(return_value=MagicMock(
        content="Python expert response."
    ))
    
    workflow = SimpleQAWorkflow(
        name="python-qa",
        llm=llm,
        system_prompt="You are a Python expert with 10+ years experience.",
    )
    
    result = await workflow.invoke("What are decorators?")
    
    # Verify LLM was called
    assert llm.ainvoke.called


@pytest.mark.asyncio
async def test_example_13_empty_question():
    """Test handling of empty questions."""
    llm = AsyncMock()
    llm.ainvoke = AsyncMock(return_value=MagicMock(
        content="Please provide a question."
    ))
    
    workflow = SimpleQAWorkflow(
        name="test-qa",
        llm=llm,
    )
    
    result = await workflow.invoke("")
    assert result is not None


@pytest.mark.asyncio
async def test_example_13_domain_specific_workflows():
    """Test domain-specific configurations."""
    llm = AsyncMock()
    llm.ainvoke = AsyncMock(return_value=MagicMock(
        content="Domain-specific answer."
    ))
    
    domains = [
        ("python", "You are a Python expert."),
        ("web-dev", "You are a web developer."),
        ("data-science", "You are a data scientist."),
    ]
    
    for domain_name, system_prompt in domains:
        workflow = SimpleQAWorkflow(
            name=f"{domain_name}-qa",
            llm=llm,
            system_prompt=system_prompt,
        )
        
        result = await workflow.invoke(f"Question about {domain_name}?")
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
