# Nexus Build Pipeline & Fabric Coverage

This matrix standardizes how every example moves through the Nexus pipeline:

1. **Design layer** – a manifest (YAML) that defines graphs, routers, and tools.
2. **Compile layer** – `nexus compile <manifest> --target langgraph --output agent.py` to produce an executable artifact.
3. **Runtime layer** – `python run_agent.py` (or equivalent) that executes the compiled graph and attaches Cache Fabric + observability.

## Fabric defaults

Use `shared.cache_fabric.defaults.resolve_fabric_from_env` to make backend choice consistent across examples. The helper defaults to in-memory Fabric and supports `CACHE_BACKEND=memory|redis|vector` plus `REDIS_URL` / `VECTOR_URL` overrides.

```python
from shared.cache_fabric import resolve_fabric_from_env

fabric, meta = resolve_fabric_from_env()
print(f"Fabric backend: {meta['backend']}")
```

> Baseline expectation: **every example should either wire Cache Fabric explicitly or at least inherit the default (memory) selection above.**

## Example pipeline matrix

| Example | Design source | Compile command | Runtime entry | Fabric stance |
| --- | --- | --- | --- | --- |
| 01 – Hello World | `manifest.yaml` | `nexus compile manifest.yaml --target langgraph --output agent.py` | `python agent.py` | Uses default Fabric helper (memory unless overridden) |
| 02 – Content Moderation | `manifest.yaml` | `nexus compile manifest.yaml --target langgraph --output agent.py` | `python run_agent.py` | Uses default Fabric helper (memory unless overridden) |
| 03 – Data Pipeline | `manifest.yaml` | `nexus compile manifest.yaml --target langgraph --output agent.py` | `python run_agent.py` | Uses default Fabric helper (memory unless overridden) |
| 04 – Support Chatbot | `manifest.yaml` | `nexus compile manifest.yaml --target langgraph --output agent.py` | `python run_agent.py` | Uses default Fabric helper (memory unless overridden) |
| 05 – Research Assistant | `manifest.yaml` | `nexus compile manifest.yaml --target langgraph --output agent.py` | `python run_agent.py` | Uses default Fabric helper (memory unless overridden) |
| 06 – Playground Simulation | Frontend + backend Python services | _N/A (no manifest)_ | `uvicorn backend/main:app --port 8888` | Fabric optional; defaults to helper when added |
| 07 – Innovation Waves | Frontend + backend Python services | _N/A (no manifest)_ | `python backend/main.py` | Fabric optional; defaults to helper when added |
| 08 – Local Agent Runtime | Runtime-oriented repo (MCP servers) | _N/A (runtime-first)_ | `python runtime/agent_runtime.py` | Fabric optional; defaults to helper when added |
| 09 – Autonomous Flow | `autonomous_flow.yaml` | `nexus compile autonomous_flow.yaml --target langgraph --output agent.py` | `python runtime/autonomous_runtime.py` | Uses default Fabric helper (memory unless overridden) |
| 10 – Local LLM Tool Servers | Tool-service scaffolding | _N/A (runtime-first)_ | `python organization_agent.py` | Fabric optional; defaults to helper when added |
| 11 – N-Decision Router | `manifest.yaml` | `nexus compile manifest.yaml --target langgraph --output agent.py` | `python run_agent.py` | Uses default Fabric helper (memory unless overridden) |
| 12 – Self-Modifying Agent | `manifest.yaml` | `nexus compile manifest.yaml --target langgraph --output agent.py` | `python run_agent.py` | Uses default Fabric helper (memory unless overridden) |
| 13 – Practical Quickstart | `manifest.yaml` | `nexus compile manifest.yaml --target langgraph --output agent.py` | `python run_agent.py` | Uses default Fabric helper (memory unless overridden) |
| 15 – Cached Content Moderation | `manifest.yaml` | `nexus compile manifest.yaml --target langgraph --output agent.py` | `python run_fabric_demo.py` | Fabric integrated (tracks compilation + runtime feedback) |

### How to upgrade an example to the full three-layer path

1. Add/verify a manifest under the example root (`manifest.yaml` preferred).
2. Document `nexus compile` using the command above (output `agent.py`).
3. In the runtime entrypoint, call `resolve_fabric_from_env()` and route both compiled contexts and runtime feedback through Fabric (see `15-cached-content-moderation/run_fabric_demo.py`).

Aligning to this matrix keeps new examples predictable and ensures Cache Fabric is consistently available—even when an example does not yet require advanced caching.
