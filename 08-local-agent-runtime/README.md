# 🤖 Local Agent Runtime - MCP Tools + LangGraph + Ollama

**Fully local agent with MCP tool integration. Demonstrates the December 2025 stack.**

## 🎯 What This Demonstrates

This example shows how **Universal Agent Nexus** compiles Fabric YAML to a LangGraph runtime with MCP tool integration:

```
Fabric YAML (defines tools)
    ↓
Nexus Compiler (bridges to LangGraph)
    ↓
LangGraph Runtime (orchestrates execution)
    ↓
MCP Servers (provide tools)
    ↓
Ollama LLM (function calling)
```

---

## 🚀 Quick Start (5 Minutes)

### 1. Install Dependencies

```bash
cd 08-local-agent-runtime
pip install -r backend/requirements.txt
```

### 2. Start MCP Servers

**Terminal 1: Filesystem Server**
```bash
python mcp_servers/filesystem/server.py
# Runs on http://localhost:8000
```

**Terminal 2: Git Server**
```bash
python mcp_servers/git/server.py
# Runs on http://localhost:8001
```

### 3. Pull Ollama Model

```bash
ollama pull llama3.2:11b
# Or use: gemma:2b-instruct, qwen2.5:7b
```

### 4. Run Agent

```bash
# Option 1: Direct runtime
python runtime/agent_runtime.py

# Option 2: Compile from Fabric YAML (demonstrates compiler)
python backend/compiler_bridge.py
```

---

## 🏗️ Architecture

### December 2025 Stack

```
┌─────────────────────────────────────────┐
│ LOCAL LLM (Ollama)                      │
│ • llama3.2:11b (function calling)      │
│ • Native tool support                   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ LangGraph Agent Runtime                  │
│ • State management                       │
│ • Tool routing                           │
│ • Multi-step execution                   │
│ • Checkpoints/resumability              │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ MCP Client (Python-MCP)                  │
│ • Tool schema introspection             │
│ • Auto-discovery                         │
│ • Transport (HTTP/SSE/stdio)            │
└──────────────┬──────────────────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
┌──────────────┐ ┌──────────────┐
│ MCP Server   │ │ MCP Server   │
│ Filesystem   │ │ Git          │
│ • read_file  │ │ • git_status │
│ • write_file │ │ • git_commit │
│ • list_dir   │ │ • git_diff   │
└──────────────┘ └──────────────┘
```

---

## 📋 MCP Tools Available

### Filesystem Server (`localhost:8000`)

| Tool | Description |
|------|-------------|
| `read_file` | Read file contents |
| `write_file` | Write content to file |
| `list_directory` | List files in directory |
| `search_code` | Search for code patterns |

### Git Server (`localhost:8001`)

| Tool | Description |
|------|-------------|
| `git_status` | Get repository status |
| `git_commit` | Create commit |
| `git_diff` | Show changes |

---

## 🔧 Compiler Integration

### Fabric YAML → LangGraph

The `compiler_bridge.py` demonstrates how **Universal Agent Nexus** would compile:

**Input:** `local_agent.yaml`
```yaml
tools:
  - name: "read_file"
    protocol: "mcp"
    mcp_server: "filesystem"
    config:
      server_url: "http://localhost:8000/mcp"
```

**Output:** `runtime/generated_agent.py`
```python
from runtime.agent_runtime import MCPToolLoader, create_agent_graph

tools = MCPToolLoader.load_from_server("http://localhost:8000/mcp")
agent = create_agent_graph(tools, llm)
```

---

## 🎬 Example Usage

### Example 1: Read a File

```python
from runtime.agent_runtime import create_agent_graph, MCPToolLoader

# Load tools
tools = MCPToolLoader.load_from_server("http://localhost:8000/mcp")

# Create agent
agent = create_agent_graph(tools, llm)

# Run
result = agent.invoke({
    "messages": [
        HumanMessage(content="Read the contents of main.py")
    ]
})
```

### Example 2: Search Code

```python
result = agent.invoke({
    "messages": [
        HumanMessage(content="Find all TODO comments in the codebase")
    ]
})
```

### Example 3: Git Operations

```python
result = agent.invoke({
    "messages": [
        HumanMessage(content="Check git status and show me the diff")
    ]
})
```

---

## 🔒 Security & Governance

The Fabric YAML includes governance rules:

```yaml
governance:
  - name: "file_safety"
    target_pattern: ".*write_file.*"
    action: "require_approval"
    conditions:
      path_matches: ".*\\.(exe|sh|bat|ps1)$"
```

These would be enforced by the **Universal Agent Architecture** runtime's `PolicyEngine`.

---

## 📊 MCP Spec Compliance (November 2025)

This example implements:

- ✅ **SEP-986**: Standardized tool naming
- ✅ **SEP-835**: Default scopes in authorization
- ✅ **SEP-1319**: Decoupled request payload
- ✅ **SEP-1699**: SSE polling support
- ✅ **Tool introspection**: Auto-discovery via `/tools` endpoint
- ✅ **Standardized schemas**: JSON Schema format

---

## 🧪 Testing

```bash
# Test MCP servers
curl http://localhost:8000/mcp/tools
curl http://localhost:8001/mcp/tools

# Test tool execution
curl -X POST http://localhost:8000/mcp/tools/read_file \
  -H "Content-Type: application/json" \
  -d '{"path": "README.md"}'
```

---

## 🚧 What's Next

This example demonstrates the **compiler architecture** for tool integration:

1. ✅ Fabric YAML defines tools
2. ✅ MCP servers provide tools
3. ✅ Compiler bridges Fabric → LangGraph
4. ✅ LangGraph orchestrates execution
5. ⏳ **Next**: Full compiler integration in Universal Agent Nexus

---

## 📄 License

MIT License - Part of [Universal Agent Examples](https://github.com/mjdevaccount/universal_agent_nexus_examples)

