"""Generate a baseline decision manifest using shared router helpers."""

from dataclasses import asdict
from enum import Enum
from pathlib import Path
import sys

import yaml
from universal_agent_nexus.ir import ToolIR

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
from universal_agent_tools.patterns import RouteDefinition, build_decision_agent_manifest  # noqa: E402


def write_manifest() -> None:
    routes = [
        RouteDefinition(
            name="search_docs",
            tool_ref="doc_search",
            condition_expression="contains(output, 'search_docs')",
            label="Search Documents",
        ),
        RouteDefinition(
            name="calculate_risk",
            tool_ref="risk_calculator",
            condition_expression="contains(output, 'calculate_risk')",
            label="Calculate Risk",
        ),
    ]

    tools = [
        ToolIR(
            name="doc_search",
            protocol="mcp",
            description="Search indexed documents for answers.",
            config={"command": "mcp-doc-search"},
        ),
        ToolIR(
            name="risk_calculator",
            protocol="mcp",
            description="Compute risk scores for a portfolio or request.",
            config={"command": "mcp-risk-calc"},
        ),
    ]

    manifest = build_decision_agent_manifest(
        agent_name="self-modifying-agent",
        system_message="Decide whether to search documents or calculate risk.",
        llm="local://qwen3",
        routes=routes,
        formatter_prompt="Format the result for the user: {result}",
        tools=tools,
    )

    manifest_path = Path(__file__).parent / "manifest.yaml"
    manifest_dict = _to_primitive(asdict(manifest))
    manifest_path.write_text(yaml.safe_dump(manifest_dict, sort_keys=False), encoding="utf-8")
    print(f"✓ Wrote {manifest_path}")


def _to_primitive(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {k: _to_primitive(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_primitive(v) for v in value]
    return value


if __name__ == "__main__":
    write_manifest()
