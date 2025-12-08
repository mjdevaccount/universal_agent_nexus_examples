"""
Comprehensive unit tests for router_patterns module.

Target: >70% coverage for promotion to universal-agent-tools@1.1.0
"""

import pytest
from _lib.patterns.universal_agent_tools.router_patterns import (
    RouteDefinition,
    build_decision_agent_manifest
)
from universal_agent_nexus.ir import (
    ManifestIR,
    GraphIR,
    NodeIR,
    NodeKind,
    EdgeIR,
    ToolIR
)


class TestRouteDefinition:
    """Tests for RouteDefinition dataclass."""

    def test_route_definition_creation(self):
        """Test creating a route definition with all fields."""
        route = RouteDefinition(
            name="financial",
            tool_ref="financial_analyzer",
            condition_expression="contains(output, 'financial')",
            label="Financial Analysis"
        )
        assert route.name == "financial"
        assert route.tool_ref == "financial_analyzer"
        assert route.condition_expression == "contains(output, 'financial')"
        assert route.label == "Financial Analysis"

    def test_route_definition_optional_label(self):
        """Test that label is optional."""
        route = RouteDefinition(
            name="technical",
            tool_ref="technical_researcher",
            condition_expression="contains(output, 'technical')"
        )
        assert route.name == "technical"
        assert route.label is None

    def test_route_definition_multiple_routes(self):
        """Test creating multiple route definitions."""
        routes = [
            RouteDefinition(
                name="route1",
                tool_ref="tool1",
                condition_expression="condition1"
            ),
            RouteDefinition(
                name="route2",
                tool_ref="tool2",
                condition_expression="condition2",
                label="Route 2"
            )
        ]
        assert len(routes) == 2
        assert routes[0].name == "route1"
        assert routes[1].label == "Route 2"


class TestBuildDecisionAgentManifest:
    """Tests for build_decision_agent_manifest function."""

    def test_build_manifest_single_route(self):
        """Test building manifest with a single route."""
        routes = [
            RouteDefinition(
                name="search",
                tool_ref="search_tool",
                condition_expression="contains(output, 'search')"
            )
        ]
        
        manifest = build_decision_agent_manifest(
            agent_name="search_agent",
            system_message="You are a search assistant.",
            llm="local://qwen3",
            routes=routes
        )
        
        assert isinstance(manifest, ManifestIR)
        assert manifest.name == "search_agent"
        assert manifest.version == "1.0.0"
        assert len(manifest.graphs) == 1
        
        graph = manifest.graphs[0]
        assert graph.name == "main"
        assert graph.entry_node == "analyze_query"
        
        # Check nodes
        node_ids = [node.id for node in graph.nodes]
        assert "analyze_query" in node_ids  # Router
        assert "search_exec" in node_ids  # Tool node
        assert "format_response" in node_ids  # Formatter
        
        # Check router node
        router = next(n for n in graph.nodes if n.id == "analyze_query")
        assert router.kind == NodeKind.ROUTER
        assert router.config["system_message"] == "You are a search assistant."
        assert router.config["llm"] == "local://qwen3"
        
        # Check tool node
        tool_node = next(n for n in graph.nodes if n.id == "search_exec")
        assert tool_node.kind == NodeKind.TOOL
        assert tool_node.tool_ref == "search_tool"
        
        # Check formatter node
        formatter = next(n for n in graph.nodes if n.id == "format_response")
        assert formatter.kind == NodeKind.TASK
        
        # Check edges
        assert len(graph.edges) == 2  # router->tool, tool->formatter
        router_to_tool = next(e for e in graph.edges if e.from_node == "analyze_query")
        assert router_to_tool.to_node == "search_exec"
        assert router_to_tool.condition["expression"] == "contains(output, 'search')"
        
        tool_to_formatter = next(e for e in graph.edges if e.from_node == "search_exec")
        assert tool_to_formatter.to_node == "format_response"

    def test_build_manifest_multiple_routes(self):
        """Test building manifest with multiple routes."""
        routes = [
            RouteDefinition(
                name="financial",
                tool_ref="financial_analyzer",
                condition_expression="contains(output, 'financial')"
            ),
            RouteDefinition(
                name="technical",
                tool_ref="technical_researcher",
                condition_expression="contains(output, 'technical')"
            ),
            RouteDefinition(
                name="general",
                tool_ref="general_assistant",
                condition_expression="True"
            )
        ]
        
        manifest = build_decision_agent_manifest(
            agent_name="multi_route_agent",
            system_message="Route to appropriate tool.",
            llm="local://qwen3",
            routes=routes
        )
        
        graph = manifest.graphs[0]
        
        # Should have 1 router + 3 tool nodes + 1 formatter = 5 nodes
        assert len(graph.nodes) == 5
        
        # Should have 6 edges: 3 router->tool, 3 tool->formatter
        assert len(graph.edges) == 6
        
        # Check all tool nodes exist
        tool_node_ids = [n.id for n in graph.nodes if n.kind == NodeKind.TOOL]
        assert "financial_exec" in tool_node_ids
        assert "technical_exec" in tool_node_ids
        assert "general_exec" in tool_node_ids
        
        # Check all routes have edges from router
        router_edges = [e for e in graph.edges if e.from_node == "analyze_query"]
        assert len(router_edges) == 3
        for route in routes:
            edge = next(e for e in router_edges if e.to_node == f"{route.name}_exec")
            assert edge.condition["expression"] == route.condition_expression

    def test_build_manifest_custom_formatter_prompt(self):
        """Test building manifest with custom formatter prompt."""
        routes = [
            RouteDefinition(
                name="search",
                tool_ref="search_tool",
                condition_expression="True"
            )
        ]
        
        custom_prompt = "Format this result nicely: {result}"
        manifest = build_decision_agent_manifest(
            agent_name="custom_agent",
            system_message="Test",
            llm="local://qwen3",
            routes=routes,
            formatter_prompt=custom_prompt
        )
        
        formatter = next(n for n in manifest.graphs[0].nodes if n.id == "format_response")
        assert formatter.config["prompt"] == custom_prompt

    def test_build_manifest_default_formatter_prompt(self):
        """Test that default formatter prompt is used when not specified."""
        routes = [
            RouteDefinition(
                name="search",
                tool_ref="search_tool",
                condition_expression="True"
            )
        ]
        
        manifest = build_decision_agent_manifest(
            agent_name="default_agent",
            system_message="Test",
            llm="local://qwen3",
            routes=routes
        )
        
        formatter = next(n for n in manifest.graphs[0].nodes if n.id == "format_response")
        assert formatter.config["prompt"] == "Format the tool result for the user: {result}"

    def test_build_manifest_with_tools(self):
        """Test building manifest with additional tool definitions."""
        routes = [
            RouteDefinition(
                name="search",
                tool_ref="search_tool",
                condition_expression="True"
            )
        ]
        
        tools = [
            ToolIR(
                name="search_tool",
                protocol="mcp",
                config={"command": "mcp-search"}
            ),
            ToolIR(
                name="helper_tool",
                protocol="mcp",
                config={"command": "mcp-helper"}
            )
        ]
        
        manifest = build_decision_agent_manifest(
            agent_name="tooled_agent",
            system_message="Test",
            llm="local://qwen3",
            routes=routes,
            tools=tools
        )
        
        assert len(manifest.tools) == 2
        tool_names = [t.name for t in manifest.tools]
        assert "search_tool" in tool_names
        assert "helper_tool" in tool_names

    def test_build_manifest_without_tools(self):
        """Test building manifest without additional tools."""
        routes = [
            RouteDefinition(
                name="search",
                tool_ref="search_tool",
                condition_expression="True"
            )
        ]
        
        manifest = build_decision_agent_manifest(
            agent_name="minimal_agent",
            system_message="Test",
            llm="local://qwen3",
            routes=routes
        )
        
        assert manifest.tools == []

    def test_build_manifest_custom_version(self):
        """Test building manifest with custom version."""
        routes = [
            RouteDefinition(
                name="search",
                tool_ref="search_tool",
                condition_expression="True"
            )
        ]
        
        manifest = build_decision_agent_manifest(
            agent_name="versioned_agent",
            system_message="Test",
            llm="local://qwen3",
            routes=routes,
            version="2.0.0"
        )
        
        assert manifest.version == "2.0.0"

    def test_build_manifest_route_labels(self):
        """Test that route labels are used in tool node labels."""
        routes = [
            RouteDefinition(
                name="search",
                tool_ref="search_tool",
                condition_expression="True",
                label="Custom Search Label"
            )
        ]
        
        manifest = build_decision_agent_manifest(
            agent_name="labeled_agent",
            system_message="Test",
            llm="local://qwen3",
            routes=routes
        )
        
        tool_node = next(n for n in manifest.graphs[0].nodes if n.id == "search_exec")
        assert tool_node.label == "Custom Search Label"

    def test_build_manifest_default_tool_labels(self):
        """Test that default labels are used when route label is not provided."""
        routes = [
            RouteDefinition(
                name="search",
                tool_ref="search_tool",
                condition_expression="True"
            )
        ]
        
        manifest = build_decision_agent_manifest(
            agent_name="default_label_agent",
            system_message="Test",
            llm="local://qwen3",
            routes=routes
        )
        
        tool_node = next(n for n in manifest.graphs[0].nodes if n.id == "search_exec")
        assert tool_node.label == "Execute search"

    def test_build_manifest_description(self):
        """Test that manifest description includes route count."""
        routes = [
            RouteDefinition(name="r1", tool_ref="t1", condition_expression="True"),
            RouteDefinition(name="r2", tool_ref="t2", condition_expression="True"),
            RouteDefinition(name="r3", tool_ref="t3", condition_expression="True")
        ]
        
        manifest = build_decision_agent_manifest(
            agent_name="counted_agent",
            system_message="Test",
            llm="local://qwen3",
            routes=routes
        )
        
        assert "3 routing paths" in manifest.description

    def test_build_manifest_all_nodes_connected(self):
        """Test that all nodes are properly connected in the graph."""
        routes = [
            RouteDefinition(name="route1", tool_ref="tool1", condition_expression="True"),
            RouteDefinition(name="route2", tool_ref="tool2", condition_expression="True")
        ]
        
        manifest = build_decision_agent_manifest(
            agent_name="connected_agent",
            system_message="Test",
            llm="local://qwen3",
            routes=routes
        )
        
        graph = manifest.graphs[0]
        
        # All tool nodes should have an edge from router
        router_edges = [e for e in graph.edges if e.from_node == "analyze_query"]
        assert len(router_edges) == 2
        
        # All tool nodes should have an edge to formatter
        formatter_edges = [e for e in graph.edges if e.to_node == "format_response"]
        assert len(formatter_edges) == 2
        
        # Verify no orphaned nodes
        all_node_ids = {n.id for n in graph.nodes}
        edge_from_nodes = {e.from_node for e in graph.edges}
        edge_to_nodes = {e.to_node for e in graph.edges}
        
        # Router should have outgoing edges
        assert "analyze_query" in edge_from_nodes
        # Formatter should have incoming edges
        assert "format_response" in edge_to_nodes
        # All tool nodes should have both incoming and outgoing edges
        for route in routes:
            tool_id = f"{route.name}_exec"
            assert tool_id in edge_to_nodes  # Has incoming edge
            assert tool_id in edge_from_nodes  # Has outgoing edge

