"""
Tests for Workflow Helpers (ToolCalling, Conditional, SimpleQA)

Tests focus on:
- Basic functionality
- Error handling
- Metrics collection
- Integration with base nodes

Run with: pytest tests/test_workflow_helpers.py -v
"""

import asyncio
import pytest
from typing import Any, Dict, List
from unittest.mock import Mock, AsyncMock, patch

from langchain_core.tools import Tool
from langchain_core.language_model import BaseLanguageModel
from langchain_core.messages import AIMessage, ToolMessage

from shared.workflows import (
    ToolCallingWorkflow,
    ConditionalWorkflow,
    SimpleQAWorkflow,
    IntelligenceNode,
    BaseNode,
    ToolCall,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = Mock(spec=BaseLanguageModel)
    return llm


@pytest.fixture
def simple_tools() -> List[Tool]:
    """Create simple test tools."""
    
    def add(a: int, b: int) -> str:
        """Add two numbers."""
        return str(a + b)
    
    def multiply(a: int, b: int) -> str:
        """Multiply two numbers."""
        return str(a * b)
    
    return [
        Tool(name="add", func=add, description="Add two numbers"),
        Tool(name="multiply", func=multiply, description="Multiply two numbers"),
    ]


# ============================================================================
# TOOL CALLING WORKFLOW TESTS
# ============================================================================

class TestToolCallingWorkflow:
    """Tests for ToolCallingWorkflow."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, mock_llm, simple_tools):
        """Test that ToolCallingWorkflow initializes correctly."""
        workflow = ToolCallingWorkflow(
            name="test-workflow",
            llm=mock_llm,
            tools=simple_tools,
            max_iterations=5,
        )
        
        assert workflow.name == "test-workflow"
        assert workflow.max_iterations == 5
        assert len(workflow.tools) == 2
    
    @pytest.mark.asyncio
    async def test_simple_no_tools_query(self, mock_llm, simple_tools):
        """Test query that doesn't require tools."""
        # Mock LLM to return no tool calls
        mock_response = Mock()
        mock_response.content = "The answer is 42."
        mock_response.tool_calls = []
        
        mock_llm.bind_tools.return_value.invoke = Mock(return_value=mock_response)
        
        workflow = ToolCallingWorkflow(
            name="test",
            llm=mock_llm,
            tools=simple_tools,
        )
        
        result = await workflow.invoke("What is the answer?")
        
        assert result["query"] == "What is the answer?"
        assert result["final_response"] == "The answer is 42."
        assert len(result["tool_calls"]) == 0
        assert result["iterations"] == 1
        assert result["metrics"]["success_rate"] == 100.0
    
    @pytest.mark.asyncio
    async def test_max_iterations_limit(self, mock_llm, simple_tools):
        """Test that max_iterations prevents infinite loops."""
        # Mock LLM to always request tools
        mock_response = Mock()
        mock_response.content = ""
        mock_response.tool_calls = [
            {"name": "add", "args": {"a": 1, "b": 2}, "id": "call_1"}
        ]
        
        mock_llm.bind_tools.return_value.invoke = Mock(return_value=mock_response)
        
        workflow = ToolCallingWorkflow(
            name="test",
            llm=mock_llm,
            tools=simple_tools,
            max_iterations=3,
        )
        
        result = await workflow.invoke("Test")
        
        # Should stop after max iterations
        assert result["iterations"] == 3
        assert "Max iterations" in str(result["metrics"]["errors"])
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self, mock_llm, simple_tools):
        """Test that metrics are properly collected."""
        mock_response = Mock()
        mock_response.content = "Done"
        mock_response.tool_calls = []
        
        mock_llm.bind_tools.return_value.invoke = Mock(return_value=mock_response)
        
        workflow = ToolCallingWorkflow(
            name="metrics-test",
            llm=mock_llm,
            tools=simple_tools,
        )
        
        result = await workflow.invoke("Test")
        
        metrics = result["metrics"]
        assert "total_duration_ms" in metrics
        assert "tool_call_count" in metrics
        assert "success_rate" in metrics
        assert "workflow_name" in metrics
        assert metrics["workflow_name"] == "metrics-test"


# ============================================================================
# CONDITIONAL WORKFLOW TESTS
# ============================================================================

class TestConditionalWorkflow:
    """Tests for ConditionalWorkflow."""
    
    @pytest.fixture
    def decision_node(self):
        """Create a mock decision node."""
        node = Mock(spec=BaseNode)
        node.name = "decision"
        node.execute = AsyncMock(return_value={"decision": "branch_a"})
        return node
    
    @pytest.fixture
    def branch_nodes(self):
        """Create mock branch nodes."""
        node_a = Mock(spec=BaseNode)
        node_a.name = "node_a"
        node_a.execute = AsyncMock(return_value={"result": "a"})
        
        node_b = Mock(spec=BaseNode)
        node_b.name = "node_b"
        node_b.execute = AsyncMock(return_value={"result": "b"})
        
        return {"branch_a": [node_a], "branch_b": [node_b]}
    
    @pytest.mark.asyncio
    async def test_initialization(self, decision_node, branch_nodes):
        """Test ConditionalWorkflow initialization."""
        workflow = ConditionalWorkflow(
            name="test",
            state_schema=dict,
            decision_node=decision_node,
            branches=branch_nodes,
        )
        
        assert workflow.name == "test"
        assert len(workflow.branches) == 2
    
    @pytest.mark.asyncio
    async def test_branch_selection(self, decision_node, branch_nodes):
        """Test that correct branch is executed based on decision."""
        workflow = ConditionalWorkflow(
            name="test",
            state_schema=dict,
            decision_node=decision_node,
            branches=branch_nodes,
        )
        
        result = await workflow.invoke({"input": "test"})
        
        assert result["decision"] == "branch_a"
        assert result["branch_executed"] == "branch_a"
        assert result["state"]["result"] == "a"
    
    @pytest.mark.asyncio
    async def test_unknown_branch_error(self, decision_node, branch_nodes):
        """Test handling of unknown branch selection."""
        # Decision returns unknown branch
        decision_node.execute = AsyncMock(return_value={"decision": "unknown"})
        
        workflow = ConditionalWorkflow(
            name="test",
            state_schema=dict,
            decision_node=decision_node,
            branches=branch_nodes,
        )
        
        result = await workflow.invoke({"input": "test"})
        
        assert result["branch_executed"] is None
        assert "Unknown branch" in str(result["error"])
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self, decision_node, branch_nodes):
        """Test that metrics are collected."""
        workflow = ConditionalWorkflow(
            name="cond-test",
            state_schema=dict,
            decision_node=decision_node,
            branches=branch_nodes,
        )
        
        result = await workflow.invoke({"input": "test"})
        
        metrics = result["metrics"]
        assert "total_duration_ms" in metrics
        assert "branch_duration_ms" in metrics
        assert "decision" in metrics
        assert "branch_executed" in metrics
        assert metrics["workflow_name"] == "cond-test"


# ============================================================================
# SIMPLE QA WORKFLOW TESTS
# ============================================================================

class TestSimpleQAWorkflow:
    """Tests for SimpleQAWorkflow."""
    
    @pytest.fixture
    def qa_llm(self):
        """Create mock LLM for QA."""
        llm = Mock(spec=BaseLanguageModel)
        response = Mock()
        response.content = "This is the answer."
        llm.invoke = Mock(return_value=response)
        return llm
    
    @pytest.mark.asyncio
    async def test_initialization(self, qa_llm):
        """Test SimpleQAWorkflow initialization."""
        workflow = SimpleQAWorkflow(
            name="qa",
            llm=qa_llm,
            system_prompt="You are helpful.",
        )
        
        assert workflow.name == "qa"
        assert workflow.system_prompt == "You are helpful."
    
    @pytest.mark.asyncio
    async def test_simple_query(self, qa_llm):
        """Test simple Q&A."""
        workflow = SimpleQAWorkflow(
            name="qa",
            llm=qa_llm,
        )
        
        result = await workflow.invoke("What is Python?")
        
        assert result["query"] == "What is Python?"
        assert result["answer"] == "This is the answer."
        assert result["metrics"]["success"] is True
    
    @pytest.mark.asyncio
    async def test_error_handling(self, qa_llm):
        """Test error handling in QA."""
        qa_llm.invoke = Mock(side_effect=Exception("LLM error"))
        
        workflow = SimpleQAWorkflow(
            name="qa",
            llm=qa_llm,
        )
        
        result = await workflow.invoke("What is Python?")
        
        assert result["answer"] is None
        assert result["error"] is not None
        assert result["metrics"]["success"] is False


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple components."""
    
    @pytest.mark.asyncio
    async def test_tool_call_dataclass(self):
        """Test ToolCall dataclass."""
        call = ToolCall(
            tool_name="test_tool",
            tool_input={"a": 1},
            tool_result="result",
            duration_ms=100.0,
            success=True,
        )
        
        assert call.tool_name == "test_tool"
        assert call.success is True
        assert call.duration_ms == 100.0
    
    @pytest.mark.asyncio
    async def test_tool_call_with_error(self):
        """Test ToolCall with error."""
        call = ToolCall(
            tool_name="test_tool",
            tool_input={},
            tool_result="",
            duration_ms=50.0,
            success=False,
            error="Tool execution failed",
        )
        
        assert call.success is False
        assert call.error == "Tool execution failed"


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Performance tests for workflow helpers."""
    
    @pytest.mark.asyncio
    async def test_tool_calling_overhead(self, mock_llm):
        """Test that ToolCallingWorkflow overhead is minimal."""
        # Simple no-tool query should complete quickly
        mock_response = Mock()
        mock_response.content = "Quick answer"
        mock_response.tool_calls = []
        
        mock_llm.bind_tools.return_value.invoke = Mock(return_value=mock_response)
        
        workflow = ToolCallingWorkflow(
            name="perf",
            llm=mock_llm,
            tools=[],
        )
        
        result = await workflow.invoke("Quick question")
        
        # Should complete in reasonable time (< 5 seconds)
        assert result["metrics"]["total_duration_ms"] < 5000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
