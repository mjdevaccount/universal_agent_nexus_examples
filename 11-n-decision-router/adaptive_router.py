"""Demonstrate dynamic tool injection on top of the N-decision router."""

from tools.universal_agent_tools import (
    DynamicCSVToolInjector,
    RouteDefinition,
    build_decision_agent_manifest,
)
from universal_agent_nexus.compiler import generate
from universal_agent_nexus.ir import ToolIR


def build_base_manifest():
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
        ToolIR(name="data_quality_tool", description="Detect data anomalies and quality issues", protocol="mcp", config={"command": "mcp-data-quality"}),
        ToolIR(name="growth_experiment_tool", description="Run A/B tests and growth experiments", protocol="mcp", config={"command": "mcp-growth-experiments"}),
        ToolIR(name="customer_support_tool", description="Handle customer support requests and triage", protocol="mcp", config={"command": "mcp-support"}),
        ToolIR(name="reporting_tool", description="Generate reports and KPI summaries", protocol="mcp", config={"command": "mcp-reporting"}),
    ]

    return build_decision_agent_manifest(
        agent_name="n-decision-router",
        system_message=(
            "You are the routing coordinator. Classify the user's request into one of:"
            " data_quality, growth_experiment, customer_support, reporting."
            " Respond with only the category name."
        ),
        llm="local://qwen3",
        routes=routes,
        formatter_prompt="Summarize the tool output clearly for the user:\n{result}",
        tools=tools,
    )


def main():
    manifest = build_base_manifest()

    # Dynamically attach CSV-derived tools (e.g., user uploads)
    csv_paths = ["/uploads/leads.csv", "/uploads/experiments.csv"]
    injector = DynamicCSVToolInjector(csv_paths)
    manifest = injector.inject_tools(manifest)

    # Compile to LangGraph Python (string) just to verify the graph is valid
    compiled = generate(manifest, target="langgraph")
    print(f"Injected tools: {injector.injected_tools}")
    print(f"Compiled code lines: {len(compiled.splitlines())}")


if __name__ == "__main__":
    main()
