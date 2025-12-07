# Universal Agent Tools

Reusable, promotion-ready building blocks extracted from the Local LLM + Tool Server examples. These helpers keep patterns centralized so other examples (or parent repos) can import them directly.

## Modules

- `scaffolding.py` — nested graph utilities (e.g., `OrganizationAgentFactory`, `build_organization_manifest`).
- `enrichment.py` — tenant-aware enrichment handlers and `create_tenant_agent` helper.
- `dynamic_tools.py` — IR visitor helpers for runtime tool creation (e.g., `DynamicCSVToolInjector`).
- `router_patterns.py` — single- and multi-decision router manifest builder (`RouteDefinition`, `build_decision_agent_manifest`).
- `self_modifying.py` — self-evolving agent utilities (`SelfModifyingAgent`, `deterministic_tool_from_error`).
- `mcp_stub.py` — tiny MCP stub server helper (`DictToolServer`) for fast local demos.

## Usage Examples

### Build an organization manifest
```python
from tools.universal_agent_tools import build_organization_manifest

manifest = build_organization_manifest()
```

### Compile a tenant-aware agent
```python
from tools.universal_agent_tools import create_tenant_agent

compiled_path = create_tenant_agent(
    tenant_id="acme-corp",
    tenant_config={"name": "ACME", "retention": 30, "tools": ["research"]},
    base_manifest_path="manifest.yaml",
)
```

### Inject CSV tools at runtime
```python
from tools.universal_agent_tools import DynamicCSVToolInjector
from universal_agent_nexus.compiler import parse

ir = parse("manifest.yaml")
injector = DynamicCSVToolInjector(["/tmp/data/customers.csv"])
ir = injector.inject_tools(ir)
```

### Build a multi-decision router manifest
```python
from tools.universal_agent_tools import RouteDefinition, build_decision_agent_manifest
from universal_agent_nexus.ir import ToolIR

routes = [
    RouteDefinition(
        name="classify_bug",
        tool_ref="bug_triage_tool",
        condition_expression="contains(output, 'bug')",
        label="Send to Bug Triage",
    ),
    RouteDefinition(
        name="feature_request",
        tool_ref="feature_prioritizer",
        condition_expression="contains(output, 'feature')",
    ),
]

tools = [
    ToolIR(name="bug_triage_tool", protocol="mcp", config={"command": "mcp-bugs"}),
    ToolIR(name="feature_prioritizer", protocol="mcp", config={"command": "mcp-features"}),
]

manifest = build_decision_agent_manifest(
    agent_name="issue-director",
    system_message="Route incoming requests to bug triage or feature prioritization.",
    llm="local://qwen3",
    routes=routes,
    tools=tools,
)
```

### Spin up a stub MCP server without boilerplate
```python
from tools.universal_agent_tools import DictToolServer

server = DictToolServer(
    name="billing-mcp",
    tools={
        "get_balance": lambda args: {"balance": 42, "status": "active"},
        "process_payment": lambda args: f"Processed ${args.get('amount', 0)}",
    },
)

server.run_sync()
```

### Evolve an agent from failure logs
```python
from tools.universal_agent_tools import (
    ExecutionLog,
    SelfModifyingAgent,
    deterministic_tool_from_error,
)

agent = SelfModifyingAgent("manifest.yaml")
log = ExecutionLog(
    failed_queries=["Cannot reach billing data source", "Cannot parse CSV file"],
    decision_hint="add_billing_repair",
)

tool = agent.analyze_and_generate_tool(log, deterministic_tool_from_error)
if tool:
    agent.register_generated_tool(
        tool=tool,
        condition_expression="contains(output, 'add_billing_repair')",
        label="Repair Billing Data Source",
    )
    agent.compile("agent_evolved.py")
```
