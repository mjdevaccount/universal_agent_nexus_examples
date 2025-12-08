# Example Command Conventions

This repo now contains a mix of introductory and advanced Universal Agent Nexus examples. To keep them consistent, every example should publish the same set of runnable commands and use the shared tooling instead of bespoke scripts.

> For a per-example view of **design → compile → runtime → fabric** coverage, see [NEXUS_PIPELINE_MATRIX.md](NEXUS_PIPELINE_MATRIX.md).

## Three-layer model (Nexus + Cache Fabric)

All examples should align to the three-layer pipeline:

1. **Design** – a manifest (`manifest.yaml` recommended) that defines graphs, routers, and tools.
2. **Compile** – `nexus compile <manifest> --target langgraph --output agent.py` to emit a runnable graph.
3. **Runtime** – a Python entrypoint (`run_agent.py` preferred) that executes the compiled graph and attaches Cache Fabric and observability.

Cache Fabric defaults are centralized in `shared/cache_fabric/defaults.py`; use `resolve_fabric_from_env()` so every example has a consistent fallback (memory by default, opt-in Redis/vector via env vars).

## Standard command surface

Each example should expose the following commands (omit only if the capability truly does not apply):

1. **Compile** – produce a runnable artifact from `manifest.yaml`.
   ```bash
   nexus compile manifest.yaml --target langgraph --output agent.py
   ```
2. **Run (local)** – execute the example in-place.
   ```bash
   python run_agent.py  # or python agent.py when only the compiled graph is used
   ```
3. **Validate** – run any smoke tests the example carries.
   ```bash
   python -m pytest
   ```
4. **Serve (optional)** – expose the graph as an MCP server when interactive tools are present.
   ```bash
   nexus serve manifest.yaml --protocol mcp --transport stdio
   ```

When adding new examples, prefer `run_agent.py` as the entrypoint name and keep commands self-contained so the wrapper below can surface them automatically.

## Command wrapper (tools/example_runner.py)

`tools/example_runner.py` provides a uniform way to list and print the canonical commands for every example. Usage:

```bash
# List examples with a one-line description
python tools/example_runner.py list

# Show the commands for a single example
python tools/example_runner.py show 08

# Show Nexus → LangGraph compile/run/fabric matrix
python tools/example_runner.py matrix

# (Optional) execute a command in the example's working directory
python tools/example_runner.py run 01 compile --execute
```

The wrapper is intentionally conservative: by default it only prints the commands so you can copy/paste them. Use `--execute` when you want it to run the steps in-process.

## Current command matrix

| Example | Scope | Canonical commands |
| --- | --- | --- |
| 01 – Hello World | Basic compile/run | `nexus compile manifest.yaml --target langgraph --output agent.py`; `python agent.py` |
| 02 – Content Moderation | Multi-stage pipeline | `python run_agent.py`; `python -m pytest` (tests included) |
| 03 – Data Pipeline | ETL + enrichment | `python run_agent.py` |
| 04 – Support Chatbot | Router + handoff | `python run_agent.py`; `python -m pytest` |
| 05 – Research Assistant | Doc analysis | `python run_agent.py` |
| 06 – Playground Simulation | Multi-agent sim (frontend + backend) | `pip install -r backend/requirements.txt`; `uvicorn backend/main:app --port 8888` |
| 07 – Innovation Waves | Simulation matrix | `pip install -r backend/requirements.txt`; `python backend/main.py` |
| 08 – Local Agent Runtime | MCP + LangGraph + Ollama | `pip install -r backend/requirements.txt`; start filesystem & git MCP servers; `python runtime/agent_runtime.py` |
| 09 – Autonomous Flow | Dynamic tool discovery | `python runtime/autonomous_runtime.py` |
| 10 – Local LLM Tool Servers | Nested scaffolding + enrichment | `pip install -r requirements.txt`; `python organization_agent.py` or `python research_agent/run_local.py` |
| 11 – N-Decision Router | Adaptive router patterns | `pip install -r requirements.txt`; `python run_agent.py` |
| 12 – Self-Modifying Agent | Hot manifest regeneration | `python run_agent.py` |
| 13 – Practical Quickstart | Batteries-included starter | `python run_agent.py` |
| 15 – Cached Content Moderation | Cache Fabric + observability | `pip install -r requirements.txt`; `python run_fabric_demo.py` |

## Promoted abstractions

- **Cache Fabric Layer** – Use the shared helpers in `shared/cache_fabric/` instead of ad-hoc caching. The cached content moderation example already routes compiler output, runtime executions, and feedback through this layer while supporting Redis and vector backends.【F:15-cached-content-moderation/run_fabric_demo.py†L19-L129】
- **Observability helper** – Prefer `universal_agent_tools.observability` for tracing instead of per-example wrappers; it integrates cleanly with the Cache Fabric workflow.【F:15-cached-content-moderation/run_fabric_demo.py†L17-L23】【F:15-cached-content-moderation/run_fabric_demo.py†L36-L96】
- **MCP-aware runtimes** – Use LangGraph runtimes paired with MCP tool discovery (examples 08–10) rather than custom request loops. The wrapper highlights which examples already follow this pattern so new ones can align.

## Recommendations

1. **Reuse shared libraries:** Replace bespoke cache or logging code with the Cache Fabric and observability helpers noted above.
2. **Keep manifests first-class:** Ensure every runnable graph flows through `manifest.yaml` + `nexus compile` so the wrapper can present consistent `compile` and `run` steps.
3. **Document MCP endpoints the same way:** When tools are exposed via MCP, add a `serve` command block using the standard `nexus serve` invocation shown above.
4. **Prefer python entrypoints:** Name runtime scripts `run_agent.py` (or `run_<role>.py` when multiple variants exist) so contributors can locate the correct command quickly.

These conventions make it easier to add or evolve examples without re-learning unique command sets each time.
