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

**Last Updated:** Example 09 implementation - Discovery and regeneration working

