"""Nested scaffolding example using reusable toolkit primitives."""

from universal_agent_tools.patterns import (
    OrganizationAgentFactory,
    build_organization_manifest as build_manifest,
)


__all__ = ["OrganizationAgentFactory", "build_manifest"]


if __name__ == "__main__":
    from universal_agent_nexus.compiler import compile

    manifest = build_manifest()
    compile(str(manifest), target="langgraph", output="org_agent.py")
