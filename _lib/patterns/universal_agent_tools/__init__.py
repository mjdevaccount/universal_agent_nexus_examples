"""Reusable agent-building patterns for Universal Agent Nexus examples."""

from .dynamic_tools import DynamicCSVToolInjector
from .enrichment import TenantIsolationHandler, VectorDBIsolationHandler, create_tenant_agent
from .router_patterns import RouteDefinition, build_decision_agent_manifest
from .scaffolding import OrganizationAgentFactory, build_organization_manifest
from .self_modifying import (
    ExecutionLog,
    SelfModifyingAgent,
    ToolGenerationVisitor,
    deterministic_tool_from_error,
)

__all__ = [
    "OrganizationAgentFactory",
    "build_organization_manifest",
    "TenantIsolationHandler",
    "VectorDBIsolationHandler",
    "create_tenant_agent",
    "RouteDefinition",
    "build_decision_agent_manifest",
    "DynamicCSVToolInjector",
    "ExecutionLog",
    "SelfModifyingAgent",
    "ToolGenerationVisitor",
    "deterministic_tool_from_error",
    "DictToolServer",
    "ToolHandler",
]


def __getattr__(name):
    if name in {"DictToolServer", "ToolHandler"}:
        from .mcp_stub import DictToolServer, ToolHandler

        return {"DictToolServer": DictToolServer, "ToolHandler": ToolHandler}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
