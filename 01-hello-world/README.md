# Hello World - Zero to Production in 10 Minutes

**Your first Universal Agent Nexus workflow.**

## What You'll Build

A simple greeting agent that:
1. Takes a name as input
2. Generates a personalized greeting
3. Returns the result

**Time to complete:** 10 minutes

---

## Prerequisites

```bash
# Install Universal Agent Nexus
pip install universal-agent-nexus

# Verify installation
nexus --version
```

---

## Step 1: Define Your Agent (2 min)

The `manifest.yaml` in this directory defines a simple agent:

```yaml
name: hello-world
version: "1.0.0"
description: "A simple greeting agent"

graphs:
  - name: main
    entry_node: greet
    nodes:
      - id: greet
        kind: task
        label: "Generate Greeting"
        config:
          prompt: "Generate a friendly greeting for {name}"
    edges: []

tools: []
routers: []
```

**What this means:**
- One graph called `main`
- One task node called `greet`
- No edges (single-step workflow)
- No tools or routers (basic example)

---

## Step 2: Test Locally with LangGraph (3 min)

```bash
# Compile to LangGraph
nexus compile manifest.yaml --target langgraph --output agent.py

# The generated agent.py contains a runnable LangGraph StateGraph
python agent.py
```

**Expected output:**
```
✅ LangGraph runtime initialized
Executing graph: main
Input: {"name": "World"}
Result: {"greeting": "Hello, World! Welcome to Universal Agent Nexus!"}
```

---

## Step 3: Deploy to AWS (5 min)

```bash
# Compile to AWS Step Functions
nexus compile manifest.yaml --target aws --output state_machine.json

# The state_machine.json contains AWS ASL (Amazon States Language)
cat state_machine.json
```

**Deploy with AWS CLI:**
```bash
# Create execution role (first time only)
aws iam create-role \
  --role-name HelloWorldStepFunctionsRole \
  --assume-role-policy-document file://trust-policy.json

# Create state machine
aws stepfunctions create-state-machine \
  --name hello-world \
  --definition file://state_machine.json \
  --role-arn arn:aws:iam::YOUR_ACCOUNT_ID:role/HelloWorldStepFunctionsRole

# Execute
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:us-east-1:YOUR_ACCOUNT_ID:stateMachine:hello-world \
  --input '{"name": "AWS"}'
```

---

## Step 4: Expose as MCP Server (Optional)

```bash
# Start MCP server (for Claude Desktop, Cursor, etc.)
nexus serve manifest.yaml --protocol mcp --transport stdio
```

**Configure in Claude Desktop:**
```json
{
  "mcpServers": {
    "hello-world": {
      "command": "nexus",
      "args": ["serve", "/path/to/manifest.yaml", "--protocol", "mcp"]
    }
  }
}
```

---

## What You Learned

✅ How to define an agent with UAA YAML  
✅ How to compile to LangGraph (local dev)  
✅ How to compile to AWS (production)  
✅ How to expose as MCP server (AI clients)  

**One manifest. Three runtimes. Zero rewrites.**

---

## Next Steps

- [Content Moderation Example](../02-content-moderation/) - Multi-stage pipeline
- [Data Pipeline Example](../03-data-pipeline/) - ETL with LLM enrichment
- [Migration Guide](../migration-guides/langgraph-to-uaa.md) - Convert existing agents

---

## Troubleshooting

**Q: `nexus: command not found`**  
A: Install with `pip install universal-agent-nexus`

**Q: AWS deployment fails**  
A: Check IAM role permissions (Step Functions execution role)

**Q: LangGraph execution fails**  
A: Ensure Postgres is running (if checkpointing enabled)

---

**Questions?** [Open an issue](https://github.com/mjdevaccount/universal_agent_nexus/issues)

