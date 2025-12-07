"""Reusable router construction patterns for single- and multi-decision agents."""

from dataclasses import dataclass
from typing import List, Optional

from universal_agent_nexus.ir import EdgeIR, GraphIR, ManifestIR, NodeIR, NodeKind, ToolIR


@dataclass
class RouteDefinition:
    """Defines a routing target for a decision node."""

    name: str
    tool_ref: str
    condition_expression: str
    label: Optional[str] = None


def build_decision_agent_manifest(
    agent_name: str,
    system_message: str,
    llm: str,
    routes: List[RouteDefinition],
    formatter_prompt: str = "Format the tool result for the user: {result}",
    tools: Optional[List[ToolIR]] = None,
    version: str = "1.0.0",
) -> ManifestIR:
    """Create a manifest with a single decision node that can route to N tools.

    Args:
        agent_name: Display and manifest name.
        system_message: System prompt for the router node.
        llm: LLM reference (e.g., ``local://qwen2.5-32b``).
        routes: A list of RouteDefinition objects describing each decision path.
        formatter_prompt: Prompt used by the final formatting task.
        tools: Optional tool definitions to include with the manifest.
        version: Manifest version string.

    Returns:
        A ManifestIR ready for compilation to LangGraph, AWS, or MCP runtimes.
    """

    router_node = NodeIR(
        id="analyze_query",
        kind=NodeKind.ROUTER,
        label="Decision Router",
        config={"system_message": system_message, "llm": llm},
    )

    format_node = NodeIR(
        id="format_response",
        kind=NodeKind.TASK,
        label="Format Response",
        config={"prompt": formatter_prompt},
    )

    tool_nodes: List[NodeIR] = []
    edges: List[EdgeIR] = []

    for route in routes:
        node_id = f"{route.name}_exec"
        tool_nodes.append(
            NodeIR(
                id=node_id,
                kind=NodeKind.TOOL,
                tool_ref=route.tool_ref,
                label=route.label or f"Execute {route.name}",
            )
        )

        edges.append(
            EdgeIR(
                from_node=router_node.id,
                to_node=node_id,
                condition={"expression": route.condition_expression},
            )
        )

        edges.append(EdgeIR(from_node=node_id, to_node=format_node.id))

    graph = GraphIR(
        name="main",
        entry_node=router_node.id,
        nodes=[router_node, *tool_nodes, format_node],
        edges=edges,
    )

    return ManifestIR(
        name=agent_name,
        version=version,
        description=f"Decision router agent with {len(routes)} routing paths",
        graphs=[graph],
        tools=tools or [],
    )


__all__ = ["RouteDefinition", "build_decision_agent_manifest"]
