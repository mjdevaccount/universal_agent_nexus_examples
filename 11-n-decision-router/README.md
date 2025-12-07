# N-Decision Router Example

This example generalizes the single-decision router pattern into an **N-decision agent** while keeping tools and router wiring fully reusable. It leans on the shared helpers in `tools/universal_agent_tools` so the routing logic can be promoted or embedded in other projects without copy/paste.

## What’s inside?

- **Manifest (`manifest.yaml`)** built with four routes (data quality, growth experiments, customer support, reporting).
- **`generate_manifest.py`** shows how to rebuild the manifest programmatically using `RouteDefinition` + `build_decision_agent_manifest`.
- **`adaptive_router.py`** demonstrates adding runtime CSV-derived tools via `DynamicCSVToolInjector` without touching the router topology.
- **`requirements.txt`** pins the minimal dependencies for compiling or generating code.

## Architecture

```
User Query → Decision Router → (N tool paths) → Formatter
```

- **Single router, many decisions** — the router makes one decision per invocation, but the number of destinations is configurable.
- **Reusable wiring** — routes are defined as data (`RouteDefinition`), so teams can expand or shrink decisions without editing YAML by hand.
- **Dynamic tools** — CSV uploads (or other external context) can inject new MCP tools and edges at runtime using the shared IR visitor.

## Quickstart

```bash
pip install -r requirements.txt

# Rebuild the manifest from code (uses shared router helper)
python generate_manifest.py

# Optionally compile to LangGraph for local runs
nexus compile manifest.yaml --target langgraph --output agent.py
python agent.py  # or integrate into your runtime
```

## Key Reusable Pieces

- `RouteDefinition` and `build_decision_agent_manifest` (from `tools/universal_agent_tools/router_patterns.py`) turn a list of routes into a full manifest with router + edges + formatter.
- `DynamicCSVToolInjector` (from `tools/universal_agent_tools/dynamic_tools.py`) appends new tools and edges without modifying the router code.

## Extending the router

Add or remove routes in `generate_manifest.py` and regenerate the manifest. Because the edges are derived from route definitions, the manifest always stays in sync with the tool catalog.
