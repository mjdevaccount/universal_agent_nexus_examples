# Universal Agent Nexus: Local LLM + Tool Server Examples

This example set demonstrates how to build locally executable, multi-agent systems that pair 16GB-class local LLMs with MCP tool servers. It captures the architecture patterns described in the "December 2025" stack: single-decision routers, nested scaffolding, tenant-aware enrichment, and dynamic tool generation.

## What's inside
- **Pattern A – Single-decision agents:** Minimal router graphs that avoid agent loops (`single_decision_agent.yaml`).
- **Pattern B – Nested scaffolding:** Hierarchical agent graphs composed via `CompilerBuilder` (`organization_agent.py` → `tools/universal_agent_tools/scaffolding.py`).
- **Pattern C – Memory separation:** Tenant-aware enrichment handlers for per-tenant isolation (`enrichment/tenant_enrichment.py` → `tools/universal_agent_tools/enrichment.py`).
- **Pattern D – Virtual tool creation:** Runtime CSV tool injection using an IR visitor (`dynamic_tools/csv_analyzer.py` → `tools/universal_agent_tools/dynamic_tools.py`).
- **Production Example – Research agent:** Local research assistant with embeddings-backed MCP tools (`research_agent/`).
- **Reusable toolkit:** Promotion-ready helpers extracted from this folder live in `tools/universal_agent_tools/`.

## Quick start (research agent)
```bash
cd 10-local-llm-tool-servers/research_agent
ollama pull qwen2.5:32b
pip install -r ../requirements.txt  # Align deps with root examples
python run_local.py
```

## Architecture snapshot
```
┌─────────────────────────────────────────────────────────────┐
│                    USER QUERY                               │
│              (Natural Language Input)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              LANGGRAPH RUNTIME (Local)                       │
│  StateGraph execution with async/await                      │
│  Entry: Decision Node (Router)                              │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
   ┌────────┐  ┌────────┐  ┌──────────┐
   │ Qwen   │  │MCP Tool│  │ Generate │
   │ Router │  │ Exec   │  │  Tools   │
   └────────┘  └────────┘  └──────────┘
        │            │            │
        └────────────┼────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          MCP TOOL SERVERS (Parallel)                        │
│  - Database Query Server (sqlite3)                          │
│  - File System Server (safe read/write)                     │
│  - Calculation Server (sympy)                               │
│  - Research Server (local embeddings + sqlite)              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│         POSTGRES CHECKPOINTING (Optional)                   │
│         Store state for resumption/replay                   │
└─────────────────────────────────────────────────────────────┘
```

## Patterns
- **Single decision per agent:** Router nodes make exactly one decision before delegating to tools or sub-graphs, cutting token use.
- **Nested scaffolding:** `CompilerBuilder` composes sub-agents (teams) into larger organizations with clear entry points.
- **Memory separation:** Enrichment handlers inject tenant metadata, policies, and isolated vector stores per compilation.
- **Virtual tool creation:** IR visitors can inject new MCP tool definitions (for uploads) and connect them to routers.

## Production-grade stack
- LLM: Qwen2.5 (32B) via Ollama
- Vector DB: SQLite + `all-minilm` embeddings
- Tools: MCP servers for research, filesystem, calculations
- Runtime: LangGraph runtime compiled from Nexus manifests
- Optional checkpointing: Postgres for resumable executions

## Cost snapshot
- **LLM:** ~2 calls (router + formatter) ≈ $0.001 per query
- **Embeddings + storage:** Local and free (SQLite + CPU embeddings)
- **Compared to cloud APIs:** ~50× cheaper for the same workload
