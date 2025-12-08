"""
Workflow Abstraction Layer

Provides SOLID-based workflow orchestration for LangGraph agents.

Key Concepts:
  - BaseNode: Abstract interface for reusable workflow nodes
  - Workflow: Composes nodes into LangGraph with typed state
  - Common nodes: Intelligence, Extraction, Validation (December 2025 patterns)
  - Helpers: Pre-built workflows (ToolCalling, Conditional, SimpleQA)

Usage Example:
    from shared.workflows import Workflow, IntelligenceNode, ExtractionNode
    from langgraph.graph import StateGraph
    
    workflow = Workflow(
        name="analysis-pipeline",
        state_schema=MyState,
        nodes=[intelligence_node, extraction_node],
        edges=[("intelligence", "extraction")]
    )
    
    result = await workflow.invoke(initial_state)

Helper Workflows:
    from shared.workflows import ToolCallingWorkflow, ConditionalWorkflow
    
    # Tool-calling loop
    tool_workflow = ToolCallingWorkflow(
        name="research",
        llm=llm,
        tools=[search_tool, summarize_tool],
    )
    result = await tool_workflow.invoke("Find latest AI news")
    
    # Conditional branching
    cond_workflow = ConditionalWorkflow(
        name="router",
        state_schema=State,
        decision_node=classifier,
        branches={
            "urgent": [urgent_node],
            "normal": [normal_node],
        }
    )
    result = await cond_workflow.invoke(state)

SOLID Principles:
  - Single Responsibility: Each node does ONE thing
  - Open/Closed: Add nodes/workflows without modifying core
  - Liskov Substitution: All nodes implement BaseNode
  - Interface Segregation: Minimal required interface
  - Dependency Inversion: Depends on abstractions, not implementations
"""

from shared.workflows.nodes import (
    BaseNode,
    NodeExecutionError,
    NodeState,
)

from shared.workflows.common_nodes import (
    IntelligenceNode,
    ExtractionNode,
    ValidationNode,
)

from shared.workflows.workflow import (
    Workflow,
    WorkflowExecutionError,
)

from shared.workflows.helpers import (
    ToolCallingWorkflow,
    ConditionalWorkflow,
    SimpleQAWorkflow,
    ToolCall,
    ConditionalBranchExecution,
)

__all__ = [
    # Core abstractions
    "BaseNode",
    "NodeExecutionError",
    "NodeState",
    "Workflow",
    "WorkflowExecutionError",
    # Common nodes
    "IntelligenceNode",
    "ExtractionNode",
    "ValidationNode",
    # Workflow helpers
    "ToolCallingWorkflow",
    "ConditionalWorkflow",
    "SimpleQAWorkflow",
    "ToolCall",
    "ConditionalBranchExecution",
]

__version__ = "0.2.0"
