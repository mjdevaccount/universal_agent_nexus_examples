# 🤖 AutonomousFlow - Dynamic Workflow Discovery

**Autonomous agent that discovers tools and regenerates workflows on the fly through process of discovery.**

## 🎯 Concept

AutonomousFlow demonstrates how Universal Agent Nexus can:
- Discover available tools dynamically
- Receive high-level instructions
- Figure out the workflow itself
- Execute using discovered capabilities
- Adapt to new tools without manual recompilation

## 🏗️ Architecture

```
Instructions → Agent → Tool Discovery → Dynamic Workflow → Execution
     ↓            ↓           ↓              ↓                ↓
User Task    LLM Router   MCP Servers   Tool Selection   LangGraph Runtime
```

## 🚀 Quick Start

### 1. Start MCP Servers

```bash
# Terminal 1: Filesystem server
python 08-local-agent-runtime/mcp_servers/filesystem/server.py

# Terminal 2: Git server  
python 08-local-agent-runtime/mcp_servers/git/server.py

# Terminal 3: Qdrant server
python tools/mcp_servers/qdrant/server.py

# Terminal 4: GitHub server (optional, needs GITHUB_TOKEN)
python tools/mcp_servers/github/server.py
```

### 2. Pull Ollama Model

```bash
ollama pull llama3.2:11b
```

### 3. Run AutonomousFlow

```bash
cd 09-autonomous-flow
python runtime/autonomous_runtime.py
```

## 📋 How It Works

1. **Discovery Phase**: Registry discovers available tools from MCP servers
2. **Regeneration Phase**: Manifest is regenerated with discovered tools
3. **Instruction Phase**: Agent receives high-level task instructions
4. **Planning Phase**: Agent figures out workflow using available tools
5. **Execution Phase**: Agent executes using discovered tools autonomously

## 🎯 Example Task

The agent can receive instructions like:

"Find all GitHub repos with 'universal_agent' in the name, chunk their Python files using AST parsing, store in Qdrant with structured naming, and write a summary of how they connect."

The agent will:
- Use github_search_repos to find repos
- Use github_list_files to discover Python files
- Use chunk_and_store_python to process files
- Use its LLM to generate summaries
- All autonomously, figuring out the workflow itself

## 🔧 Configuration

Edit `autonomous_flow.yaml` to configure:
- Which MCP servers to discover
- LLM model selection
- Agent system prompts

## 📝 Notes

This is an **autonomous agent** - it receives instructions and figures out how to accomplish them using available tools. It's not scripted - it's truly autonomous.
