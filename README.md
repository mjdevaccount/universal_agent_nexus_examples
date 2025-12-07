<div align="center">

# **Universal Agent Examples**

### *Real-world examples for [Universal Agent Nexus](https://github.com/mjdevaccount/universal_agent_nexus)*

**Learn by doing: content moderation, data pipelines, chatbots, research assistants, interactive playground, and migration guides.**

[![Examples](https://img.shields.io/badge/examples-13-blue.svg)](.)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 🎯 **Quick Start**

```bash
# Install Universal Agent Nexus
pip install universal-agent-nexus

# Clone examples
git clone https://github.com/mjdevaccount/universal_agent_nexus_examples.git
cd universal_agent_nexus_examples

# Run an example
cd 01-hello-world
nexus compile manifest.yaml --target langgraph --output agent.py
python agent.py
```

---

## 📚 **Examples**

### **1. Hello World** ([01-hello-world/](01-hello-world/))
**Zero to Production in 10 Minutes**

Your first agent: a simple greeting workflow.

- ✅ Basic graph structure
- ✅ Compile to LangGraph
- ✅ Deploy to AWS
- ✅ Test locally

**Perfect for:** First-time users, quick start

---

### **2. Content Moderation Pipeline** ([02-content-moderation/](02-content-moderation/))
**Production-Grade Content Moderation**

Multi-stage content moderation with AI risk assessment, policy checks, and human escalation.

- ✅ Router-based risk classification
- ✅ Policy validation tools
- ✅ Human review escalation
- ✅ Error handling & retries

**Perfect for:** Social platforms, UGC systems, compliance

---

### **3. Data Pipeline** ([03-data-pipeline/](03-data-pipeline/))
**ETL with LLM Enrichment**

Extract, transform, and load data with AI-powered enrichment.

- ✅ Data extraction from APIs
- ✅ LLM-based transformation
- ✅ Schema validation
- ✅ Batch processing

**Perfect for:** Data engineering, ETL workflows, ML pipelines

---

### **4. Support Chatbot** ([04-support-chatbot/](04-support-chatbot/))
**Multi-Step Customer Support**

Intelligent routing, knowledge base search, and escalation logic.

- ✅ Intent classification
- ✅ Knowledge base retrieval
- ✅ Multi-turn conversation
- ✅ Human agent handoff

**Perfect for:** Customer support, help desks, chatbots

---

### **5. Research Assistant** ([05-research-assistant/](05-research-assistant/))
**Document Analysis & Summarization**

Analyze documents, extract insights, and generate summaries.

- ✅ Document parsing
- ✅ Key point extraction
- ✅ Multi-document synthesis
- ✅ Citation tracking

**Perfect for:** Research, document processing, knowledge management

---

### **6. Interactive Agent Playground** ([06-playground-simulation/](06-playground-simulation/)) 🎮
**Watch Agents Interact in Real-Time**

Build agents with different personalities (bully, shy kid, mediator, joker, teacher) and watch them have conversations.

- ✅ 5 pre-built archetypes with personality traits
- ✅ Real-time conversation simulation
- ✅ Custom scenario support
- ✅ Visual personality bars
- ✅ WebSocket streaming

**Perfect for:** Learning multi-agent systems, LLM prompt engineering, educational demos

**Try it:**
```bash
cd 06-playground-simulation
ollama pull gemma:2b-instruct
uvicorn backend/main:app --port 8888
# Open frontend/index.html
```

---

### **7. Innovation Waves** ([07-innovation-waves/](07-innovation-waves/)) 🚀
**Technology Adoption Simulator - One YAML → 5 Runtimes**

Watch 300-1000 companies compete as technology adoption cascades through business networks.

- ✅ 1000 agents at 60fps (Gemma 2B)
- ✅ God Mode: Drop patents, apply regulations
- ✅ Rich-get-richer market dynamics
- ✅ Fabric policy enforcement (anti-monopoly)
- ✅ 5-runtime demo matrix (Browser, AWS, LangGraph, MCP, Ollama)

**Perfect for:** Enterprise demos, multi-runtime showcases, policy enforcement demos

**Try it:**
```bash
cd 07-innovation-waves
ollama pull gemma:2b-instruct
pip install -r backend/requirements.txt
python backend/main.py
# Open frontend/index.html (single view)
# Open frontend/demo-matrix.html (5-runtime matrix)
```

---

### **8. Local Agent Runtime** ([08-local-agent-runtime/](08-local-agent-runtime/)) 🤖
**MCP Tools + LangGraph + Ollama - December 2025 Stack**

Fully local agent with MCP tool integration. Demonstrates compiler architecture for tool calling.

- ✅ MCP servers (filesystem, git) with auto-discovery
- ✅ LangGraph orchestration with tool routing
- ✅ Ollama with native function calling
- ✅ Compiler bridge: Fabric YAML → LangGraph runtime
- ✅ Tool introspection (MCP November 2025 spec)

**Perfect for:** Understanding tool integration, compiler architecture, local agent development

**Try it:**
```bash
cd 08-local-agent-runtime
ollama pull llama3.2:11b
pip install -r backend/requirements.txt
# Start MCP servers
python mcp_servers/filesystem/server.py &
python mcp_servers/git/server.py &
# Run agent
python runtime/agent_runtime.py
```

---

### **9. Autonomous Flow** ([09-autonomous-flow/](09-autonomous-flow/)) 🛰️
**Dynamic Tool Discovery + Regenerated Manifests**

Autonomous agent that discovers MCP tools at runtime, regenerates its manifest, and executes workflows without manual wiring.

- ✅ Tool discovery and registry
- ✅ LangGraph runtime with regenerated manifests
- ✅ Ollama (llama3.2) for routing and planning
- ✅ Qdrant, filesystem, Git, and GitHub MCP integrations

**Perfect for:** Self-directed automation that adapts to new tools.

**Try it:**
```bash
cd 09-autonomous-flow
python runtime/autonomous_runtime.py
```

---

### **10. Local LLM + Tool Server Patterns** ([10-local-llm-tool-servers/](10-local-llm-tool-servers/)) 🧠
**Single-Decision Routers, Nested Scaffolding, Tenant Isolation, and Dynamic Tools**

Architecture patterns for running Qwen2.5-sized LLMs locally with MCP tool servers. Includes a production-style research agent with embeddings and Postgres-free LangGraph runtime.

- ✅ Pattern A: Single-decision router manifest
- ✅ Pattern B: CompilerBuilder nested scaffolding
- ✅ Pattern C: Tenant-aware enrichment handlers
- ✅ Pattern D: Dynamic CSV tool generation via IR visitor
- ✅ Research agent stack (Ollama + SQLite + sentence-transformers)
- ✅ Reusable toolkit extracted to `tools/universal_agent_tools`

**Perfect for:** Building cost-efficient, locally executed multi-agent systems with strict tool routing.

**Try it:**
```bash
cd 10-local-llm-tool-servers/research_agent
ollama pull qwen2.5:32b
pip install -r ../requirements.txt
python run_local.py
```

---

### **11. N-Decision Router (Reusable Routing Helpers)** ([11-n-decision-router/](11-n-decision-router/)) 🛣️
**Declarative router wiring with N decision paths plus dynamic tool injection**

Generalize the single-decision pattern into an N-decision agent, built from reusable route definitions. Demonstrates how router wiring, tool edges, and dynamic tool injection can live in the shared `tools/universal_agent_tools` library.

- ✅ RouteDefinition-driven manifest builder (no manual YAML wiring)
- ✅ Plug-and-play MCP tool definitions per route
- ✅ Dynamic CSV tool injection layered onto the same router
- ✅ Minimal dependencies (YAML generation + Nexus IR)

**Perfect for:** Teams that want to grow from 1 → N router decisions without rewriting manifests.

**Try it:**
```bash
cd 11-n-decision-router
pip install -r requirements.txt
python generate_manifest.py
nexus compile manifest.yaml --target langgraph --output agent.py
```

---

### **12. Self-Modifying Agent (Runtime Tool Generation)** ([12-self-modifying-agent/](12-self-modifying-agent/)) 🔁
**Evolve manifests from failure logs with reusable helpers**

Generate a repair tool from repeated failures, wire it into the router, and recompile—all powered by the shared `SelfModifyingAgent` abstraction.

- ✅ Execution-log driven tool synthesis
- ✅ Deterministic tool definitions (promotion-safe)
- ✅ Router wiring that preserves single-decision semantics while adding new branches
- ✅ End-to-end regeneration of an evolved agent file

**Perfect for:** Systems that must heal themselves when new failure patterns appear.

**Try it:**
```bash
cd 12-self-modifying-agent
pip install -r requirements.txt
python generate_manifest.py
python self_modifying_runtime.py
```

---

### **13. Practical Quickstart (Minimal Abstractions)** ([13-practical-quickstart/](13-practical-quickstart/)) ⚡
**Smallest possible end-to-end agent using shared primitives**

Single-decision customer-support router built with the shared `RouteDefinition` helper, plus in-memory MCP stubs via `DictToolServer`. Minimal files, maximum reuse.

- ✅ Manifest generated from a handful of route definitions
- ✅ Zero-boilerplate MCP servers (dictionary-dispatched)
- ✅ Lightweight runtime harness (no Postgres, no extra scaffolding)

**Perfect for:** Teams that want a copy-paste starter showing the abstractions in their simplest form.

**Try it:**
```bash
cd 13-practical-quickstart
pip install -r requirements.txt
python generate_manifest.py
# start MCP stubs
python servers.py --server billing
python servers.py --server tech
python servers.py --server account
# run agent
python run_agent.py
```

---

## 🔄 **Migration Guides**

### **Migrating from LangGraph** ([migration-guides/langgraph-to-uaa.md](migration-guides/langgraph-to-uaa.md))

Step-by-step guide to convert existing LangGraph agents to Universal Agent Architecture.

- Automatic conversion with `nexus translate`
- Manual migration patterns
- Common pitfalls
- Testing strategies

---

### **Migrating from AWS Step Functions** ([migration-guides/aws-to-uaa.md](migration-guides/aws-to-uaa.md))

Convert AWS Step Functions state machines to UAA manifests.

- ASL → UAA conversion
- Lambda function integration
- State management
- Deployment strategies

---

### **Building Custom Optimization Passes** ([migration-guides/custom-optimization-passes.md](migration-guides/custom-optimization-passes.md))

Extend Universal Agent Nexus with your own optimization passes.

- PassManager architecture
- Writing custom transforms
- Testing optimization passes
- Integration with compiler pipeline

---

## 🚀 **Getting Help**

- **Documentation:** [Universal Agent Nexus Docs](https://github.com/mjdevaccount/universal_agent_nexus)
- **Issues:** [Report a bug](https://github.com/mjdevaccount/universal_agent_nexus/issues)
- **Discussions:** [Ask questions](https://github.com/mjdevaccount/universal_agent_nexus/discussions)

---

## 🤝 **Contributing**

Want to add an example? Pull requests welcome!

1. Fork this repository
2. Add your example in a new directory
3. Submit a pull request

---

## 📄 **License**

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with [Universal Agent Nexus](https://github.com/mjdevaccount/universal_agent_nexus)**

⭐ **Star the main project** if these examples help you!

</div>
