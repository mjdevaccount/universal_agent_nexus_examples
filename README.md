<div align="center">

# 🚀 **Universal Agent Examples**

### *Showcasing the Universal Agent Nexus — Build Once, Run Anywhere*

**This repository exists for one purpose:**

Show—through real, runnable code—that a single Universal Agent manifest can execute across multiple runtimes (LangGraph, AWS Step Functions, MCP, or the UAA Kernel) without rewriting your agent logic.

**Every example in this repository is a working proof of that idea.**

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
- **05 Research Assistant** - Document analysis pipeline (graph name consistency fixed)

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

## 🎯 **Why This Repo Exists**

You shouldn't have to rebuild your agents every time you change where they run.

- **Develop in LangGraph**
- **Deploy at scale with AWS Step Functions**
- **Expose to Claude Desktop via MCP**
- **Run fully offline on local LLMs**
- **Execute natively through the UAA Kernel**

### **Traditionally:**

❌ Each runtime = a separate codebase  
❌ Different file formats  
❌ Different execution models  
❌ Drift, duplication, and rewrites

### **With Universal Agent Nexus:**

```
manifest.yaml
        ↓
    nexus compile --target langgraph
    nexus compile --target aws
    nexus compile --target mcp
    nexus compile --target uaa
```

**Same agent logic.**
**Zero rewrites.**
**Different runtimes.**

That's the entire point of this repo. Every example below is a lens on this promise.

---

## 🧠 **How These Examples Teach the Universal Agent Architecture**

Every example, simple or advanced, is built from the same five abstractions:

```
GRAPH  ── defines the workflow
ROUTER ── decides what path to take
TASK   ── does LLM work (generation)
TOOLS  ── call external capabilities (MCP, HTTP, local)
OBSERVER ─ metrics, traces, logs
```

You do not need to learn theory first. These examples make the architecture intuitive by using it:

- Moderate unsafe text
- Classify user intents
- Run ETL + enrichment jobs
- Analyze documents
- Simulate 1000-agent economies
- Run tool-driven agents locally
- Auto-discover tools
- Regenerate manifests
- Add caching, batching, Fabric integration

**If you understand one example, you understand all of them.**

---

## 🔥 **The One Diagram Everyone Should See**

Put this in your head:

```
        DESIGN
       manifest.yaml
            ↓
       COMPILATION
         (Nexus)
            ↓
        RUNTIME
 ┌─────────┬───────────┬───────────┬────────────┐
 │LangGraph│   AWS     │   MCP     │    UAA     │
 │ Python  │ Step Fn   │ stdio     │  Kernel    │
 └─────────┴───────────┴───────────┴────────────┘
```

**These examples just prove this diagram from every angle.**

---

## 🧭 **Recommended Learning Path**

### **BEGINNER (01–05): Core Agent Concepts**

These five examples give you the entire UAA mental model:

- **01 – Hello World** – Your first graph & compile
- **02 – Content Moderation** – Routers + policy checks + tests
- **03 – Data Pipeline** – ETL + LLM enrichment
- **04 – Support Chatbot** – Intent routing + multi-turn dialogue
- **05 – Research Assistant** – Document analysis + synthesis

### **INTERMEDIATE (06–10): Multi-Agent & Multi-Runtime**

Explore scale, local execution, and runtime translation:

- **06 – Playground Simulation** 🎮 – Multi-agent personalities (Gemma 2B)
- **07 – Innovation Waves** 🚀 – 300–1000 agents across 5 runtimes (Gemma 2B)
- **08 – Local Agent Runtime** 🤖 – MCP tools + LangGraph + Ollama (Llama 3.2 11B)
- **09 – Autonomous Flow** 🛰️ – Tool discovery + self-regeneration (Ollama)
- **10 – Tool Server Patterns** 🧠 – Qwen research agent, routers, tenant isolation (Qwen2.5 32B)

### **ADVANCED (11–14): Patterns, Autonomy, Fabric**

For architecture-minded engineers:

- **11 – N-Decision Router** 🛣️ – Declarative routing at scale
- **12 – Self-Modifying Agent** 🔁 – Generate new tools from logs
- **13 – Practical Quickstart** ⚡ – Production starter template
- **14 – Cached Moderation** 💾 – Cache Fabric integration + runtime caching

---

## ⚡ **Quick Start**

```bash
# Install dependencies
pip install universal-agent-nexus universal-agent-tools

# Clone examples
git clone https://github.com/mjdevaccount/universal_agent_nexus_examples.git
cd universal_agent_nexus_examples

# Run your first example
cd 01-hello-world
nexus compile manifest.yaml --target langgraph --output agent.py
python agent.py

# Test all examples
python tools/test_all_examples.py
```

### 🔄 **Command Conventions**

- [EXAMPLES_COMMAND_CONVENTIONS.md](EXAMPLES_COMMAND_CONVENTIONS.md) documents the standard compile/run/test/serve commands used across every example.
- [NEXUS_PIPELINE_MATRIX.md](NEXUS_PIPELINE_MATRIX.md) shows the design → compile → runtime → Cache Fabric coverage for each example.
- Run `python tools/example_runner.py list` to see the canonical commands for each example, `python tools/example_runner.py show <id>` for details, or `python tools/example_runner.py matrix` for the standardized pipeline view.

---

## 📚 **Example Index (Concise)**

### **01 – Hello World**
Graph → compile → run.

### **02 – Content Moderation**
Router logic + branching + risk-level tests (`test_all_risk_levels.py`).

### **03 – Data Pipeline**
ETL pattern + LLM enrichment + validation.

### **04 – Support Chatbot**
Multi-turn workflow + intent tests (`test_intents.py`).

### **05 – Research Assistant**
Document analysis + multi-doc synthesis. (Graph name consistency fixed)

### **06 – Playground Simulation** 🎮
Real-time personality-driven agent simulation. Gemma 2B local LLM.

**Try it:**
```bash
cd 06-playground-simulation
ollama pull gemma:2b-instruct
uvicorn backend/main:app --port 8888
# Open frontend/index.html
```

### **07 – Innovation Waves** 🚀
1000-agent adoption model running across 5 runtimes. Gemma 2B at 60fps.

**Try it:**
```bash
cd 07-innovation-waves
ollama pull gemma:2b-instruct
pip install -r backend/requirements.txt
python backend/main.py
# Open frontend/index.html (single view)
# Open frontend/demo-matrix.html (5-runtime matrix)
```

### **08 – Local Agent Runtime** 🤖
MCP + LangGraph + local LLM compilation pipeline. Llama 3.2 11B with native function calling.

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

### **09 – Autonomous Flow** 🛰️
Agents that discover tools → regenerate manifests → run. Ollama (llama3.2) for routing.

**Try it:**
```bash
cd 09-autonomous-flow
python runtime/autonomous_runtime.py
```

### **10 – LLM Tool Server Patterns** 🧠
Qwen research agent, nested scaffolding, isolation. Qwen2.5 32B with embeddings.

**Try it:**
```bash
cd 10-local-llm-tool-servers/research_agent
ollama pull qwen2.5:32b
pip install -r ../requirements.txt
python run_local.py
```

### **11 – N-Decision Router** 🛣️
Declarative routing patterns with dynamic tool injection.

**Try it:**
```bash
cd 11-n-decision-router
pip install -r requirements.txt
python generate_manifest.py
nexus compile manifest.yaml --target langgraph --output agent.py
```

### **12 – Self-Modifying Agent** 🔁
Failure patterns → new tool generation → new manifest.

**Try it:**
```bash
cd 12-self-modifying-agent
pip install -r requirements.txt
python generate_manifest.py
python self_modifying_runtime.py
```

### **13 – Practical Quickstart** ⚡
Batteries-included starter template.

**Try it:**
```bash
cd 13-practical-quickstart
pip install -r requirements.txt
python generate_manifest.py
nexus compile manifest.yaml --target langgraph --output agent.py
python run_agent.py
```

### **14 – Cached Moderation** 💾
Complete Cache Fabric integration demo (memory/Redis/vector stores).

**Try it:**
```bash
cd 14-cached-content-moderation
pip install -r requirements.txt
python run_fabric_demo.py
```

---

## 🧪 **Test Infrastructure**

```bash
# Test all examples
python tools/test_all_examples.py

# Verbose output
python tools/test_all_examples.py --verbose

# Include server-based examples (06, 07, 08)
python tools/test_all_examples.py --include-servers

# Test specific examples
python tools/test_all_examples.py --examples 01 02 03

# Custom timeout
python tools/test_all_examples.py --timeout 120
```

### **Example-Specific Tests**

Each major example has its own test suite:

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

### **Migrating from AWS Step Functions** ([migration-guides/aws-to-uaa.md](migration-guides/aws-to-uaa.md))

Convert AWS Step Functions state machines to UAA manifests.

- ASL → UAA conversion
- Lambda function integration
- State management
- Deployment strategies

### **Building Custom Optimization Passes** ([migration-guides/custom-optimization-passes.md](migration-guides/custom-optimization-passes.md))

Extend Universal Agent Nexus with your own optimization passes.

- PassManager architecture
- Writing custom transforms
- Testing optimization passes
- Integration with compiler pipeline

---

## 🔗 **Related Repositories**

| Repo | Purpose |
|------|---------|
| [Universal Agent Nexus](https://github.com/mjdevaccount/universal_agent_nexus) | The translation layer — compile once, run anywhere |
| Universal Agent Fabric | Composition layer — roles, domains, policies → enriched manifest |
| UAA Architecture / Kernel | Runtime execution layer |

These examples sit above Architecture and beside Fabric — purely to show what Nexus enables.

---

## 🚀 **Getting Help**

- **Documentation:** [Universal Agent Nexus Docs](https://github.com/mjdevaccount/universal_agent_nexus)
- **Issues:** [Report a bug](https://github.com/mjdevaccount/universal_agent_nexus/issues)
- **Discussions:** [Ask questions](https://github.com/mjdevaccount/universal_agent_nexus/discussions)
- **API Reference:** [API_REFERENCE.md](API_REFERENCE.md) - Complete API documentation
- **Cache Fabric Guide:** [docs/CACHE_FABRIC_INTEGRATION_GUIDE.md](docs/CACHE_FABRIC_INTEGRATION_GUIDE.md)
- **Output Parsers Guide:** [docs/OUTPUT_PARSERS_GUIDE.md](docs/OUTPUT_PARSERS_GUIDE.md)

---

## 🙌 **Contributing**

PRs welcome! Follow the standard:

1. Create a directory
2. Add manifest + runtime code
3. Add tests
4. Follow the [command conventions](EXAMPLES_COMMAND_CONVENTIONS.md)
5. Update the [pipeline matrix](NEXUS_PIPELINE_MATRIX.md)
6. Submit the PR

### **Contributing Guidelines**

- **Follow the three-layer model**: Design (manifest.yaml) → Compile → Runtime
- **Include tests**: Add validation scripts for your example
- **Document local LLM support**: If using Ollama, document model requirements
- **Use standard commands**: Follow `compile`, `run`, `test` conventions
- **Cache Fabric integration**: Use `resolve_fabric_from_env()` for consistency

---

## ⭐ **Final Word**

If you only remember one sentence:

**These examples exist to prove that agent logic should never be tied to runtime code again. Nexus keeps the manifest constant, and translates it wherever you need it to run.**

This repo demonstrates how far you can push the Universal Agent Architecture:

- local LLMs (Gemma 2B, Llama 3.2, Qwen2.5)
- streaming multi-agent worlds (1000 agents at 60fps)
- durable pipelines
- tool-driven autonomy
- self-modifying agents
- multi-runtime deployment
- Cache Fabric integration

**All with one manifest and zero vendor lock-in.**

If this repo helped you understand that vision, star the main project:

👉 **[https://github.com/mjdevaccount/universal_agent_nexus](https://github.com/mjdevaccount/universal_agent_nexus)**

<div align="center">

**Built with [Universal Agent Nexus](https://github.com/mjdevaccount/universal_agent_nexus)**

⭐ **Star the main project** if these examples help you!

</div>
