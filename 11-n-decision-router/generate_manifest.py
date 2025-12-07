"""Programmatically rebuild the N-decision manifest using reusable router helpers."""

import yaml
from universal_agent_nexus.ir import ToolIR

from tools.universal_agent_tools import RouteDefinition, build_decision_agent_manifest


def build_manifest():
    routes = [
        RouteDefinition(
            name="data_quality",
            tool_ref="data_quality_tool",
            condition_expression="contains(output, 'data_quality')",
            label="Execute Data Quality",
        ),
        RouteDefinition(
            name="growth_experiment",
            tool_ref="growth_experiment_tool",
            condition_expression="contains(output, 'growth_experiment')",
            label="Execute Growth Experiment",
        ),
        RouteDefinition(
            name="customer_support",
            tool_ref="customer_support_tool",
            condition_expression="contains(output, 'customer_support')",
            label="Execute Customer Support",
        ),
        RouteDefinition(
            name="reporting",
            tool_ref="reporting_tool",
            condition_expression="contains(output, 'reporting')",
            label="Execute Reporting",
        ),
    ]

    tools = [
        ToolIR(name="data_quality_tool", description="Detect data anomalies and quality issues", protocol="mcp", config={"command": "mcp-data-quality", "args": ["--mode", "anomaly"]}),
        ToolIR(name="growth_experiment_tool", description="Run A/B tests and growth experiments", protocol="mcp", config={"command": "mcp-growth-experiments", "args": ["--llm", "local://qwen2.5-32b"]}),
        ToolIR(name="customer_support_tool", description="Handle customer support requests and triage", protocol="mcp", config={"command": "mcp-support", "args": ["--kb", "/data/kb.sqlite"]}),
        ToolIR(name="reporting_tool", description="Generate reports and KPI summaries", protocol="mcp", config={"command": "mcp-reporting", "args": ["--metrics", "weekly"]}),
    ]

    manifest = build_decision_agent_manifest(
        agent_name="n-decision-router",
        system_message=(
            "You are the routing coordinator. Classify the user's request into one of:"
            " data_quality, growth_experiment, customer_support, reporting."
            " Respond with only the category name."
        ),
        llm="local://qwen2.5-32b",
        routes=routes,
        formatter_prompt="Summarize the tool output clearly for the user:\n{result}",
        tools=tools,
    )

    return manifest


def manifest_to_dict(manifest):
    """Convert ManifestIR to dictionary for YAML serialization."""
    return {
        "name": manifest.name,
        "version": manifest.version,
        "description": manifest.description,
        "graphs": [
            {
                "name": graph.name,
                "entry_node": graph.entry_node,
                "nodes": [
                    {
                        "id": node.id,
                        "kind": node.kind.value if hasattr(node.kind, 'value') else str(node.kind),
                        "label": node.label,
                        "tool_ref": node.tool_ref if hasattr(node, 'tool_ref') else None,
                        "config": node.config if hasattr(node, 'config') else {},
                    }
                    for node in graph.nodes
                ],
                "edges": [
                    {
                        "from_node": edge.from_node,
                        "to_node": edge.to_node,
                        "condition": (
                            {
                                "expression": (
                                    edge.condition.expression
                                    if hasattr(edge.condition, 'expression')
                                    else edge.condition.get('expression') if isinstance(edge.condition, dict) else None
                                ),
                            }
                            if hasattr(edge, 'condition') and edge.condition
                            else None
                        ),
                    }
                    for edge in graph.edges
                ],
            }
            for graph in manifest.graphs
        ],
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "protocol": tool.protocol,
                "config": tool.config,
            }
            for tool in manifest.tools
        ],
    }


def main():
    manifest = build_manifest()
    manifest_dict = manifest_to_dict(manifest)
    # Remove None values for cleaner YAML
    def clean_dict(d):
        if isinstance(d, dict):
            return {k: clean_dict(v) for k, v in d.items() if v is not None}
        elif isinstance(d, list):
            return [clean_dict(item) for item in d]
        return d
    
    manifest_dict = clean_dict(manifest_dict)
    
    with open("manifest.yaml", "w", encoding="utf-8") as handle:
        yaml.safe_dump(manifest_dict, handle, sort_keys=False, default_flow_style=False)
    print("✓ manifest.yaml regenerated from router helper")


if __name__ == "__main__":
    main()
