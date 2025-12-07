# 13. Practical Quickstart (Minimal Abstractions)

A compact, end-to-end customer-support agent that reuses the shared router builder and a tiny MCP stub server helper. The goal is maximum reuse and minimum boilerplate.

## Files
- `generate_manifest.py` — builds the manifest via `build_decision_agent_manifest` + `RouteDefinition`.
- `servers.py` — in-memory MCP stubs created with `DictToolServer` (billing, tech, account).
- `run_agent.py` — minimal LangGraph runtime harness.

## Usage
```bash
# 1) Generate manifest (uses shared router builder)
python generate_manifest.py

# 2) Start MCP stubs in separate shells
python servers.py --server billing
python servers.py --server tech
python servers.py --server account

# 3) Run the agent
python run_agent.py
```
