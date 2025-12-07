# Universal Agent Nexus - API Reference

**Master documentation for the Universal Agent Nexus platform.**

This document captures discoveries, patterns, and API usage as the platform is developed and used.

---

## Table of Contents

1. [Tool Discovery](#tool-discovery)
2. [Compiler Usage](#compiler-usage)
3. [Runtime Integration](#runtime-integration)
4. [MCP Server Integration](#mcp-server-integration)
5. [Workflow Patterns](#workflow-patterns)

---

## Tool Discovery

### Tool Registry

The `tools/registry/tool_registry.py` provides centralized tool discovery.

**Basic Usage:**
```python
from tools.registry.tool_registry import get_registry

registry = get_registry()

# Register MCP servers
registry.register_server("filesystem", "http://localhost:8000/mcp")
registry.register_server("git", "http://localhost:8001/mcp")

# Discover tools
tools = registry.discover_tools()

# Access discovered tools
for tool in registry.list_tools():
    print(f"{tool.name}: {tool.description}")
```

**Tool Definition Structure:**
```python
class ToolDefinition:
    name: str                    # Tool name (e.g., "read_file")
    description: str             # Human-readable description
    server_url: str             # MCP server URL
    server_name: str            # Server identifier
    input_schema: dict          # JSON Schema for inputs
    protocol: str = "mcp"       # Protocol type
```

### MCP Server Discovery

MCP servers must implement the `/tools` endpoint for introspection:

```python
@app.get("/mcp/tools")
async def list_tools():
    return {
        "tools": [
            {
                "name": "tool_name",
                "description": "Tool description",
                "inputSchema": {
                    "type": "object",
                    "properties": {...},
                    "required": [...]
                }
            }
        ]
    }
```

**Discovery Process:**
1. Registry queries `/tools` endpoint on each registered server
2. Tools are parsed into `ToolDefinition` objects
3. Tools are cached in registry for reuse

---

## Compiler Usage

### Basic Compilation

```bash
nexus compile manifest.yaml --target langgraph --output agent.py
```

**Target Options:**
- `langgraph` - Local development with LangGraph
- `aws` - AWS Step Functions deployment
- `mcp` - MCP server output

### Dynamic Compilation

The compiler can be invoked programmatically:

```python
from universal_agent_nexus.compiler import compile_manifest

# Load manifest
with open("manifest.yaml", 'r') as f:
    manifest = yaml.safe_load(f)

# Compile to LangGraph
result = compile_manifest(manifest, target="langgraph")
```

**Note:** Actual API may vary - this is based on expected usage patterns.

---

## Runtime Integration

### LangGraph Runtime

Example 08 demonstrates LangGraph integration with MCP tools:

```python
from runtime.agent_runtime import MCPToolLoader, create_agent_graph

# Load tools from MCP servers
filesystem_tools = MCPToolLoader.load_from_server("http://localhost:8000/mcp")
git_tools = MCPToolLoader.load_from_server("http://localhost:8001/mcp")
all_tools = filesystem_tools + git_tools

# Create agent graph
agent = create_agent_graph(all_tools, llm)

# Execute
result = agent.invoke({
    "messages": [HumanMessage(content="Read main.py")]
})
```

### MCP Tool Loader

The `MCPToolLoader` class provides:
- Auto-discovery via `/tools` endpoint
- Conversion to LangChain `BaseTool` objects
- HTTP-based tool execution

**Tool Execution:**
Tools are executed via HTTP POST to `/mcp/tools/{tool_name}`:

```python
response = httpx.post(
    f"{server_url}/tools/{tool_name}",
    json=tool_args,
    timeout=10
)
```

---

## MCP Server Integration

### Server Structure

MCP servers follow this structure:

```
mcp_servers/
├── {server_name}/
│   ├── server.py          # FastAPI server
│   └── README.md          # Server documentation
```

### Server Implementation Pattern

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="MCP Server Name")

# Tool definitions for introspection
TOOLS = [
    {
        "name": "tool_name",
        "description": "Tool description",
        "inputSchema": {...}
    }
]

@app.get("/mcp/tools")
async def list_tools():
    return {"tools": TOOLS}

@app.post("/mcp/tools/{tool_name}")
async def execute_tool(tool_name: str, request: ToolRequest):
    # Tool implementation
    return {"content": "result"}
```

### Standard Endpoints

All MCP servers should implement:
- `GET /mcp/tools` - List available tools (introspection)
- `POST /mcp/tools/{tool_name}` - Execute specific tool
- `GET /health` - Health check

---

## Workflow Patterns

### Discovery-Driven Workflow

Example 09 (AutonomousFlow) demonstrates discovery-driven workflow generation:

1. **Discovery**: Query MCP servers for available tools
2. **Regeneration**: Update manifest with discovered tools
3. **Compilation**: Compile regenerated manifest to runtime
4. **Execution**: Run agent with discovered capabilities

**Pattern:**
```python
# 1. Discover
registry = get_registry()
tools = registry.discover_tools()

# 2. Regenerate manifest
manifest['tools'] = [convert_to_manifest_format(tool) for tool in tools]

# 3. Compile
nexus compile regenerated_manifest.yaml --target langgraph

# 4. Execute
python generated_agent.py
```

### Tool-Based Node Generation

When tools are discovered, nodes can be generated:

```yaml
nodes:
  - id: use_read_file
    kind: tool
    tool_ref: "read_file"
    config:
      input_mapping:
        path: "{file_path}"
```

---

## Discoveries & Notes

### As of Initial Implementation

1. **Tool Discovery**: MCP servers must implement `/tools` endpoint for introspection
2. **Registry Pattern**: Centralized registry enables dynamic workflow generation
3. **Compiler Integration**: Compiler can be invoked programmatically for dynamic workflows
4. **LangGraph Integration**: MCP tools integrate seamlessly via `MCPToolLoader`
5. **Ollama Function Calling**: Some models support `bind_tools`, others require manual tool calling

### Known Limitations

1. Compiler CLI may have import errors (needs investigation)
2. Tool execution is synchronous via HTTP (async support may vary)
3. Tool discovery requires servers to be running

### Future Enhancements

1. Automatic workflow optimization based on tool capabilities
2. Tool capability matching and recommendation
3. Multi-agent coordination with shared tool registry
4. Tool versioning and compatibility checking

---

## Examples Reference

| Example | Purpose | Key Pattern |
|---------|---------|-------------|
| 01-hello-world | Basic manifest structure | Simple task node |
| 06-playground-simulation | Multi-agent interaction | Agent archetypes |
| 07-innovation-waves | Multi-runtime demo | Same YAML → 5 runtimes |
| 08-local-agent-runtime | MCP + LangGraph + Ollama | Tool integration |
| 09-autonomous-flow | Dynamic workflow discovery | Discovery → Compile → Execute |

---

## Contributing

As you discover new patterns, APIs, or usage examples, document them here. This is a living document that grows with the platform.

**Documentation Guidelines:**
- Include code examples
- Note any gotchas or limitations
- Reference specific examples when relevant
- Keep patterns practical and tested

---

## Runtime Execution

### AutonomousFlow Pattern

Example 09 demonstrates the complete discovery → compile → execute cycle:

**1. Discovery Phase:**
```python
from tools.registry.tool_registry import get_registry

registry = get_registry()
registry.register_server("filesystem", "http://localhost:8000/mcp")
tools = registry.discover_tools()  # Discovers 7 tools
```

**2. Regeneration Phase:**
```python
# Manifest is regenerated with discovered tools
manifest['tools'] = [convert_to_manifest_format(tool) for tool in tools]
# Saved to autonomous_flow_regenerated.yaml
```

**3. Runtime Phase:**
```python
# Load regenerated manifest
manifest = load_regenerated_manifest()

# Create runtime from manifest
agent, tools = create_runtime_from_manifest(manifest)

# Execute
result = agent.invoke({"messages": [HumanMessage(content="task")]})
```

### Tool Deduplication

When loading tools from multiple servers, deduplicate:

```python
seen_servers = set()
seen_tools = set()

for tool_config in manifest['tools']:
    server_url = tool_config['config']['server_url']
    if server_url not in seen_servers:
        tools = MCPToolLoader.load_from_server(server_url)
        seen_servers.add(server_url)
        for tool in tools:
            if tool.name not in seen_tools:
                all_tools.append(tool)
                seen_tools.add(tool.name)
```

---

## MCP Protocol & Tool Discovery

### Understanding MCP

**Model Context Protocol (MCP)** is a standardized protocol for AI tools. It's **not platform-specific** - it's an open protocol.

**Key Points:**
- MCP servers are **standalone processes** (not tied to Cursor or any specific client)
- Our servers use **HTTP transport** (ports 8000, 8001)
- Any MCP-compliant client can use them
- Protocol is standardized (November 2025 spec)

**Current Setup:**
- Standalone FastAPI servers from Example 08
- Running independently on localhost
- MCP-compliant endpoints (`/mcp/tools`, `/mcp/tools/{name}`)
- Discoverable via HTTP introspection

## Available Tools (Running Servers)

### Currently Discoverable Tools

**Filesystem Server** (`http://localhost:8000`):
- `read_file` - Read file contents
- `write_file` - Write content to file
- `list_directory` - List directory contents
- `search_code` - Search for code patterns

**Git Server** (`http://localhost:8001`):
- `git_status` - Get repository status
- `git_commit` - Create a commit
- `git_diff` - Get diff of changes

**Qdrant Server** (`http://localhost:8002`):
- `chunk_and_store_python` - Chunk Python files using AST and store in Qdrant
- `store_text` - Store text in Qdrant vector database
- `search_qdrant` - Search Qdrant vector database
- `list_collections` - List all Qdrant collections

**GitHub Server** (`http://localhost:8003`):
- `github_get_file` - Get file contents from repository
- `github_list_files` - List files in repository
- `github_create_issue` - Create GitHub issue
- `github_list_issues` - List repository issues
- `github_search_repos` - Search repositories

**Total:** 16 tools available for discovery (11 currently discovered)

These servers are running and can be discovered automatically via the tool registry.

---

## Known Issues & Workarounds

### Nexus Compiler Import Error

**Issue:** `ImportError: cannot import name 'AWSStepFunctionsCompiler'`

**Status:** Compiler has import error in AWS adapter. Workaround: Use direct runtime creation from manifest.

**Workaround:**
```python
# Instead of: nexus compile manifest.yaml --target langgraph
# Use: Direct runtime creation from manifest (see Example 09 runtime)
```

### Tool Calling with Ollama

**Issue:** Some Ollama models don't support `bind_tools()` natively.

**Status:** Tool recognition works, but automatic tool calling may require manual prompting.

**Workaround:**
- Use models that support function calling (llama3.2:11b, qwen2.5:7b)
- Or implement manual tool calling based on LLM responses

---

## Infrastructure Setup

### Postgres for LangGraph Checkpointing

```bash
docker run -d -p 5432:5432 \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=nexus_dev \
  --name nexus_postgres \
  postgres:16-alpine
```

**Connection String:**
```
postgresql://postgres:password@localhost:5432/nexus_dev
```

### MCP Servers

Start MCP servers in separate terminals:

```bash
# Terminal 1: Filesystem server
python 08-local-agent-runtime/mcp_servers/filesystem/server.py
# Runs on http://localhost:8000

# Terminal 2: Git server
python 08-local-agent-runtime/mcp_servers/git/server.py
# Runs on http://localhost:8001
```

**Health Checks:**
```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
```

---

---

## v3.0.0 Migration Guide

### Breaking Changes

**1. MessagesState (Replaces Custom AgentState)**

v3.0.0 uses LangGraph's built-in `MessagesState` instead of custom `AgentState` TypedDict.

**Before (v2.x):**
```python
class AgentState(TypedDict):
    context: Dict[str, Any]
    history: Annotated[list[BaseMessage], operator.add]
    current_node: str
    error: Optional[str]

input_data = {
    "context": {"query": "..."},
    "history": []
}
```

**After (v3.0.0):**
```python
from langchain_core.messages import HumanMessage

input_data = {
    "messages": [
        HumanMessage(content="Content to classify: ...")
    ]
}
```

**2. Route Keys (Replaces Expression Evaluation)**

v3.0.0 uses simple route key matching instead of `simpleeval` expression evaluation.

**Before (v2.x):**
```yaml
edges:
  - from_node: router
    to_node: action_a
    condition:
      expression: "last_response.strip().lower() == 'safe'"
```

**After (v3.0.0):**
```yaml
edges:
  - from_node: router
    to_node: action_a
    condition:
      route: "safe"  # Simple substring matching
```

**How Route Matching Works:**
- Router returns LLM response (e.g., "safe", "low", "medium")
- Compiler does case-insensitive substring matching: `route_key.lower() in response.lower()`
- First match wins

**3. Synchronous Compiler API**

**Before (v2.x):**
```python
state_graph = await compiler.compile_async(manifest, graph_name)
```

**After (v3.0.0):**
```python
state_graph = compiler.compile(manifest, graph_name)  # No await
```

**4. Router Reference Parsing**

Both formats now work in YAML:

```yaml
# Nested format (standard)
- id: router_node
  kind: router
  router:
    name: "my_router"

# Flat format (also works in v2.0.5+)
- id: router_node
  kind: router
  router_ref: "my_router"
```

---

## Standard Runtime Pattern

### Recommended Pattern (v3.0.1+)

All examples should follow this pattern for consistency:

```python
import asyncio
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_core.messages import HumanMessage
from universal_agent_nexus.compiler import parse
from universal_agent_nexus.ir.pass_manager import create_default_pass_manager, OptimizationLevel
from universal_agent_nexus.adapters.langgraph import LangGraphRuntime
from universal_agent_tools.observability_helper import setup_observability, trace_runtime_execution

async def main():
    # 1. Setup observability (one line)
    obs_enabled = setup_observability("service-name")
    
    # 2. Parse manifest
    ir = parse("manifest.yaml")
    
    # 3. Run optimization passes
    manager = create_default_pass_manager(OptimizationLevel.DEFAULT)
    ir_optimized = manager.run(ir)
    
    # 4. Initialize runtime
    runtime = LangGraphRuntime(
        postgres_url=None,
        enable_checkpointing=False,
    )
    await runtime.initialize(ir_optimized, graph_name="main")
    
    # 5. Prepare input (MessagesState format)
    input_data = {
        "messages": [
            HumanMessage(content="Your input here")
        ]
    }
    
    # 6. Execute with tracing
    if obs_enabled:
        async with trace_runtime_execution("exec-001", graph_name="main"):
            result = await runtime.execute(
                execution_id="exec-001",
                input_data=input_data,
            )
    else:
        result = await runtime.execute(
            execution_id="exec-001",
            input_data=input_data,
        )
    
    # 7. Extract results
    messages = result.get("messages", [])
    if messages:
        last_message = messages[-1]
        output = getattr(last_message, "content", "")
        print(f"Result: {output}")

if __name__ == "__main__":
    asyncio.run(main())
```

**Key Points:**
- Always use full compiler pipeline: `parse()` → `PassManager` → `runtime.initialize()`
- Use `MessagesState` format for input
- Include observability setup
- Use `trace_runtime_execution` context manager

---

## Content Moderation Patterns (Example 02)

### Multi-Tier Router Pattern

**Use Case:** Classify content into multiple risk levels with different handling per level.

**Pattern:**
```yaml
graphs:
  - name: moderate_content
    entry_node: risk_assessment
    nodes:
      - id: risk_assessment
        kind: router
        router_ref: risk_router
      
      # Different handlers per risk level
      - id: auto_approve      # Safe
      - id: policy_check      # Low
      - id: human_review      # Medium
      - id: auto_reject       # High
      - id: critical_action  # Critical
    
    edges:
      - from_node: risk_assessment
        to_node: auto_approve
        condition:
          route: "safe"
      - from_node: risk_assessment
        to_node: policy_check
        condition:
          route: "low"
      # ... more routes

routers:
  - name: risk_router
    strategy: llm
    system_message: |
      Classify content risk. Respond with ONE word: safe, low, medium, high, or critical.
    default_model: "ollama://qwen3:8b"
```

**Key Learnings:**
- Router should return single word for simple matching
- Use descriptive route keys that match LLM output
- Each risk level gets dedicated handler node

### Convergent Path Pattern

**Use Case:** All execution paths converge to a single node (e.g., audit logging).

**Pattern:**
```yaml
edges:
  # All paths converge to audit_log
  - from_node: auto_approve
    to_node: audit_log
  - from_node: policy_approve
    to_node: audit_log
  - from_node: human_review
    to_node: audit_log
  - from_node: auto_reject
    to_node: audit_log
  - from_node: critical_action
    to_node: audit_log
```

**Benefits:**
- Ensures all decisions are logged
- Single point for compliance tracking
- Easy to add post-processing

### Policy Validation Pattern

**Use Case:** Validate content against policies with dual outcomes.

**Pattern:**
```yaml
nodes:
  - id: policy_check
    kind: tool
    tool_ref: policy_validator
  
  - id: policy_approve
    kind: task
    config:
      action: "approve"
  
  - id: policy_failed
    kind: task
    config:
      action: "escalate"
      queue: "policy_violation_queue"

edges:
  - from_node: policy_check
    to_node: policy_approve
    condition:
      trigger: success
      route: "compliant"
  
  - from_node: policy_check
    to_node: policy_failed
    condition:
      trigger: success
      route: "violation"
```

**Key Points:**
- Tool returns structured response
- Route based on tool output
- Separate handlers for pass/fail

### Escalation Workflow Pattern

**Use Case:** Escalate to human review with priority and SLA tracking.

**Pattern:**
```yaml
nodes:
  - id: human_review
    kind: task
    config:
      action: "escalate"
      queue: "moderation_queue"
      priority: "normal"      # normal, high, urgent
      sla_hours: 24          # Service level agreement
```

**Variations:**
- Different queues per risk level
- Priority based on severity
- SLA tracking for compliance

---

## Router Patterns

### Single Decision Router

**Pattern:** Router makes ONE decision, routes to N tools.

**Example:** See `tools/universal_agent_tools/router_patterns.py`

```python
from universal_agent_tools.router_patterns import RouteDefinition, build_decision_agent_manifest

routes = [
    RouteDefinition(
        name="financial",
        tool_ref="financial_analyzer",
        condition_expression="contains(output, 'financial')"
    ),
    RouteDefinition(
        name="technical",
        tool_ref="technical_researcher",
        condition_expression="contains(output, 'technical')"
    ),
]

manifest = build_decision_agent_manifest(
    agent_name="research-director",
    system_message="Classify query intent...",
    llm="local://qwen3",
    routes=routes,
)
```

**Note:** `condition_expression` is for v2.x. In v3.0.0, use `route` keys instead.

### Multi-Tier Router (Content Moderation)

**Pattern:** Router classifies into multiple tiers, each with different handling.

**Key Differences:**
- More than 2-3 routes (typically 5+)
- Each route has dedicated handler
- Convergent paths to audit/compliance
- Escalation workflows per tier

**See:** `02-content-moderation/manifest.yaml`

### Route Key Best Practices

1. **Use Single Words:** Router should return single word (e.g., "safe", "low")
2. **Case Insensitive:** Matching is case-insensitive
3. **Substring Match:** `route_key in response` (not exact match)
4. **Order Matters:** First match wins, order edges by priority

**Example:**
```yaml
edges:
  # Order by priority (most specific first)
  - from_node: router
    to_node: critical_handler
    condition:
      route: "critical"  # Most specific
  
  - from_node: router
    to_node: high_handler
    condition:
      route: "high"
  
  - from_node: router
    to_node: default_handler
    condition:
      route: "safe"  # Fallback
```

---

## Reusable Helpers

### Existing Helpers

**1. Observability Helper** (`universal_agent_tools/observability_helper.py`)
- `setup_observability()` - One-line OpenTelemetry setup
- `trace_runtime_execution()` - Context manager for tracing

**2. Router Patterns** (`tools/universal_agent_tools/router_patterns.py`)
- `RouteDefinition` - Route configuration dataclass
- `build_decision_agent_manifest()` - Single-decision router builder

**3. Ollama Tools** (`universal_agent_tools/ollama_tools.py`)
- `create_llm_with_tools()` - Ollama LLM with tool binding
- `MCPToolLoader` - Load tools from MCP servers
- `parse_tool_calls_from_content()` - Manual tool call parsing

**4. Model Config** (`universal_agent_tools/model_config.py`)
- `ModelConfig.resolve_model()` - Standardized model resolution
- Environment variable support (`UAA_MODEL`)
- Model name mapping (backwards compatibility)

### Patterns to Extract (Future)

**1. Convergent Audit Pattern**
```python
def add_audit_convergence(graph: GraphIR, audit_node_id: str) -> GraphIR:
    """Add edges from all terminal nodes to audit node."""
    # Implementation
```

**2. Escalation Workflow Builder**
```python
def create_escalation_node(
    node_id: str,
    queue: str,
    priority: str = "normal",
    sla_hours: int = 24
) -> NodeIR:
    """Create escalation task node with SLA tracking."""
    # Implementation
```

**3. Multi-Tier Router Builder**
```python
def build_multi_tier_router(
    tiers: List[RiskTier],
    router_config: RouterConfig
) -> ManifestIR:
    """Build content moderation-style multi-tier router."""
    # Implementation
```

---

## Common Gotchas

### 1. Router Reference Parsing

**Issue:** `router_ref` not being parsed correctly.

**Solution:** Use nested format or ensure v2.0.5+:
```yaml
# Preferred (works in all versions)
router:
  name: "my_router"

# Also works (v2.0.5+)
router_ref: "my_router"
```

### 2. MessagesState Input Format

**Issue:** Runtime expects `MessagesState` but code provides custom dict.

**Solution:** Always use messages format:
```python
from langchain_core.messages import HumanMessage
input_data = {"messages": [HumanMessage(content="...")]}
```

### 3. Route Key Matching

**Issue:** Route not matching because LLM returns full sentence.

**Solution:** Router system message should request single word:
```yaml
system_message: |
  Respond with ONE word only: safe, low, medium, high, or critical.
  No explanations, no JSON, just the word.
```

### 4. Compiler Pipeline

**Issue:** Bypassing compiler pipeline leads to missing optimizations.

**Solution:** Always use full pipeline:
```python
ir = parse("manifest.yaml")
manager = create_default_pass_manager(OptimizationLevel.DEFAULT)
ir_optimized = manager.run(ir)
await runtime.initialize(ir_optimized, graph_name="main")
```

---

## ETL Pipeline Patterns (Example 03)

### Router-Based Data Enrichment

**Use Case:** Use LLM router to enrich data records with structured output.

**Pattern:**
```yaml
nodes:
  - id: enrich
    kind: router
    router_ref: enrichment_router

routers:
  - name: enrichment_router
    strategy: llm
    system_message: |
      You are a data enrichment AI. Analyze the input record and extract structured information.
      
      Return ONLY valid JSON with these fields:
      {
        "sentiment": "positive|negative|neutral",
        "entities": ["entity1", "entity2"],
        "category": "support|feedback|inquiry|other",
        "confidence": 0.95
      }
      
      No explanations, no markdown, just the JSON object.
    default_model: "ollama://qwen3:8b"
```

**Key Points:**
- Router returns structured JSON (not single words)
- System message must explicitly request JSON format
- Use `router_ref` to reference router configuration
- LLM response becomes the enriched data

### Sequential Pipeline Flow

**Use Case:** Linear ETL pipeline: Extract → Transform → Validate → Load.

**Pattern:**
```yaml
edges:
  - from_node: extract
    to_node: enrich
  
  - from_node: enrich
    to_node: validate
  
  - from_node: validate
    to_node: load
  
  - from_node: load
    to_node: pipeline_complete
```

**Benefits:**
- Simple linear flow
- Easy to understand and debug
- Natural ETL pattern

### JSON Parsing from LLM Responses

**Challenge:** LLM returns JSON with newlines, need to parse reliably.

**Solution:**
```python
import json
import re

def parse_json_from_message(content: str) -> dict:
    """Extract and parse JSON from LLM message."""
    if "{" in content:
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        if json_end > json_start:
            json_str = content[json_start:json_end]
            # Clean up: remove newlines, normalize whitespace
            json_str = re.sub(r'\n\s*', ' ', json_str)
            json_str = re.sub(r'\s+', ' ', json_str)
            return json.loads(json_str)
    return None
```

**Key Points:**
- Extract JSON substring (between `{` and `}`)
- Normalize whitespace (remove newlines)
- Handle both pretty-printed and compact JSON

### Simplified Validation

**Pattern:** Use task node for validation instead of external tool.

**Before (Complex):**
```yaml
- id: validate
  kind: tool
  tool_ref: schema_validator  # Requires external service
```

**After (Simple):**
```yaml
- id: validate
  kind: task
  config:
    action: "validate_json"
    required_fields: ["sentiment", "entities", "category"]
```

**Benefits:**
- No external dependencies
- Faster execution
- Easier to test
- Can be enhanced later with real validation logic

---

## Support Chatbot Patterns (Example 04)

### Multi-Router Pattern

**Use Case:** Multiple routers in one graph for different purposes (intent classification, sentiment analysis, response generation).

**Pattern:**
```yaml
nodes:
  - id: classify_intent
    kind: router
    router_ref: intent_classifier  # Routes to handlers
  
  - id: sentiment_check
    kind: router
    router_ref: sentiment_router  # Routes: escalate or handle
  
  - id: generate_response
    kind: router
    router_ref: response_generator  # Generates final response

routers:
  - name: intent_classifier
    system_message: "Classify intent: faq, technical, billing, complaint, or other"
    default_model: "ollama://qwen3:8b"
  
  - name: sentiment_router
    system_message: "Analyze sentiment: respond with 'escalate' or 'handle'"
    default_model: "ollama://qwen3:8b"
  
  - name: response_generator
    system_message: "Generate helpful customer support response"
    default_model: "ollama://qwen3:8b"
```

**Key Points:**
- Each router has a specific purpose
- Routers can route to handlers OR generate content
- Use descriptive router names
- Each router needs its own system message

### Router for Content Generation

**Use Case:** Use router node to generate actual content (not just routing decisions).

**Pattern:**
```yaml
- id: generate_response
  kind: router
  router_ref: response_generator

routers:
  - name: response_generator
    strategy: llm
    system_message: |
      You are a helpful customer support assistant.
      Generate a helpful, empathetic response.
    default_model: "ollama://qwen3:8b"
```

**Key Points:**
- Router returns full response text (not just a word)
- System message guides the response style
- Response becomes the final output
- No routing needed after content generation

### Convergent Response Pattern

**Use Case:** Multiple paths converge to a single response generator.

**Pattern:**
```yaml
edges:
  - from_node: search_knowledge
    to_node: generate_response
  - from_node: troubleshoot
    to_node: generate_response
  - from_node: handle_billing
    to_node: generate_response
  - from_node: sentiment_check
    to_node: generate_response
    condition:
      route: "handle"
```

**Benefits:**
- Single point for response formatting
- Consistent response style
- Easy to add post-processing
- All paths get proper responses

### Intent Classification Flow

**Pattern:** Classify → Route → Handle → Respond

```yaml
edges:
  - from_node: classify_intent
    to_node: search_knowledge
    condition:
      route: "faq"
  
  - from_node: classify_intent
    to_node: troubleshoot
    condition:
      route: "technical"
  
  - from_node: classify_intent
    to_node: account_lookup
    condition:
      route: "billing"
```

**Key Points:**
- Router returns single word for routing
- Each intent gets dedicated handler
- Handlers can be tools or tasks
- All paths eventually converge

---

## Research Assistant Patterns (Example 05)

### Parallel Processing with Convergence

**Use Case:** Run multiple analysis tasks in parallel, then converge to synthesis.

**Pattern:**
```yaml
edges:
  - from_node: chunk_content
    to_node: extract_key_points
  
  - from_node: chunk_content
    to_node: extract_entities  # Parallel with extract_key_points
  
  - from_node: extract_key_points
    to_node: identify_themes
  
  - from_node: identify_themes
    to_node: generate_summary
  
  - from_node: extract_entities
    to_node: generate_summary  # Converges to summary
```

**Key Points:**
- Multiple edges from same source = parallel execution
- Convergent paths ensure all results are used
- Final node receives context from all parallel branches

### Specialized Router Pattern

**Use Case:** Each analysis task uses a specialized router with task-specific system message.

**Pattern:**
```yaml
nodes:
  - id: extract_key_points
    kind: router
    router_ref: key_points_router
  
  - id: extract_entities
    kind: router
    router_ref: entity_router
  
  - id: identify_themes
    kind: router
    router_ref: theme_router

routers:
  - name: key_points_router
    system_message: "Extract key points with claims, evidence, confidence..."
  
  - name: entity_router
    system_message: "Extract entities: people, organizations, locations..."
  
  - name: theme_router
    system_message: "Identify themes with names, evidence, relevance scores..."
```

**Benefits:**
- Each router optimized for its specific task
- Clear separation of concerns
- Easy to tune individual routers
- Reusable router definitions

### Multi-Graph Pattern

**Use Case:** Separate graphs for different workflows (single doc analysis vs multi-doc synthesis).

**Pattern:**
```yaml
graphs:
  - name: analyze_document
    entry_node: parse_document
    # ... single document analysis
  
  - name: synthesize_documents
    entry_node: collect_summaries
    # ... multi-document synthesis
```

**Usage:**
```python
# Analyze single document
await runtime.initialize(ir_optimized, graph_name="analyze_document")

# Synthesize multiple documents
await runtime.initialize(ir_optimized, graph_name="synthesize_documents")
```

**Benefits:**
- Clear workflow separation
- Can reuse nodes across graphs
- Easy to extend with new workflows

### Structured Output Pattern

**Use Case:** Routers generate structured JSON or formatted text for downstream processing.

**Pattern:**
```yaml
routers:
  - name: key_points_router
    system_message: |
      Extract key points and return as JSON array:
      [
        {
          "claim": "...",
          "evidence": "...",
          "confidence": "high",
          "page": 1
        }
      ]
```

**Key Points:**
- System message explicitly requests JSON format
- Structured output enables downstream processing
- Can parse JSON from router responses
- Use JSON parsing helper for reliability

---

## N-Decision Router Pattern (Example 11)

### N-Way Routing Pattern

**Use Case:** Single router that classifies input into N categories, each leading to a different tool/action.

**Pattern:**
```yaml
nodes:
  - id: analyze_query
    kind: router
    router_ref: decision_router
  
  - id: data_quality_exec
    kind: tool
    tool_ref: data_quality_tool
  
  - id: growth_experiment_exec
    kind: tool
    tool_ref: growth_experiment_tool
  
  # ... more tool nodes ...

edges:
  - from_node: analyze_query
    to_node: data_quality_exec
    condition:
      route: "data_quality"
  
  - from_node: analyze_query
    to_node: growth_experiment_exec
    condition:
      route: "growth_experiment"
  
  # ... more routes ...

routers:
  - name: decision_router
    system_message: |
      Classify the user's request into one of:
      - data_quality
      - growth_experiment
      - customer_support
      - reporting
      
      Respond with ONLY the category name.
```

**Key Points:**
- Single router makes one decision per invocation
- N edges from router (one per category)
- Each edge uses `route:` condition with category name
- Router returns single word for simple matching
- All paths can converge to a common formatter

### Convergent Formatter Pattern

**Use Case:** Multiple execution paths converge to a single formatter/router for consistent output.

**Pattern:**
```yaml
edges:
  - from_node: data_quality_exec
    to_node: format_response
  
  - from_node: growth_experiment_exec
    to_node: format_response
  
  - from_node: customer_support_exec
    to_node: format_response
  
  - from_node: reporting_exec
    to_node: format_response

nodes:
  - id: format_response
    kind: router
    router_ref: formatter_router

routers:
  - name: formatter_router
    system_message: |
      Summarize the tool output clearly for the user.
      Make it concise, actionable, and easy to understand.
```

**Benefits:**
- Consistent output format across all routes
- Single place to modify formatting logic
- Easy to add new routes without changing formatter
- Can include route-specific context in formatting

### Router for Formatting

**Use Case:** Use a router (not just a task) for LLM-powered formatting/transformation.

**Pattern:**
```yaml
nodes:
  - id: format_response
    kind: router  # Router, not task!
    router_ref: formatter_router

routers:
  - name: formatter_router
    strategy: llm
    system_message: |
      Transform the tool output into a user-friendly format.
      - Extract key information
      - Structure it clearly
      - Make it actionable
```

**Why Router Instead of Task?**
- Router uses LLM for intelligent formatting
- Can adapt format based on content
- Better than simple string templates
- Consistent with v3.0.0 patterns

### Extending N-Decision Router

**Adding New Routes:**
1. Add new tool node
2. Add new edge from router with `route:` condition
3. Add edge from tool to formatter
4. Update router system message to include new category

**Example:**
```yaml
# Add new tool
- id: analytics_exec
  kind: tool
  tool_ref: analytics_tool

# Add new route
- from_node: analyze_query
  to_node: analytics_exec
  condition:
    route: "analytics"

# Converge to formatter
- from_node: analytics_exec
  to_node: format_response
```

**No code changes needed** - just manifest updates!

---

**Last Updated:** December 7, 2025 - v3.0.1 patterns: content moderation, ETL pipeline, support chatbot, research assistant, and N-decision router learnings

