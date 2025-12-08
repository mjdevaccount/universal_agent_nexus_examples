<div align="center">

# **Universal Agent Examples**

### *Real-world examples for [Universal Agent Nexus](https://github.com/mjdevaccount/universal_agent_nexus)*

**Learn by doing: content moderation, data pipelines, chatbots, research assistants, interactive playground, and migration guides.**

[![Examples](https://img.shields.io/badge/examples-14-blue.svg)](.)
[![Tests](https://img.shields.io/badge/tests-5%2F5%20passing-green.svg)](.)
[![Local LLM](https://img.shields.io/badge/local%20LLM-Ollama%20ready-orange.svg)](.)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 🎉 **December 2025 Accomplishments**

### ✅ **All Core Examples Passing**
All 5 foundational examples (01-05) are fully tested and passing:
- **01 Hello World** - Basic manifest compilation and execution
- **02 Content Moderation** - Multi-stage pipeline with comprehensive risk-level tests
- **03 Data Pipeline** - ETL with LLM enrichment
- **04 Support Chatbot** - Intent classification with test suite
- **05 Research Assistant** - Document analysis pipeline (graph name fix applied)

### 🤖 **Local LLM Integration**
The repository now features extensive support for **100% local execution** using Ollama:

- **Examples 06-07**: Gemma 2B for multi-agent simulations (1000 agents at 60fps)
- **Example 08**: Llama 3.2 11B with native function calling + MCP tool integration
- **Example 09**: Autonomous agents with Ollama (llama3.2) for dynamic tool discovery
- **Example 10**: Qwen2.5 32B research agent with embeddings and SQLite backend
- **Zero API costs** - All local LLM examples run completely offline

### 🧪 **Comprehensive Testing Infrastructure**
- **Automated test runner**: `python tools/test_all_examples.py` validates all examples
- **Example-specific tests**: Risk-level tests (02), intent classification tests (04)
- **Fabric integration tests**: Validates Universal Agent Fabric archetype integration
- **Test coverage**: All examples include validation scripts and test data

### 🔧 **Production-Ready Features**
- Unicode encoding fixes applied across all examples
- Graph name consistency fixes (example 05)
- Standardized command conventions across all 14 examples
- Three-layer pipeline: Design → Compile → Runtime with Cache Fabric integration

---

## 🎯 **Quick Start**

```bash
# Install Universal Agent Nexus and Tools
pip install universal-agent-nexus universal-agent-tools

# Clone examples
git clone https://github.com/mjdevaccount/universal_agent_nexus_examples.git
cd universal_agent_nexus_examples

# Run an example
cd 01-hello-world
nexus compile manifest.yaml --target langgraph --output agent.py
python agent.py
```

### 🔄 **Command Conventions**

- [EXAMPLES_COMMAND_CONVENTIONS.md](EXAMPLES_COMMAND_CONVENTIONS.md) documents the standard compile/run/test/serve commands used across every example.
- [NEXUS_PIPELINE_MATRIX.md](NEXUS_PIPELINE_MATRIX.md) shows the design → compile → runtime → Cache Fabric coverage for each example.
- Run `python tools/example_runner.py list` to see the canonical commands for each example, `python tools/example_runner.py show <id>` for details, or `python tools/example_runner.py matrix` for the standardized pipeline view.

### 🧪 **Quick Test**

Test all examples to verify your setup:

```bash
# Test all core examples (01-05)
python tools/test_all_examples.py

# Test with verbose output
python tools/test_all_examples.py --verbose
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
- ✅ **Comprehensive test suite** (`test_all_risk_levels.py`) - All risk levels validated

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
- ✅ **Intent classification tests** (`test_intents.py`) - All intent types validated

**Perfect for:** Customer support, help desks, chatbots

---

### **5. Research Assistant** ([05-research-assistant/](05-research-assistant/))
**Document Analysis & Summarization**

Analyze documents, extract insights, and generate summaries.

- ✅ Document parsing
- ✅ Key point extraction
- ✅ Multi-document synthesis
- ✅ Citation tracking
- ✅ **Tested and passing** (graph name consistency fixed)

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

### **13. Practical Quickstart** ([13-practical-quickstart/](13-practical-quickstart/)) ⚡
**Batteries-Included Starter Template**

Production-ready starter with sensible defaults, MCP server integration, and best practices.

- ✅ Pre-configured manifest structure
- ✅ MCP server examples
- ✅ Standard command conventions
- ✅ Cache Fabric integration ready

**Perfect for:** Teams starting new projects, learning best practices

**Try it:**
```bash
cd 13-practical-quickstart
pip install -r requirements.txt
python generate_manifest.py
nexus compile manifest.yaml --target langgraph --output agent.py
python run_agent.py
```

---

### **14. Cached Content Moderation** ([14-cached-content-moderation/](14-cached-content-moderation/)) 💾
**Cache Fabric Integration Demo**

Demonstrates Cache Fabric integration with compiler output, runtime executions, and feedback tracking.

- ✅ Cache Fabric integration (memory/Redis/vector backends)
- ✅ Compiler output caching
- ✅ Runtime execution tracking
- ✅ Feedback loop integration

**Perfect for:** Understanding Cache Fabric patterns, production caching strategies

**Try it:**
```bash
cd 14-cached-content-moderation
pip install -r requirements.txt
python run_fabric_demo.py
```

---

## 🧪 **Testing Infrastructure**

### **Automated Test Runner**

Run all examples with a single command:

```bash
# Test all examples
python tools/test_all_examples.py

# Test specific examples
python tools/test_all_examples.py --examples 01 02 03

# Include server-based examples (06, 07, 08)
python tools/test_all_examples.py --include-servers

# Verbose output
python tools/test_all_examples.py --verbose

# Custom timeout
python tools/test_all_examples.py --timeout 120
```

### **Example-Specific Tests**

Each example includes targeted tests:

- **02 Content Moderation**: `test_all_risk_levels.py` - Validates all 5 risk levels (safe, low, medium, high, critical)
- **04 Support Chatbot**: `test_intents.py` - Tests all intent classifications (FAQ, technical, billing, complaint, other)
- **06 Playground Simulation**: `tests/test_fabric_integration.py` - Validates Fabric archetype integration
- **08 Local Agent Runtime**: `test_runtime.py` - Validates MCP tool loading and LangGraph agent creation

### **Test Status (December 2025)**

✅ **5/5 Core Examples Passing:**
- 01 Hello World
- 02 Content Moderation (with comprehensive risk-level tests)
- 03 Data Pipeline
- 04 Support Chatbot (with intent classification tests)
- 05 Research Assistant (graph name consistency fixed)

### **Local LLM Testing**

Examples 06-10 include local LLM integration tests that validate:
- Ollama model availability
- Function calling capabilities
- MCP tool integration
- Runtime execution with local models

**Supported Models:**
- **Gemma 2B** (Examples 06-07) - Fast inference, function calling support
- **Llama 3.2 11B** (Example 08) - Native function calling, MCP integration
- **Qwen2.5 32B** (Example 10) - Research agent with embeddings

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
- **API Reference:** [API_REFERENCE.md](API_REFERENCE.md) - Complete API documentation
- **Cache Fabric Guide:** [docs/CACHE_FABRIC_INTEGRATION_GUIDE.md](docs/CACHE_FABRIC_INTEGRATION_GUIDE.md)
- **Output Parsers Guide:** [docs/OUTPUT_PARSERS_GUIDE.md](docs/OUTPUT_PARSERS_GUIDE.md)

---

## 🤝 **Contributing**

Want to add an example? Pull requests welcome!

1. Fork this repository
2. Add your example in a new directory
3. Follow the [command conventions](EXAMPLES_COMMAND_CONVENTIONS.md)
4. Include tests (see examples 02, 04 for patterns)
5. Update the [pipeline matrix](NEXUS_PIPELINE_MATRIX.md)
6. Submit a pull request

### **Contributing Guidelines**

- **Follow the three-layer model**: Design (manifest.yaml) → Compile → Runtime
- **Include tests**: Add validation scripts for your example
- **Document local LLM support**: If using Ollama, document model requirements
- **Use standard commands**: Follow `compile`, `run`, `test` conventions
- **Cache Fabric integration**: Use `resolve_fabric_from_env()` for consistency

---

## 📄 **License**

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with [Universal Agent Nexus](https://github.com/mjdevaccount/universal_agent_nexus)**

⭐ **Star the main project** if these examples help you!

</div>
