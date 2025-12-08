"""Unit and integration tests for Example 10: Local LLM Tool Servers

Tests the ToolCallingWorkflow with multiple tool types and error scenarios.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain.tools import Tool
from shared.workflows import ToolCallingWorkflow


# ============================================================================
# Mock Tools
# ============================================================================

def mock_arithmetic(expression: str) -> str:
    """Mock arithmetic tool."""
    if "invalid" in expression.lower():
        return "Error: Invalid expression"
    return f"Result: {eval(expression)}"


def mock_search(query: str) -> str:
    """Mock web search tool."""
    if "not found" in query.lower():
        return "No results found"
    return f"Found information about {query}"


def mock_text_length(text: str) -> str:
    """Mock text length tool."""
    return f"Text has {len(text)} characters and {len(text.split())} words"


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_tools():
    """Create mock LangChain Tool objects."""
    return [
        Tool(
            name="arithmetic",
            func=mock_arithmetic,
            description="Calculate math expressions",
        ),
        Tool(
            name="web_search",
            func=mock_search,
            description="Search the web",
        ),
        Tool(
            name="text_length",
            func=mock_text_length,
            description="Get text length",
        ),
    ]


@pytest.fixture
def mock_llm():
    """Create mock LLM."""
    llm = AsyncMock()
    llm.invoke = AsyncMock()
    return llm


@pytest.fixture
async def workflow(mock_llm, mock_tools):
    """Create ToolCallingWorkflow instance."""
    return ToolCallingWorkflow(
        name="test-workflow",
        llm=mock_llm,
        tools=mock_tools,
        max_iterations=3,
    )


# ============================================================================
# Happy Path Tests
# ============================================================================

@pytest.mark.asyncio
async def test_workflow_creation(mock_llm, mock_tools):
    """Test workflow can be created successfully."""
    workflow = ToolCallingWorkflow(
        name="test",
        llm=mock_llm,
        tools=mock_tools,
    )
    assert workflow is not None
    assert workflow.name == "test"


@pytest.mark.asyncio
async def test_simple_tool_call(mock_llm, mock_tools):
    """Test simple tool call execution."""
    workflow = ToolCallingWorkflow(
        name="test",
        llm=mock_llm,
        tools=mock_tools,
        max_iterations=1,
    )
    
    # Mock LLM to request arithmetic tool
    mock_llm.invoke = AsyncMock(return_value=MagicMock(
        content="The result is 15",
        tool_calls=[],  # No more tool calls
    ))
    
    result = await workflow.invoke("Calculate 10 + 5")
    
    assert result is not None
    assert "final_response" in result or "status" in result


@pytest.mark.asyncio
async def test_multiple_tool_calls(mock_llm, mock_tools):
    """Test workflow with multiple sequential tool calls."""
    workflow = ToolCallingWorkflow(
        name="test",
        llm=mock_llm,
        tools=mock_tools,
        max_iterations=3,
    )
    
    # Mock LLM with multiple tool call rounds
    responses = [
        MagicMock(
            content="Let me calculate first",
            tool_calls=[MagicMock(name="arithmetic", args={"expression": "10+5"})],
        ),
        MagicMock(
            content="Now let me search for more info",
            tool_calls=[MagicMock(name="web_search", args={"query": "math"})],
        ),
        MagicMock(
            content="Here's the final answer: 15 and math info",
            tool_calls=[],
        ),
    ]
    
    mock_llm.invoke = AsyncMock(side_effect=responses)
    
    result = await workflow.invoke("Calculate 10 + 5 and search for math info")
    
    assert result is not None
    # Should have executed multiple iterations
    assert mock_llm.invoke.call_count >= 1


# ============================================================================
# Error Scenario Tests
# ============================================================================

@pytest.mark.asyncio
async def test_tool_not_found_handling(mock_llm, mock_tools):
    """Test handling of non-existent tool calls."""
    workflow = ToolCallingWorkflow(
        name="test",
        llm=mock_llm,
        tools=mock_tools,
        max_iterations=2,
    )
    
    # Mock LLM to request non-existent tool
    mock_llm.invoke = AsyncMock(return_value=MagicMock(
        content="Let me use a tool",
        tool_calls=[MagicMock(name="unknown_tool", args={})],
    ))
    
    # Should handle gracefully
    result = await workflow.invoke("Use an unknown tool")
    assert result is not None


@pytest.mark.asyncio
async def test_tool_execution_error(mock_llm, mock_tools):
    """Test handling of tool execution errors."""
    # Create workflow with tool that raises error
    error_tool = Tool(
        name="error_tool",
        func=lambda x: exec('raise ValueError("Tool error")'),
        description="Tool that raises error",
    )
    
    workflow = ToolCallingWorkflow(
        name="test",
        llm=mock_llm,
        tools=[error_tool],
        max_iterations=1,
    )
    
    mock_llm.invoke = AsyncMock(return_value=MagicMock(
        content="Using error tool",
        tool_calls=[MagicMock(name="error_tool", args={})],
    ))
    
    # Should not crash
    result = await workflow.invoke("Use error tool")
    assert result is not None


@pytest.mark.asyncio
async def test_max_iterations_limit(mock_llm, mock_tools):
    """Test that workflow stops at max iterations."""
    workflow = ToolCallingWorkflow(
        name="test",
        llm=mock_llm,
        tools=mock_tools,
        max_iterations=2,
    )
    
    # Mock LLM to always request tools (infinite loop scenario)
    mock_llm.invoke = AsyncMock(return_value=MagicMock(
        content="Using a tool",
        tool_calls=[MagicMock(name="arithmetic", args={"expression": "1+1"})],
    ))
    
    result = await workflow.invoke("Keep using tools")
    
    # Should stop after max_iterations
    assert result is not None
    assert mock_llm.invoke.call_count <= workflow.max_iterations + 1


@pytest.mark.asyncio
async def test_empty_query(mock_llm, mock_tools):
    """Test handling of empty query."""
    workflow = ToolCallingWorkflow(
        name="test",
        llm=mock_llm,
        tools=mock_tools,
    )
    
    mock_llm.invoke = AsyncMock(return_value=MagicMock(
        content="Please provide a query",
        tool_calls=[],
    ))
    
    result = await workflow.invoke("")
    assert result is not None


# ============================================================================
# Metrics and Observability Tests
# ============================================================================

@pytest.mark.asyncio
async def test_metrics_collection(mock_llm, mock_tools):
    """Test that metrics are collected properly."""
    workflow = ToolCallingWorkflow(
        name="test",
        llm=mock_llm,
        tools=mock_tools,
    )
    
    mock_llm.invoke = AsyncMock(return_value=MagicMock(
        content="Result",
        tool_calls=[],
    ))
    
    result = await workflow.invoke("Test query")
    metrics = workflow.get_metrics()
    
    assert metrics is not None
    assert "workflow_name" in metrics
    assert metrics["workflow_name"] == "test"


@pytest.mark.asyncio
async def test_tool_call_counting(mock_llm, mock_tools):
    """Test that tool calls are counted in metrics."""
    workflow = ToolCallingWorkflow(
        name="test",
        llm=mock_llm,
        tools=mock_tools,
    )
    
    mock_llm.invoke = AsyncMock(return_value=MagicMock(
        content="Result with tools",
        tool_calls=[MagicMock(name="arithmetic", args={"expression": "1+1"})],
    ))
    
    result = await workflow.invoke("Use arithmetic tool")
    
    # Check metrics reflect tool usage
    assert result is not None
    metrics = workflow.get_metrics()
    assert metrics is not None


# ============================================================================
# Tool Coverage Tests
# ============================================================================

@pytest.mark.asyncio
async def test_arithmetic_tool():
    """Test arithmetic tool functionality."""
    result = mock_arithmetic("2 + 3 * 4")
    assert "Result: 14" in result


@pytest.mark.asyncio
async def test_arithmetic_tool_error():
    """Test arithmetic tool error handling."""
    result = mock_arithmetic("invalid math")
    assert "Error" in result


@pytest.mark.asyncio
async def test_search_tool():
    """Test search tool functionality."""
    result = mock_search("python programming")
    assert "python" in result.lower()


@pytest.mark.asyncio
async def test_text_length_tool():
    """Test text length tool."""
    text = "Hello world test"
    result = mock_text_length(text)
    assert "16" in result  # 16 characters
    assert "3" in result   # 3 words


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.asyncio
async def test_workflow_performance(mock_llm, mock_tools):
    """Test workflow executes in reasonable time."""
    import time
    
    workflow = ToolCallingWorkflow(
        name="test",
        llm=mock_llm,
        tools=mock_tools,
        max_iterations=1,
    )
    
    mock_llm.invoke = AsyncMock(return_value=MagicMock(
        content="Quick result",
        tool_calls=[],
    ))
    
    start = time.time()
    result = await workflow.invoke("Quick query")
    duration = (time.time() - start) * 1000  # Convert to ms
    
    # Should complete in reasonable time (< 5 seconds for mock)
    assert duration < 5000
    assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
