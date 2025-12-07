# Available Tools - Running MCP Servers

## Currently Running Servers

### 1. Filesystem Server (`http://localhost:8000`)

**Status:** ✅ Running  
**Location:** `08-local-agent-runtime/mcp_servers/filesystem/server.py`

**Available Tools:**
- `read_file` - Read contents of a file
- `write_file` - Write content to a file
- `list_directory` - List files in a directory
- `search_code` - Search for code patterns (regex)

**Health Check:**
```bash
curl http://localhost:8000/health
# Returns: {"status":"ok","server":"filesystem","tools":4}
```

**Introspection:**
```bash
curl http://localhost:8000/mcp/tools
# Returns: {"tools": [...]}
```

### 2. Git Server (`http://localhost:8001`)

**Status:** ✅ Running  
**Location:** `08-local-agent-runtime/mcp_servers/git/server.py`

**Available Tools:**
- `git_status` - Get Git repository status
- `git_commit` - Create a Git commit
- `git_diff` - Get Git diff of changes

**Health Check:**
```bash
curl http://localhost:8001/health
# Returns: {"status":"ok","server":"git","tools":3}
```

**Introspection:**
```bash
curl http://localhost:8001/mcp/tools
# Returns: {"tools": [...]}
```

## Using These Tools

### Via Tool Registry

```python
from tools.registry.tool_registry import get_registry

registry = get_registry()

# Register servers
registry.register_server("filesystem", "http://localhost:8000/mcp")
registry.register_server("git", "http://localhost:8001/mcp")

# Discover all tools
tools = registry.discover_tools()
# Returns: 7 tools total
```

### Direct MCP Tool Loader

```python
from 08-local-agent-runtime.runtime.agent_runtime import MCPToolLoader

# Load filesystem tools
fs_tools = MCPToolLoader.load_from_server("http://localhost:8000/mcp")
# Returns: 4 tools

# Load git tools
git_tools = MCPToolLoader.load_from_server("http://localhost:8001/mcp")
# Returns: 3 tools
```

## Tool Execution Examples

### Read a File
```python
import httpx

response = httpx.post(
    "http://localhost:8000/mcp/tools/read_file",
    json={"path": "README.md"}
)
print(response.json()["content"])
```

### List Directory
```python
response = httpx.post(
    "http://localhost:8000/mcp/tools/list_directory",
    json={"path": "."}
)
print(response.json()["content"])
```

### Git Status
```python
response = httpx.post(
    "http://localhost:8001/mcp/tools/git_status",
    json={"repo_path": "."}
)
print(response.json()["content"])
```

### Search Code
```python
response = httpx.post(
    "http://localhost:8000/mcp/tools/search_code",
    json={"pattern": "def main", "directory": "."}
)
print(response.json()["content"])
```

## Integration with AutonomousFlow

These tools are automatically discovered by Example 09:

```bash
cd 09-autonomous-flow
python backend/main.py
# Discovers all 7 tools and regenerates manifest
```

## Adding More Tools

To add more tools, you can:

1. **Extend existing servers** - Add more endpoints to filesystem or git servers
2. **Create new MCP servers** - Follow the pattern in `08-local-agent-runtime/mcp_servers/`
3. **Register in registry** - Add to `tools/registry/tool_registry.py`

## Server Implementation Pattern

All MCP servers follow this pattern:

```python
from fastapi import FastAPI

app = FastAPI()

TOOLS = [
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

@app.get("/mcp/tools")
async def list_tools():
    return {"tools": TOOLS}

@app.post("/mcp/tools/{tool_name}")
async def execute_tool(tool_name: str, request: ToolRequest):
    # Implementation
    return {"content": "result"}

@app.get("/health")
async def health():
    return {"status": "ok", "server": "name", "tools": len(TOOLS)}
```


