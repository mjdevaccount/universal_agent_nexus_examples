# Self-Modifying Agent (Runtime Tool Generation)

Demonstrates how to evolve an agent at runtime using reusable helpers from `tools/universal_agent_tools`. The example ingests failure logs, generates a dedicated MCP repair tool, wires it into the router, and recompiles the manifest.

## What this shows
- ✅ Reusable `SelfModifyingAgent` helper for manifest evolution
- ✅ Deterministic tool generation from error messages
- ✅ Router wiring that keeps the single-decision design while allowing new branches
- ✅ End-to-end regeneration of an evolved agent file (`agent_evolved.py`)

## Files
- `generate_manifest.py` — builds the base decision-manifest with reusable router helpers.
- `manifest.yaml` — generated baseline manifest (2 routes + formatter).
- `self_modifying_runtime.py` — ingests an execution log, generates a repair tool, wires it in, and recompiles.
- `requirements.txt` — minimal dependencies for the demo.

## Run it
```bash
cd 12-self-modifying-agent
pip install -r requirements.txt
python generate_manifest.py  # regenerate baseline if desired
python self_modifying_runtime.py
```

After running, the evolved agent code is written to `agent_evolved.py` with the newly injected repair route.
