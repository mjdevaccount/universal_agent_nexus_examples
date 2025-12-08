"""
Comprehensive unit tests for self_modifying module.

Target: >70% coverage for promotion to universal-agent-tools@1.1.0
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from _lib.patterns.universal_agent_tools.self_modifying import (
    ExecutionLog,
    ToolGenerationVisitor,
    SelfModifyingAgent,
    deterministic_tool_from_error
)
from universal_agent_nexus.ir import ManifestIR, GraphIR, NodeIR, NodeKind, ToolIR, EdgeIR


class TestExecutionLog:
    """Tests for ExecutionLog dataclass."""

    def test_execution_log_creation(self):
        """Test creating an execution log."""
        log = ExecutionLog(failed_queries=["query1", "query2", "query3"])
        assert len(log.failed_queries) == 3
        assert log.decision_hint is None

    def test_execution_log_with_hint(self):
        """Test creating an execution log with decision hint."""
        log = ExecutionLog(
            failed_queries=["query1"],
            decision_hint="Try different approach"
        )
        assert log.decision_hint == "Try different approach"

    def test_execution_log_empty_queries(self):
        """Test creating an execution log with empty queries."""
        log = ExecutionLog(failed_queries=[])
        assert len(log.failed_queries) == 0


class TestToolGenerationVisitor:
    """Tests for ToolGenerationVisitor."""

    def test_visitor_initialization(self):
        """Test that visitor initializes with empty counts."""
        visitor = ToolGenerationVisitor()
        assert visitor.tool_call_counts == {}

    def test_visit_tool_single(self):
        """Test visiting a single tool."""
        visitor = ToolGenerationVisitor()
        tool = ToolIR(name="test_tool", protocol="mcp", config={})
        
        visitor.visit_tool(tool)
        
        assert visitor.tool_call_counts["test_tool"] == 1

    def test_visit_tool_multiple(self):
        """Test visiting the same tool multiple times."""
        visitor = ToolGenerationVisitor()
        tool = ToolIR(name="test_tool", protocol="mcp", config={})
        
        visitor.visit_tool(tool)
        visitor.visit_tool(tool)
        visitor.visit_tool(tool)
        
        assert visitor.tool_call_counts["test_tool"] == 3

    def test_visit_tool_different_tools(self):
        """Test visiting different tools."""
        visitor = ToolGenerationVisitor()
        tool1 = ToolIR(name="tool1", protocol="mcp", config={})
        tool2 = ToolIR(name="tool2", protocol="mcp", config={})
        
        visitor.visit_tool(tool1)
        visitor.visit_tool(tool2)
        visitor.visit_tool(tool1)
        
        assert visitor.tool_call_counts["tool1"] == 2
        assert visitor.tool_call_counts["tool2"] == 1


class TestDeterministicToolFromError:
    """Tests for deterministic_tool_from_error function."""

    def test_deterministic_tool_creation(self):
        """Test creating a tool from an error message."""
        tool = deterministic_tool_from_error("Connection timeout")
        
        assert isinstance(tool, ToolIR)
        assert tool.protocol == "mcp"
        assert "repair" in tool.name
        assert "connection-timeout" in tool.name.lower()
        assert tool.description == "Auto-generated repair tool derived from execution failures."

    def test_deterministic_tool_config(self):
        """Test that tool has correct configuration."""
        tool = deterministic_tool_from_error("Test error")
        
        assert tool.config["command"] == "python"
        assert tool.config["args"] == ["-m", "mcp_toolkit.repair"]
        assert tool.config["env"]["ERROR_PATTERN"] == "Test error"

    def test_deterministic_tool_name_sanitization(self):
        """Test that error message is sanitized in tool name."""
        tool = deterministic_tool_from_error("Error with 'quotes' and spaces")
        
        # Should remove quotes and spaces, limit length
        assert "'" not in tool.name
        assert " " not in tool.name
        assert len(tool.name) <= len("repair_") + 32  # prefix + max 32 chars

    def test_deterministic_tool_custom_prefix(self):
        """Test creating tool with custom name prefix."""
        tool = deterministic_tool_from_error("Error", name_prefix="fix")
        
        assert tool.name.startswith("fix_")

    def test_deterministic_tool_long_error(self):
        """Test that long error messages are truncated."""
        long_error = "A" * 100
        tool = deterministic_tool_from_error(long_error)
        
        # Name should be limited (prefix + 32 chars max)
        assert len(tool.name) <= len("repair_") + 32
        # But config should have full error
        assert tool.config["env"]["ERROR_PATTERN"] == long_error


class TestSelfModifyingAgent:
    """Tests for SelfModifyingAgent class."""

    @patch("_lib.patterns.universal_agent_tools.self_modifying.parse")
    def test_initialization(self, mock_parse):
        """Test initializing SelfModifyingAgent."""
        mock_manifest = ManifestIR(
            name="test",
            version="1.0.0",
            graphs=[],
            tools=[]
        )
        mock_parse.return_value = mock_manifest
        
        agent = SelfModifyingAgent("test.yaml")
        
        assert agent.manifest_path == "test.yaml"
        assert agent.ir == mock_manifest
        mock_parse.assert_called_once_with("test.yaml")

    @patch("_lib.patterns.universal_agent_tools.self_modifying.parse")
    def test_analyze_and_generate_tool_below_threshold(self, mock_parse):
        """Test that tool is not generated when below threshold."""
        mock_parse.return_value = ManifestIR(name="test", version="1.0.0", graphs=[], tools=[])
        
        agent = SelfModifyingAgent("test.yaml")
        log = ExecutionLog(failed_queries=["query1", "query2"])  # Only 2, threshold is 3
        
        def tool_gen(error: str) -> ToolIR:
            return ToolIR(name="generated", protocol="mcp", config={})
        
        result = agent.analyze_and_generate_tool(log, tool_gen, failure_threshold=3)
        
        assert result is None

    @patch("_lib.patterns.universal_agent_tools.self_modifying.parse")
    def test_analyze_and_generate_tool_at_threshold(self, mock_parse):
        """Test that tool is generated when at threshold."""
        mock_parse.return_value = ManifestIR(name="test", version="1.0.0", graphs=[], tools=[])
        
        agent = SelfModifyingAgent("test.yaml")
        log = ExecutionLog(failed_queries=["q1", "q2", "q3"])  # Exactly 3
        
        def tool_gen(error: str) -> ToolIR:
            return ToolIR(name="generated", protocol="mcp", config={})
        
        result = agent.analyze_and_generate_tool(log, tool_gen, failure_threshold=3)
        
        assert result is not None
        assert result.name == "generated"

    @patch("_lib.patterns.universal_agent_tools.self_modifying.parse")
    def test_analyze_and_generate_tool_uses_last_failure(self, mock_parse):
        """Test that tool generator receives the last failed query."""
        mock_parse.return_value = ManifestIR(name="test", version="1.0.0", graphs=[], tools=[])
        
        agent = SelfModifyingAgent("test.yaml")
        log = ExecutionLog(failed_queries=["q1", "q2", "last_query"])
        
        captured_error = None
        def tool_gen(error: str) -> ToolIR:
            nonlocal captured_error
            captured_error = error
            return ToolIR(name="generated", protocol="mcp", config={})
        
        agent.analyze_and_generate_tool(log, tool_gen, failure_threshold=3)
        
        assert captured_error == "last_query"

    @patch("_lib.patterns.universal_agent_tools.self_modifying.parse")
    def test_register_generated_tool_adds_tool(self, mock_parse):
        """Test that register_generated_tool adds tool to manifest."""
        mock_parse.return_value = ManifestIR(name="test", version="1.0.0", graphs=[], tools=[])
        
        agent = SelfModifyingAgent("test.yaml")
        tool = ToolIR(name="new_tool", protocol="mcp", config={})
        
        # Create a graph with router
        router = NodeIR(id="router", kind=NodeKind.ROUTER, config={})
        graph = GraphIR(name="main", entry_node="router", nodes=[router], edges=[])
        agent.ir.graphs = [graph]
        
        agent.register_generated_tool(tool, "condition")
        
        assert len(agent.ir.tools) == 1
        assert agent.ir.tools[0] == tool

    @patch("_lib.patterns.universal_agent_tools.self_modifying.parse")
    def test_register_generated_tool_creates_node(self, mock_parse):
        """Test that register_generated_tool creates execution node."""
        mock_parse.return_value = ManifestIR(name="test", version="1.0.0", graphs=[], tools=[])
        
        agent = SelfModifyingAgent("test.yaml")
        tool = ToolIR(name="new_tool", protocol="mcp", config={})
        
        router = NodeIR(id="router", kind=NodeKind.ROUTER, config={})
        graph = GraphIR(name="main", entry_node="router", nodes=[router], edges=[])
        agent.ir.graphs = [graph]
        
        agent.register_generated_tool(tool, "condition")
        
        # Check that execution node was added
        exec_node = next(n for n in graph.nodes if n.id == "new_tool_exec")
        assert exec_node is not None
        assert exec_node.kind == NodeKind.TOOL
        assert exec_node.tool_ref == "new_tool"

    @patch("_lib.patterns.universal_agent_tools.self_modifying.parse")
    def test_register_generated_tool_creates_edges(self, mock_parse):
        """Test that register_generated_tool creates edges to router and formatter."""
        mock_parse.return_value = ManifestIR(name="test", version="1.0.0", graphs=[], tools=[])
        
        agent = SelfModifyingAgent("test.yaml")
        tool = ToolIR(name="new_tool", protocol="mcp", config={})
        
        router = NodeIR(id="router", kind=NodeKind.ROUTER, config={})
        formatter = NodeIR(id="formatter", kind=NodeKind.TASK, config={})
        graph = GraphIR(
            name="main",
            entry_node="router",
            nodes=[router, formatter],
            edges=[]
        )
        agent.ir.graphs = [graph]
        
        agent.register_generated_tool(tool, "condition_expr")
        
        # Check edges
        assert len(graph.edges) == 2
        
        # Router to tool edge
        router_edge = next(e for e in graph.edges if e.from_node == "router")
        assert router_edge.to_node == "new_tool_exec"
        assert router_edge.condition["expression"] == "condition_expr"
        
        # Tool to formatter edge
        tool_edge = next(e for e in graph.edges if e.from_node == "new_tool_exec")
        assert tool_edge.to_node == "formatter"

    @patch("_lib.patterns.universal_agent_tools.self_modifying.parse")
    def test_register_generated_tool_no_formatter(self, mock_parse):
        """Test that register_generated_tool works without formatter."""
        mock_parse.return_value = ManifestIR(name="test", version="1.0.0", graphs=[], tools=[])
        
        agent = SelfModifyingAgent("test.yaml")
        tool = ToolIR(name="new_tool", protocol="mcp", config={})
        
        router = NodeIR(id="router", kind=NodeKind.ROUTER, config={})
        graph = GraphIR(name="main", entry_node="router", nodes=[router], edges=[])
        agent.ir.graphs = [graph]
        
        agent.register_generated_tool(tool, "condition")
        
        # Should only have router->tool edge, no tool->formatter
        assert len(graph.edges) == 1
        assert graph.edges[0].from_node == "router"

    @patch("_lib.patterns.universal_agent_tools.self_modifying.parse")
    def test_register_generated_tool_custom_label(self, mock_parse):
        """Test that custom label is used for execution node."""
        mock_parse.return_value = ManifestIR(name="test", version="1.0.0", graphs=[], tools=[])
        
        agent = SelfModifyingAgent("test.yaml")
        tool = ToolIR(name="new_tool", protocol="mcp", config={})
        
        router = NodeIR(id="router", kind=NodeKind.ROUTER, config={})
        graph = GraphIR(name="main", entry_node="router", nodes=[router], edges=[])
        agent.ir.graphs = [graph]
        
        agent.register_generated_tool(tool, "condition", label="Custom Label")
        
        exec_node = next(n for n in graph.nodes if n.id == "new_tool_exec")
        assert exec_node.label == "Custom Label"

    @patch("_lib.patterns.universal_agent_tools.self_modifying.parse")
    def test_register_generated_tool_no_router(self, mock_parse):
        """Test that register_generated_tool skips graphs without router."""
        mock_parse.return_value = ManifestIR(name="test", version="1.0.0", graphs=[], tools=[])
        
        agent = SelfModifyingAgent("test.yaml")
        tool = ToolIR(name="new_tool", protocol="mcp", config={})
        
        # Graph without router
        task = NodeIR(id="task", kind=NodeKind.TASK, config={})
        graph = GraphIR(name="main", entry_node="task", nodes=[task], edges=[])
        agent.ir.graphs = [graph]
        
        agent.register_generated_tool(tool, "condition")
        
        # Tool should still be added, but no nodes/edges
        assert len(agent.ir.tools) == 1
        assert len(graph.nodes) == 1  # Only original task
        assert len(graph.edges) == 0

    @patch("_lib.patterns.universal_agent_tools.self_modifying.parse")
    def test_register_generated_tool_multiple_graphs(self, mock_parse):
        """Test that register_generated_tool processes all graphs."""
        mock_parse.return_value = ManifestIR(name="test", version="1.0.0", graphs=[], tools=[])
        
        agent = SelfModifyingAgent("test.yaml")
        tool = ToolIR(name="new_tool", protocol="mcp", config={})
        
        router1 = NodeIR(id="router1", kind=NodeKind.ROUTER, config={})
        router2 = NodeIR(id="router2", kind=NodeKind.ROUTER, config={})
        graph1 = GraphIR(name="graph1", entry_node="router1", nodes=[router1], edges=[])
        graph2 = GraphIR(name="graph2", entry_node="router2", nodes=[router2], edges=[])
        agent.ir.graphs = [graph1, graph2]
        
        agent.register_generated_tool(tool, "condition")
        
        # Both graphs should have the new node and edges
        assert len(graph1.nodes) == 2  # router + exec node
        assert len(graph2.nodes) == 2
        assert len(graph1.edges) == 1
        assert len(graph2.edges) == 1

    @patch("builtins.open", new_callable=mock_open)
    @patch("_lib.patterns.universal_agent_tools.self_modifying.generate")
    @patch("_lib.patterns.universal_agent_tools.self_modifying.parse")
    def test_compile(self, mock_parse, mock_generate, mock_file):
        """Test compiling the evolved manifest."""
        mock_parse.return_value = ManifestIR(name="test", version="1.0.0", graphs=[], tools=[])
        mock_generate.return_value = "compiled_code_here"
        
        agent = SelfModifyingAgent("test.yaml")
        result = agent.compile("output.py", target="langgraph")
        
        assert result == "output.py"
        mock_generate.assert_called_once_with(agent.ir, target="langgraph")
        mock_file.assert_called_once_with("output.py", "w", encoding="utf-8")

    @patch("builtins.open", new_callable=mock_open)
    @patch("_lib.patterns.universal_agent_tools.self_modifying.generate")
    @patch("_lib.patterns.universal_agent_tools.self_modifying.parse")
    def test_compile_default_target(self, mock_parse, mock_generate, mock_file):
        """Test that compile uses 'langgraph' as default target."""
        mock_parse.return_value = ManifestIR(name="test", version="1.0.0", graphs=[], tools=[])
        mock_generate.return_value = "code"
        
        agent = SelfModifyingAgent("test.yaml")
        agent.compile("output.py")
        
        mock_generate.assert_called_once_with(agent.ir, target="langgraph")

