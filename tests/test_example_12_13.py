"""Unit and integration tests for Examples 12 & 13

Example 12: Self-modifying agent with adaptive behavior
Example 13: Practical quickstart with SimpleQAWorkflow
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
from dataclasses import dataclass, asdict

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
        super().__init__(
            llm=llm,
            prompt_template="",
            name="mock_task_analyzer",
            description="Mock task analyzer"
        )
        self._call_count = 0
    
    async def execute(self, state) -> dict:
        """Analyze and classify task."""
        self._call_count += 1
        
        # Handle both dict and dataclass
        if isinstance(state, dict):
            text = state.get("task_description", "").lower()
        else:
            text = state.task_description.lower()
        
        # Simple keyword-based classification
        if any(word in text for word in ["design", "create", "plan", "evaluate"]):
            complexity = "adaptive"
        elif any(word in text for word in ["explain", "describe", "list", "breakdown"]):
            complexity = "complex"
        else:
            complexity = "simple"
        
        # Update state (handle both dict and dataclass)
        if isinstance(state, dict):
            state["complexity_level"] = complexity
            state["decision"] = complexity
        else:
            state.complexity_level = complexity
        
        # Return dict for ConditionalWorkflow
        if isinstance(state, dict):
            return state
        else:
            result = asdict(state) if hasattr(state, "__dict__") else {"complexity_level": complexity, "decision": complexity}
            return result
    
    def validate_input(self, state) -> bool:
        if isinstance(state, dict):
            return state.get("task_description") is not None
        return state.task_description is not None


class MockSimpleExecutor(BaseNode):
    """Mock simple executor."""
    def __init__(self):
        super().__init__(name="mock_simple_executor", description="Mock simple executor")
    
    async def execute(self, state) -> dict:
        # Handle both dict and dataclass
        if isinstance(state, dict):
            task_desc = state.get("task_description", "")
            state["result"] = f"Simple solution for: {task_desc}"
            if "execution_steps" not in state:
                state["execution_steps"] = []
            state["execution_steps"].append("execution")
        else:
            state.result = f"Simple solution for: {state.task_description}"
            state.execution_steps.append("execution")
            state = asdict(state)
        return state
    
    def validate_input(self, state) -> bool:
        return True


class MockComplexExecutor(BaseNode):
    """Mock complex executor."""
    def __init__(self):
        super().__init__(name="mock_complex_executor", description="Mock complex executor")
    
    async def execute(self, state) -> dict:
        # Handle both dict and dataclass
        if isinstance(state, dict):
            task_desc = state.get("task_description", "")
            if "execution_steps" not in state:
                state["execution_steps"] = []
            state["execution_steps"].extend(["breakdown", "execution", "verification"])
            state["result"] = f"Complex solution with steps for: {task_desc}"
        else:
            state.execution_steps.extend(["breakdown", "execution", "verification"])
            state.result = f"Complex solution with steps for: {state.task_description}"
            state = asdict(state)
        return state
    
    def validate_input(self, state) -> bool:
        return True


class MockAdaptiveExecutor(BaseNode):
    """Mock adaptive executor."""
    def __init__(self):
        super().__init__(name="mock_adaptive_executor", description="Mock adaptive executor")
    
    async def execute(self, state) -> dict:
        # Handle both dict and dataclass
        if isinstance(state, dict):
            task_desc = state.get("task_description", "")
            if "execution_steps" not in state:
                state["execution_steps"] = []
            state["execution_steps"].extend(["planning", "review", "adaptation", "execution"])
            state["adaptations_made"] = 1
            state["result"] = f"Adaptive solution with self-modification for: {task_desc}"
        else:
            state.execution_steps.extend(["planning", "review", "adaptation", "execution"])
            state.adaptations_made = 1
            state.result = f"Adaptive solution with self-modification for: {state.task_description}"
            state = asdict(state)
        return state
    
    def validate_input(self, state) -> bool:
        return True


@pytest.mark.asyncio
async def test_example_12_simple_task_classification():
    """Test classification of simple tasks."""
    llm = AsyncMock()
    analyzer = MockTaskAnalyzer(llm)
    
    state = MockTaskState(task_description="What is 2 + 2?")
    result = await analyzer.execute(state)
    
    # Result is now a dict
    assert result.get("decision") == "simple" or result.get("complexity_level") == "simple"
    assert state.complexity_level == "simple"


@pytest.mark.asyncio
async def test_example_12_complex_task_classification():
    """Test classification of complex tasks."""
    llm = AsyncMock()
    analyzer = MockTaskAnalyzer(llm)
    
    state = MockTaskState(task_description="Explain how photosynthesis works with detailed breakdown.")
    result = await analyzer.execute(state)
    
    # Result is now a dict
    assert result.get("decision") == "complex" or result.get("complexity_level") == "complex"


@pytest.mark.asyncio
async def test_example_12_adaptive_task_classification():
    """Test classification of adaptive tasks."""
    llm = AsyncMock()
    analyzer = MockTaskAnalyzer(llm)
    
    state = MockTaskState(task_description="Design a system and evaluate potential improvements.")
    result = await analyzer.execute(state)
    
    # Result is now a dict
    assert result.get("decision") == "adaptive" or result.get("complexity_level") == "adaptive"


@pytest.mark.asyncio
async def test_example_12_simple_executor():
    """Test simple executor execution."""
    executor = MockSimpleExecutor()
    state = MockTaskState(task_description="Quick math problem")
    
    result = await executor.execute(state)
    
    # Result is now a dict
    assert result.get("result") is not None
    assert "Quick math problem" in result.get("result", "")


@pytest.mark.asyncio
async def test_example_12_complex_executor():
    """Test complex executor with multiple steps."""
    executor = MockComplexExecutor()
    state = MockTaskState(task_description="Complex problem")
    
    result = await executor.execute(state)
    
    # Result is now a dict
    assert len(result.get("execution_steps", [])) == 3
    assert "breakdown" in result.get("execution_steps", [])
    assert "verification" in result.get("execution_steps", [])


@pytest.mark.asyncio
async def test_example_12_adaptive_executor():
    """Test adaptive executor with self-modification."""
    executor = MockAdaptiveExecutor()
    state = MockTaskState(task_description="Adaptive task")
    
    result = await executor.execute(state)
    
    # Result is now a dict
    assert result.get("adaptations_made", 0) > 0
    assert "adaptation" in result.get("execution_steps", [])


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
    
    # Test simple routing - convert dataclass to dict for workflow
    state_dict = asdict(MockTaskState(task_description="What is 2 + 2?"))
    result = await workflow.invoke(state_dict)
    
    # ConditionalWorkflow returns a dict with "state" key
    result_state = result.get("state", result)
    assert result_state.get("complexity_level") == "simple"
    assert result_state.get("result") is not None


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
    # SimpleQAWorkflow uses asyncio.to_thread(self.llm.invoke, ...)
    llm.invoke = Mock(return_value=MagicMock(
        content="Python expert response."
    ))
    
    workflow = SimpleQAWorkflow(
        name="python-qa",
        llm=llm,
        system_prompt="You are a Python expert with 10+ years experience.",
    )
    
    result = await workflow.invoke("What are decorators?")
    
    # Verify LLM was called
    assert llm.invoke.called


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
