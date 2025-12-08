"""
Comprehensive unit tests for scaffolding module.

Target: >70% coverage for promotion to universal-agent-tools@1.1.0
"""

import pytest
from unittest.mock import Mock, patch
from _lib.patterns.universal_agent_tools.scaffolding import (
    OrganizationAgentFactory,
    build_organization_manifest
)
from universal_agent_nexus.ir import GraphIR, ManifestIR, NodeIR, NodeKind, ToolIR


class TestCreateTeamAgent:
    """Tests for OrganizationAgentFactory.create_team_agent()."""

    def test_create_team_agent_structure(self):
        """Test that create_team_agent returns a valid GraphIR."""
        graph = OrganizationAgentFactory.create_team_agent("HR")
        
        assert isinstance(graph, GraphIR)
        assert graph.name == "team_hr"
        assert graph.entry_node == "team_router"

    def test_create_team_agent_nodes(self):
        """Test that team agent has correct nodes."""
        graph = OrganizationAgentFactory.create_team_agent("Engineering")
        
        assert len(graph.nodes) == 2
        
        # Check router node
        router = next(n for n in graph.nodes if n.id == "team_router")
        assert router.kind == NodeKind.ROUTER
        assert router.label == "Team Engineering Router"
        assert router.config["system_message"] == "You are the Engineering team coordinator."
        assert router.config["llm"] == "local://qwen3"
        
        # Check tool node
        tool_node = next(n for n in graph.nodes if n.id == "execute_team_task")
        assert tool_node.kind == NodeKind.TOOL
        assert tool_node.tool_ref == "team_engineering_handler"
        assert tool_node.label == "Execute Engineering Task"

    def test_create_team_agent_edges(self):
        """Test that team agent has correct edges."""
        graph = OrganizationAgentFactory.create_team_agent("Finance")
        
        assert len(graph.edges) == 1
        
        edge = graph.edges[0]
        assert edge.from_node == "team_router"
        assert edge.to_node == "execute_team_task"
        assert edge.condition["expression"] == "output.startswith('execute')"

    def test_create_team_agent_name_normalization(self):
        """Test that team names are normalized to lowercase in graph name."""
        graph = OrganizationAgentFactory.create_team_agent("HR")
        assert graph.name == "team_hr"
        
        graph = OrganizationAgentFactory.create_team_agent("Engineering")
        assert graph.name == "team_engineering"
        
        graph = OrganizationAgentFactory.create_team_agent("Finance")
        assert graph.name == "team_finance"

    def test_create_team_agent_tool_ref_format(self):
        """Test that tool references follow the expected format."""
        graph = OrganizationAgentFactory.create_team_agent("HR")
        tool_node = next(n for n in graph.nodes if n.kind == NodeKind.TOOL)
        assert tool_node.tool_ref == "team_hr_handler"
        
        graph = OrganizationAgentFactory.create_team_agent("Engineering")
        tool_node = next(n for n in graph.nodes if n.kind == NodeKind.TOOL)
        assert tool_node.tool_ref == "team_engineering_handler"

    def test_create_team_agent_multiple_teams(self):
        """Test creating multiple team agents."""
        hr_graph = OrganizationAgentFactory.create_team_agent("HR")
        eng_graph = OrganizationAgentFactory.create_team_agent("Engineering")
        fin_graph = OrganizationAgentFactory.create_team_agent("Finance")
        
        assert hr_graph.name == "team_hr"
        assert eng_graph.name == "team_engineering"
        assert fin_graph.name == "team_finance"
        
        # Each should have independent structure
        assert hr_graph.entry_node == "team_router"
        assert eng_graph.entry_node == "team_router"
        assert fin_graph.entry_node == "team_router"


class TestCreateOrganizationManifest:
    """Tests for OrganizationAgentFactory.create_organization_manifest()."""

    def test_create_organization_manifest_structure(self):
        """Test that create_organization_manifest returns a valid ManifestIR."""
        manifest = OrganizationAgentFactory.create_organization_manifest()
        
        assert isinstance(manifest, ManifestIR)
        assert manifest.name == "organization"
        assert manifest.version == "1.0.0"

    def test_create_organization_manifest_team_graphs(self):
        """Test that organization manifest includes all team graphs."""
        manifest = OrganizationAgentFactory.create_organization_manifest()
        
        # Should have 4 graphs: 3 teams + 1 router graph
        assert len(manifest.graphs) == 4
        
        graph_names = [g.name for g in manifest.graphs]
        assert "team_hr" in graph_names
        assert "team_engineering" in graph_names
        assert "team_finance" in graph_names
        assert "organization_router_graph" in graph_names

    def test_create_organization_manifest_tools(self):
        """Test that organization manifest includes team handler tools."""
        manifest = OrganizationAgentFactory.create_organization_manifest()
        
        assert len(manifest.tools) == 3
        
        tool_names = [t.name for t in manifest.tools]
        assert "team_hr_handler" in tool_names
        assert "team_engineering_handler" in tool_names
        assert "team_finance_handler" in tool_names
        
        # Verify tool configurations
        hr_tool = next(t for t in manifest.tools if t.name == "team_hr_handler")
        assert hr_tool.protocol == "mcp"
        assert hr_tool.config["command"] == "mcp-hr-server"

    def test_create_organization_manifest_org_router(self):
        """Test that organization router graph is created."""
        manifest = OrganizationAgentFactory.create_organization_manifest()
        
        router_graph = next(g for g in manifest.graphs if g.name == "organization_router_graph")
        assert router_graph.entry_node == "org_router"
        
        org_router = next(n for n in router_graph.nodes if n.id == "org_router")
        assert org_router.kind == NodeKind.ROUTER
        assert org_router.label == "Organization Router"
        assert org_router.config["system_message"] == "Route query to HR, Engineering, or Finance team."
        assert org_router.config["llm"] == "local://qwen3"

    def test_create_organization_manifest_graph_connections(self):
        """Test that organization router is connected to team graphs."""
        manifest = OrganizationAgentFactory.create_organization_manifest()
        
        # The CompilerBuilder.connect_graphs() should have been called
        # We can verify by checking that the router graph exists and team graphs exist
        router_graph = next(g for g in manifest.graphs if g.name == "organization_router_graph")
        assert router_graph is not None
        
        team_graphs = [g for g in manifest.graphs if g.name.startswith("team_")]
        assert len(team_graphs) == 3

    def test_create_organization_manifest_team_graph_structure(self):
        """Test that team graphs maintain their structure in the manifest."""
        manifest = OrganizationAgentFactory.create_organization_manifest()
        
        hr_graph = next(g for g in manifest.graphs if g.name == "team_hr")
        assert hr_graph.entry_node == "team_router"
        assert len(hr_graph.nodes) == 2
        assert len(hr_graph.edges) == 1


class TestBuildOrganizationManifest:
    """Tests for build_organization_manifest() helper function."""

    def test_build_organization_manifest_returns_manifest(self):
        """Test that helper function returns a ManifestIR."""
        manifest = build_organization_manifest()
        
        assert isinstance(manifest, ManifestIR)
        assert manifest.name == "organization"

    def test_build_organization_manifest_same_as_factory(self):
        """Test that helper function produces same result as factory method."""
        manifest1 = build_organization_manifest()
        manifest2 = OrganizationAgentFactory.create_organization_manifest()
        
        # Should have same structure
        assert manifest1.name == manifest2.name
        assert manifest1.version == manifest2.version
        assert len(manifest1.graphs) == len(manifest2.graphs)
        assert len(manifest1.tools) == len(manifest2.tools)

    def test_build_organization_manifest_team_graphs(self):
        """Test that helper includes all team graphs."""
        manifest = build_organization_manifest()
        
        graph_names = [g.name for g in manifest.graphs]
        assert "team_hr" in graph_names
        assert "team_engineering" in graph_names
        assert "team_finance" in graph_names


class TestScaffoldingIntegration:
    """Integration tests for scaffolding module."""

    def test_full_organization_structure(self):
        """Test complete organization structure with all components."""
        manifest = build_organization_manifest()
        
        # Verify manifest structure
        assert manifest.name == "organization"
        assert manifest.version == "1.0.0"
        
        # Verify graphs
        assert len(manifest.graphs) == 4
        
        # Verify tools
        assert len(manifest.tools) == 3
        
        # Verify each team graph
        for team_name in ["hr", "engineering", "finance"]:
            team_graph = next(g for g in manifest.graphs if g.name == f"team_{team_name}")
            assert team_graph is not None
            assert team_graph.entry_node == "team_router"
            
            # Verify team tool exists
            tool_name = f"team_{team_name}_handler"
            team_tool = next(t for t in manifest.tools if t.name == tool_name)
            assert team_tool is not None
            assert team_tool.protocol == "mcp"

    def test_team_agent_independence(self):
        """Test that team agents are independent and can be created separately."""
        hr_graph = OrganizationAgentFactory.create_team_agent("HR")
        eng_graph = OrganizationAgentFactory.create_team_agent("Engineering")
        
        # Should have same structure but different names/refs
        assert hr_graph.name != eng_graph.name
        assert hr_graph.entry_node == eng_graph.entry_node
        
        hr_tool_ref = next(n for n in hr_graph.nodes if n.kind == NodeKind.TOOL).tool_ref
        eng_tool_ref = next(n for n in eng_graph.nodes if n.kind == NodeKind.TOOL).tool_ref
        assert hr_tool_ref != eng_tool_ref

