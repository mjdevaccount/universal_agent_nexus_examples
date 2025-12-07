"""Reusable scaffolding utilities for nested agent graphs."""

from universal_agent_nexus.builder import CompilerBuilder
from universal_agent_nexus.ir import EdgeIR, GraphIR, ManifestIR, NodeIR, NodeKind, ToolIR


class OrganizationAgentFactory:
    """Creates hierarchical agent scaffolding with team sub-graphs."""

    @staticmethod
    def create_team_agent(team_name: str) -> GraphIR:
        """Create a graph for a specific team (HR, Engineering, Finance)."""
        nodes = [
            NodeIR(
                id="team_router",
                kind=NodeKind.ROUTER,
                label=f"Team {team_name} Router",
                config={
                    "system_message": f"You are the {team_name} team coordinator.",
                    "llm": "local://qwen2.5-32b",
                },
            ),
            NodeIR(
                id="execute_team_task",
                kind=NodeKind.TOOL,
                tool_ref=f"team_{team_name.lower()}_handler",
                label=f"Execute {team_name} Task",
            ),
        ]

        edges = [
            EdgeIR(
                from_node="team_router",
                to_node="execute_team_task",
                condition={"expression": "output.startswith('execute')"},
            )
        ]

        return GraphIR(
            name=f"team_{team_name.lower()}",
            entry_node="team_router",
            nodes=nodes,
            edges=edges,
        )

    @staticmethod
    def create_organization_manifest() -> ManifestIR:
        """Create top-level org agent that routes to teams."""

        # Create team sub-graphs
        hr_team = OrganizationAgentFactory.create_team_agent("HR")
        eng_team = OrganizationAgentFactory.create_team_agent("Engineering")
        fin_team = OrganizationAgentFactory.create_team_agent("Finance")

        # Create org-level router
        org_router = NodeIR(
            id="org_router",
            kind=NodeKind.ROUTER,
            label="Organization Router",
            config={
                "system_message": "Route query to HR, Engineering, or Finance team.",
                "llm": "local://qwen2.5-32b",
            },
        )

        # Tool definitions for team executors
        tools = [
            ToolIR(
                name="team_hr_handler",
                protocol="mcp",
                config={"command": "mcp-hr-server"},
            ),
            ToolIR(
                name="team_engineering_handler",
                protocol="mcp",
                config={"command": "mcp-eng-server"},
            ),
            ToolIR(
                name="team_finance_handler",
                protocol="mcp",
                config={"command": "mcp-fin-server"},
            ),
        ]

        # Assembly
        manifest = ManifestIR(
            name="organization",
            version="1.0.0",
            graphs=[hr_team, eng_team, fin_team],
            tools=tools,
        )

        # Link org router to team graphs using CompilerBuilder mixins
        builder = CompilerBuilder(manifest)
        builder.add_graph(
            GraphIR(
                name="organization_router_graph",
                entry_node="org_router",
                nodes=[org_router],
                edges=[],
            )
        )
        builder.connect_graphs("organization_router_graph", hr_team.name)
        builder.connect_graphs("organization_router_graph", eng_team.name)
        builder.connect_graphs("organization_router_graph", fin_team.name)
        return builder.manifest


def build_organization_manifest() -> ManifestIR:
    """Helper for tests and documentation snippets."""

    return OrganizationAgentFactory.create_organization_manifest()
