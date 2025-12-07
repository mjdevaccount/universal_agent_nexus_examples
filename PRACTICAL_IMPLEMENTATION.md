# Universal Agent Nexus: Practical Implementation Examples

## Quick Start: Running Your First Local Agent

### Step 1: Basic Manifest (No Nexus Overhead)

```yaml
# simple_agent.yaml
name: customer-support
version: "1.0.0"

graphs:
  - name: main
    entry_node: classify_issue
    
    nodes:
      - id: classify_issue
        kind: router
        label: "Issue Classifier"
        config:
          llm: "local://qwen2.5:32b"
          system_message: |
            Classify customer issue as:
            - "billing" (payment/subscription)
            - "technical" (product problems)
            - "account" (login/access)
            Respond with ONE word only.
      
      - id: billing_handler
        kind: tool
        tool_ref: billing_system
        label: "Query Billing System"
      
      - id: tech_handler
        kind: tool
        tool_ref: tech_support
        label: "Get Technical Help"
      
      - id: account_handler
        kind: tool
        tool_ref: account_service
        label: "Account Operations"
      
      - id: respond
        kind: task
        label: "Generate Response"
        config:
          prompt: "Reply to customer issue: {context}"
    
    edges:
      - from_node: classify_issue
        to_node: billing_handler
        condition:
          expression: "contains(output, 'billing')"
      
      - from_node: classify_issue
        to_node: tech_handler
        condition:
          expression: "contains(output, 'technical')"
      
      - from_node: classify_issue
        to_node: account_handler
        condition:
          expression: "contains(output, 'account')"
      
      - from_node: billing_handler
        to_node: respond
      - from_node: tech_handler
        to_node: respond
      - from_node: account_handler
        to_node: respond

tools:
  - name: billing_system
    protocol: mcp
    config:
      command: python
      args: ["-m", "billing_server"]
  
  - name: tech_support
    protocol: mcp
    config:
      command: python
      args: ["-m", "tech_server"]
  
  - name: account_service
    protocol: mcp
    config:
      command: python
      args: ["-m", "account_server"]
```

### Step 2: Minimal Python Runner

```python
# run_agent.py
import asyncio
import os
import subprocess
from pathlib import Path

from universal_agent_nexus.adapters.langgraph import LangGraphRuntime, load_manifest

async def main():
    # Load manifest
    manifest = load_manifest("simple_agent.yaml")
    
    # No Postgres needed for local dev
    runtime = LangGraphRuntime(
        postgres_url=None,
        enable_checkpointing=False,
    )
    
    await runtime.initialize(manifest)
    
    # Test query
    result = await runtime.execute(
        execution_id="test-001",
        input_data={
            "context": {
                "query": "I can't log into my account",
            },
        },
    )
    
    print(f"✅ Result: {result['context'].get('last_response')}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 3: Tool Server (MCP)

```python
# billing_server.py
import asyncio
import json
from mcp.server import Server

server = Server("billing-mcp")

# Simulate billing database
BILLING_DB = {
    "user123": {"balance": 100.0, "status": "active"},
    "user456": {"balance": -50.0, "status": "overdue"},
}

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    from mcp.types import TextContent
    
    if name == "get_balance":
        user_id = arguments.get("user_id")
        data = BILLING_DB.get(user_id, {"balance": 0, "status": "unknown"})
        return [TextContent(type="text", text=json.dumps(data))]
    
    elif name == "process_payment":
        user_id = arguments.get("user_id")
        amount = arguments.get("amount", 0)
        if user_id in BILLING_DB:
            BILLING_DB[user_id]["balance"] += amount
            return [TextContent(type="text", text=f"Payment processed: +${amount}")]
        return [TextContent(type="text", text="User not found")]
    
    return [TextContent(type="text", text="Unknown tool")]

# Tool definitions
server._tools = [
    {
        "name": "get_balance",
        "description": "Get user billing balance",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"}
            }
        }
    },
    {
        "name": "process_payment",
        "description": "Process payment for user",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "amount": {"type": "number"}
            }
        }
    }
]

async def main():
    async with server:
        print("✓ Billing MCP server running")
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```

## Advanced: Nested Agents Pattern

### Problem

Single-level agent can't handle organizational hierarchy.

### Solution

Create sub-agent graphs that compose hierarchically.

```python
# nested_agents.py
from universal_agent_nexus.builder import CompilerBuilder
from universal_agent_nexus.ir import ManifestIR, GraphIR, NodeIR, NodeKind, ToolIR, EdgeIR

def create_department_graph(dept_name: str, dept_tools: list) -> GraphIR:
    """Create a sub-graph for a department."""
    
    router = NodeIR(
        id="dept_router",
        kind=NodeKind.ROUTER,
        label=f"{dept_name} Router",
        config={
            "llm": "local://qwen2.5:32b",
            "system_message": f"Route to {dept_name} handler or escalate",
        }
    )
    
    handler = NodeIR(
        id="dept_handler",
        kind=NodeKind.TOOL,
        tool_ref=f"{dept_name.lower()}_tool",
        label=f"Execute {dept_name} Task"
    )
    
    edges = [
        EdgeIR(
            from_node="dept_router",
            to_node="dept_handler",
            condition={"expression": "output.startswith('execute')"}
        )
    ]
    
    return GraphIR(
        name=f"dept_{dept_name.lower()}",
        entry_node="dept_router",
        nodes=[router, handler],
        edges=edges,
    )

def create_org_manifest() -> ManifestIR:
    """Create org-level manifest with sub-departments."""
    
    # Create department graphs
    engineering = create_department_graph("Engineering", ["deploy", "review"])
    sales = create_department_graph("Sales", ["quote", "pipeline"])
    operations = create_department_graph("Operations", ["inventory", "logistics"])
    
    # Create org-level router
    org_router = NodeIR(
        id="org_router",
        kind=NodeKind.ROUTER,
        label="Organization Router",
        config={
            "llm": "local://qwen2.5:32b",
            "system_message": "Route to Engineering, Sales, or Operations",
        }
    )
    
    # Tool definitions
    tools = [
        ToolIR(name="engineering_tool", description="Engineering operations", protocol="mcp", config={"command": "python -m eng_server"}),
        ToolIR(name="sales_tool", description="Sales operations", protocol="mcp", config={"command": "python -m sales_server"}),
        ToolIR(name="operations_tool", description="Operations management", protocol="mcp", config={"command": "python -m ops_server"}),
    ]
    
    return ManifestIR(
        name="organization",
        version="1.0.0",
        description="Multi-department organization agent",
        graphs=[engineering, sales, operations],
        tools=tools,
    )

# Compile
if __name__ == "__main__":
    from universal_agent_nexus.compiler import generate
    
    manifest = create_org_manifest()
    
    # Generate LangGraph code
    compiled_code = generate(manifest, target="langgraph")
    
    with open("nested_agent.py", "w") as f:
        f.write(compiled_code)
    
    print("✓ Generated nested_agent.py")
```

## Advanced: Multi-Tenant Isolation

### Problem

Same manifest for multiple customers = shared memory/data = SECURITY RISK.

### Solution

Enrich manifest with tenant context before compilation.

```python
# multi_tenant.py
from universal_agent_nexus.ir import ManifestIR, parse
from universal_agent_nexus.compiler import generate
from tools.universal_agent_tools import create_tenant_agent
import yaml

def compile_for_tenant(tenant_id: str, tenant_config: dict, base_manifest: str):
    """
    Create isolated agent for specific tenant.
    """
    # Use the reusable helper from universal_agent_tools
    output_path = create_tenant_agent(
        tenant_id=tenant_id,
        tenant_config=tenant_config,
        base_manifest_path=base_manifest,
    )
    
    print(f"✓ Compiled agent for tenant {tenant_id}")
    return output_path

# Usage
tenants = {
    "acme-corp": {
        "org_name": "ACME Corp",
        "data_location": "us-east-1",
    },
    "globex-inc": {
        "org_name": "Globex Inc",
        "data_location": "eu-west-1",
    },
}

for tenant_id, config in tenants.items():
    compile_for_tenant(tenant_id, config, "manifest.yaml")
```

## Advanced: Self-Modifying Agents

### Problem

Agent encounters repeated failures on same operation. What if it could auto-fix?

### Solution

Use IR Visitor to analyze failures, generate new tools dynamically.

```python
# self_modifying_agent.py
from universal_agent_nexus.ir.visitor import DefaultIRVisitor, traverse
from universal_agent_nexus.ir import ManifestIR, ToolIR, NodeIR, NodeKind, EdgeIR
from universal_agent_nexus.compiler import parse, generate
from tools.universal_agent_tools import SelfModifyingAgent, ExecutionLog, deterministic_tool_from_error
import json

# Usage
if __name__ == "__main__":
    # Simulate execution logs with failures
    logs = ExecutionLog(
        failed_queries=[
            "Connection timeout: database unreachable",
            "Connection timeout: database unreachable",
            "Connection timeout: database unreachable",
            "Invalid JSON response: parser error",
            "Invalid JSON response: parser error",
        ],
        decision_hint="add_retry_tool",
    )
    
    agent = SelfModifyingAgent("manifest.yaml")
    
    generated_tool = agent.analyze_and_generate_tool(
        execution_log=logs,
        tool_generator=lambda error: deterministic_tool_from_error(
            error, name_prefix="repair"
        ),
        failure_threshold=3,
    )
    
    if generated_tool:
        agent.register_generated_tool(
            tool=generated_tool,
            condition_expression="contains(output, 'add_retry_tool')",
            label="Retry with Backoff",
        )
        agent.compile("agent_evolved.py")
        print("✨ Agent evolved! Saved to agent_evolved.py")
```

## Advanced: Prompt Caching with Batch Annotations

### Problem

Qwen 32B is fast, but 100 identical queries with same system prompt = token waste.

### Solution

Use Batch Annotations to enable prompt caching.

```python
# batch_agent.py
from universal_agent_nexus.adapters.langgraph import LangGraphRuntime, load_manifest
import asyncio

async def run_batched():
    manifest = load_manifest("manifest.yaml")
    
    runtime = LangGraphRuntime(
        postgres_url=None,
        enable_checkpointing=False,
    )
    
    await runtime.initialize(manifest)
    
    # Execute 100 queries - will be batched automatically if supported
    results = []
    for i in range(100):
        result = await runtime.execute(
            execution_id=f"query-{i}",
            input_data={
                "context": {
                    "query": f"Analyze customer {i}",
                },
            },
        )
        results.append(result)
    
    print(f"✅ Processed {len(results)} queries")

# Run
if __name__ == "__main__":
    asyncio.run(run_batched())
```

## Pattern: How to NOT Use Nexus (Common Mistakes)

### ❌ Mistake 1: Agent Loops

**Bad:**

```python
# Don't do this - agent calls itself repeatedly
for i in range(100):  # WASTE! 100x LLM calls
    response = agent.run(query)
    if "needs_more_info" in response:
        query = agent.refine(response)  # Another call!
```

**Good (with Nexus):**

```yaml
# Single manifest, single decision per run
graphs:
  - name: main
    entry_node: router
    nodes:
      - id: router
        kind: router  # ONE decision
      - id: action_1
        kind: tool
      - id: action_2
        kind: tool
```

### ❌ Mistake 2: Shared State Across Tenants

**Bad:**

```python
# All tenants share same agent = memory leak
agent = Agent("manifest.yaml")
for tenant_id in ["acme", "globex"]:
    result = agent.run(f"Query for {tenant_id}")  # SHARED STATE!
```

**Good (with Nexus):**

```python
# Each tenant gets isolated agent
for tenant_id in ["acme", "globex"]:
    agent_code = compile_for_tenant(tenant_id, "manifest.yaml")
    # Run tenant-specific agent
```

### ❌ Mistake 3: Hardcoding Tool Definitions

**Bad:**

```python
# Tools defined in code = no recompilation
class MyAgent:
    def __init__(self):
        self.tools = ["tool1", "tool2", "tool3"]  # Static
```

**Good (with Nexus):**

```yaml
# Tools in manifest = recompile to change
tools:
  - name: tool1
  - name: tool2
# tools can be injected dynamically via enrichment
```

## Quick Reference

### Compilation Commands

```bash
# Compile to LangGraph (local dev)
nexus compile manifest.yaml --target langgraph --output agent.py

# With optimization
nexus compile manifest.yaml --target langgraph --opt-level aggressive

# Compile for specific tenant (uses enrichment)
python multi_tenant.py acme-corp
```

### Key Files

| File | Purpose | Pattern |
|------|---------|---------|
| `manifest.yaml` | Agent definition (routers, tools, edges) | Single-decision |
| `run_agent.py` | Local execution runner | LangGraph runtime |
| `*_server.py` | MCP tool servers | Tool protocol |
| `multi_tenant.py` | Tenant isolation | Enrichment handlers |
| `self_modifying_agent.py` | Dynamic evolution | IR visitor |

### Environment Setup

```bash
# 1. Install dependencies
pip install universal-agent-nexus[langgraph] ollama mcp

# 2. Start Ollama
ollama pull qwen2.5:32b
ollama serve

# 3. Run agent
python run_agent.py
```

### Debugging

```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Print IR before compilation
from universal_agent_nexus.compiler import parse
ir = parse("manifest.yaml")
print(f"Graphs: {len(ir.graphs)}")
print(f"Tools: {len(ir.tools)}")

# Check node connectivity
for graph in ir.graphs:
    print(f"Graph: {graph.name}")
    for node in graph.nodes:
        print(f"  - {node.id} ({node.kind.value})")
```

