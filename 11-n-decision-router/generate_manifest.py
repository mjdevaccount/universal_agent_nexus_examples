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
        ToolIR(name="data_quality_tool", protocol="mcp", config={"command": "mcp-data-quality", "args": ["--mode", "anomaly"]}),
        ToolIR(name="growth_experiment_tool", protocol="mcp", config={"command": "mcp-growth-experiments", "args": ["--llm", "local://qwen2.5-32b"]}),
        ToolIR(name="customer_support_tool", protocol="mcp", config={"command": "mcp-support", "args": ["--kb", "/data/kb.sqlite"]}),
        ToolIR(name="reporting_tool", protocol="mcp", config={"command": "mcp-reporting", "args": ["--metrics", "weekly"]}),
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


def main():
    manifest = build_manifest()
    with open("manifest.yaml", "w", encoding="utf-8") as handle:
        yaml.safe_dump(manifest.model_dump(), handle, sort_keys=False)
    print("✓ manifest.yaml regenerated from router helper")


if __name__ == "__main__":
    main()
