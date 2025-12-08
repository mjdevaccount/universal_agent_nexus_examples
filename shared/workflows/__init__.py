"""
Workflow Abstraction Layer

Provides SOLID-based workflow orchestration for LangGraph agents.

Key Concepts:
  - BaseNode: Abstract interface for reusable workflow nodes
  - Workflow: Composes nodes into LangGraph with typed state
  - Common nodes: Intelligence, Extraction, Validation (December 2025 patterns)

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
]

__version__ = "0.1.0"
