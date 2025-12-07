"""Generate a minimal customer-support manifest using shared router patterns."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from universal_agent_nexus.ir import ToolIR
from tools.universal_agent_tools import RouteDefinition, build_decision_agent_manifest

SYSTEM_MESSAGE = """
Classify customer issue as:
- "billing" (payment/subscription)
- "technical" (product problems)
- "account" (login/access)
Respond with ONE word only.
"""


def build_manifest():
    routes = [
        RouteDefinition(
            name="billing",
            tool_ref="billing_system",
            condition_expression="contains(output, 'billing')",
            label="Query Billing System",
        ),
        RouteDefinition(
            name="technical",
            tool_ref="tech_support",
            condition_expression="contains(output, 'technical')",
            label="Get Technical Help",
        ),
        RouteDefinition(
            name="account",
            tool_ref="account_service",
            condition_expression="contains(output, 'account')",
            label="Account Operations",
        ),
    ]

    tools = [
        ToolIR(
            name="billing_system",
            description="Billing database operations",
            protocol="mcp",
            config={"command": "python", "args": ["servers.py", "--server", "billing"]},
        ),
        ToolIR(
            name="tech_support",
            description="Technical troubleshooting steps",
            protocol="mcp",
            config={"command": "python", "args": ["servers.py", "--server", "tech"]},
        ),
        ToolIR(
            name="account_service",
            description="Account management actions",
            protocol="mcp",
            config={"command": "python", "args": ["servers.py", "--server", "account"]},
        ),
    ]

    manifest = build_decision_agent_manifest(
        agent_name="customer-support",
        system_message=SYSTEM_MESSAGE,
        llm="local://qwen2.5-32b",
        routes=routes,
        formatter_prompt="Reply to customer issue: {result}",
        tools=tools,
    )
    # Set description manually
    manifest.description = "Minimal single-decision support router backed by MCP stubs."
    return manifest


def write_manifest(path: str = "manifest.yaml") -> None:
    from dataclasses import asdict
    import json

    manifest = build_manifest()
    manifest_dict = json.loads(
        json.dumps(asdict(manifest), default=lambda obj: getattr(obj, "value", str(obj)))
    )

    import yaml

    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(manifest_dict, f, sort_keys=False)


if __name__ == "__main__":
    write_manifest()
    print("✓ Wrote manifest.yaml")
