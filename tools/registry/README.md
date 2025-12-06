# Tool Registry

Formal tool discovery and management system for Universal Agent Nexus examples.

## Purpose

This registry provides a centralized way to:
- Discover tools from MCP servers
- Manage tool definitions across examples
- Enable dynamic workflow generation based on available tools

## Usage

```python
from tools.registry.tool_registry import get_registry

registry = get_registry()

# Register MCP servers
registry.register_server("filesystem", "http://localhost:8000/mcp")
registry.register_server("git", "http://localhost:8001/mcp")

# Discover tools
tools = registry.discover_tools()

# List available tools
for tool in registry.list_tools():
    print(f"{tool.name}: {tool.description}")
```

## Integration with Compiler

The registry can be used by the Nexus compiler to:
1. Discover available tools at compile time
2. Generate workflows dynamically based on discovered tools
3. Update workflows when new tools become available

