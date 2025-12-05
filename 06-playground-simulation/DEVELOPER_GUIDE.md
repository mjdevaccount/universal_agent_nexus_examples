# Developer Guide - Playground Simulation

This guide explains how to extend the Interactive Agent Playground using the Universal Agent Fabric architecture.

## Architecture Overview

```
Universal Agent Nexus (Compiler)
         ↓
Universal Agent Fabric (Composition Layer)
    ├─ Roles (fabric_archetypes/*.yaml)
    ├─ Capabilities (ontology/capabilities/*.yaml)
    ├─ Domains (ontology/domains/*.yaml)
    └─ Governance (policy/rules/*.yaml)
         ↓
FabricBuilder.build()
         ↓
Runtime (backend/main.py)
         ↓
danielmiessler Fabric (LLM Abstraction)
         ↓
Providers (OpenAI, Ollama, Anthropic...)
```

## Upstream Package Schemas

The playground uses schemas from `universal_agent_fabric`:

```python
from universal_agent_fabric import (
    Role,           # Agent role definition
    Capability,     # What an agent can do
    Domain,         # Groups of capabilities
    GovernanceRule, # Safety/policy rules
    FabricSpec,     # Complete agent specification
    FabricBuilder,  # Compiles specs
)
```

---

## Adding New Archetypes

### 1. Create Role YAML

Create a new file in `fabric_archetypes/`:

```yaml
# fabric_archetypes/inventor.yaml
name: "The Inventor"
base_template: "planning_loop"
system_prompt_template: |
  You are creative and curious. Propose novel ideas and solutions.
  Think outside the box. Ask "what if?" questions.
  Keep responses VERY SHORT (1-2 sentences max).
default_capabilities:
  - "speak"
  - "brainstorm"
```

**Schema (from `universal_agent_fabric.Role`):**
- `name`: Display name (required)
- `base_template`: Graph template - `react_loop`, `planning_loop`, `simple_response` (required)
- `system_prompt_template`: LLM system prompt (required)
- `default_capabilities`: List of capability names (optional)

### 2. Define Required Capabilities

If your archetype uses new capabilities, define them:

```yaml
# ontology/capabilities/brainstorm.yaml
name: "brainstorm"
description: "Generate creative ideas and novel solutions"
protocol: "local"
config_template:
  creativity_level: "high"
  output_count: 3
```

**Schema (from `universal_agent_fabric.Capability`):**
- `name`: Unique identifier (required)
- `description`: What this capability does (required)
- `protocol`: `local`, `mcp`, `http`, `subprocess` (required)
- `config_template`: Configuration options (optional)

### 3. Add to ARCHETYPES Dict

Update `backend/main.py`:

```python
ARCHETYPES["inventor"] = {
    "name": "The Inventor",
    "role": "Creative, curious",
    "personality": {"creativity": 10, "empathy": 6, "confidence": 7},
}
```

### 4. Test

```bash
cd 06-playground-simulation
pytest tests/test_fabric_integration.py -v
```

---

## Defining Domains

Domains group related capabilities with a system prompt mixin:

```yaml
# ontology/domains/creative.yaml
name: "creative"
description: "Creative thinking and ideation capabilities"
capabilities:
  - "speak"
  - "brainstorm"
  - "imagine"
system_prompt_mixin: |
  You approach problems creatively.
  Consider unconventional solutions.
```

**Schema (from `universal_agent_fabric.Domain`):**
- `name`: Domain identifier (required)
- `description`: What this domain covers (required)
- `capabilities`: List of capability names (required)
- `system_prompt_mixin`: Added to agent's system prompt (optional)

---

## Writing Governance Rules

Governance rules enforce safety and policy:

```yaml
# policy/rules/creativity_bounds.yaml
rules:
  - name: "no_dangerous_inventions"
    target_pattern: ".*\\b(weapon|explosive|poison)\\b.*"
    action: "deny"
    conditions:
      severity: "high"
      message: "Cannot propose dangerous inventions"
  
  - name: "encourage_safety"
    target_pattern: ".*\\b(safe|careful|responsible)\\b.*"
    action: "allow"
    conditions:
      bonus: true
```

**Schema (from `universal_agent_fabric.GovernanceRule`):**
- `name`: Rule identifier (required)
- `target_pattern`: Regex pattern to match (optional)
- `action`: `allow`, `deny`, `warn`, `monitor` (required)
- `conditions`: Additional metadata (optional)

---

## Using the Compiler

### Programmatic Usage

```python
from backend.fabric_compiler import get_compiler, compile_archetype

# Get compiler instance
compiler = get_compiler()

# Compile a single archetype
compiled = compile_archetype("inventor")

print(compiled.name)           # "The Inventor"
print(compiled.capabilities)   # ["speak", "brainstorm"]
print(compiled.domains)        # ["creative"]
print(compiled.governance_rules)  # ["no_dangerous_inventions", ...]

# Access all loaded definitions
caps = compiler.get_capabilities()
domains = compiler.get_domains()
rules = compiler.get_governance_rules()
```

### What Compilation Does

1. Loads role from `fabric_archetypes/{archetype}.yaml`
2. Resolves capabilities from `ontology/capabilities/`
3. Finds domains that provide these capabilities
4. Loads governance rules from `policy/rules/`
5. Creates `FabricSpec` with all components
6. Calls `FabricBuilder.build()` from upstream

---

## Integration with Universal Agent Nexus

The compiled agents can be exported as UAA manifests:

```python
from universal_agent_nexus import load_manifest

# Future: Export compiled agent to UAA manifest
# manifest = compiled.to_uaa_manifest()
# Then use nexus compile for different targets
```

---

## Testing

### Run All Tests

```bash
cd 06-playground-simulation
pytest tests/ -v
```

### Test Categories

1. **Schema Validation** - Archetypes/capabilities match upstream schemas
2. **Capability Resolution** - All referenced capabilities are defined
3. **Compiler Tests** - FabricBuilder produces valid output
4. **Integration Tests** - Full pipeline works end-to-end

### Adding Tests

```python
# tests/test_my_feature.py
def test_new_archetype_compiles():
    from fabric_compiler import compile_archetype
    
    compiled = compile_archetype("inventor")
    assert compiled.compiled is True
    assert "brainstorm" in compiled.capabilities
```

---

## Project Structure

```
06-playground-simulation/
├── fabric_archetypes/          # Role definitions (YOUR Fabric)
│   ├── bully.yaml
│   ├── shy_kid.yaml
│   ├── mediator.yaml
│   ├── joker.yaml
│   └── teacher.yaml
├── ontology/
│   ├── capabilities/           # Capability definitions
│   │   ├── speak.yaml
│   │   ├── analyze_situation.yaml
│   │   └── observe_situation.yaml
│   └── domains/                # Domain groupings
│       └── playground_social.yaml
├── policy/
│   └── rules/                  # Governance rules
│       └── playground_safety.yaml
├── backend/
│   ├── main.py                 # FastAPI server
│   ├── llm_provider.py         # LLM integration
│   ├── fabric_compiler.py      # FabricBuilder integration
│   └── schemas.py              # Pydantic models
├── frontend/
│   └── index.html              # Interactive UI
├── tests/
│   ├── conftest.py
│   └── test_fabric_integration.py
├── README.md
└── DEVELOPER_GUIDE.md          # This file
```

---

## Troubleshooting

### "Archetype not found"

Check that the YAML file exists in `fabric_archetypes/` and has the correct name.

### "Capability not defined"

Ensure the capability is defined in `ontology/capabilities/{name}.yaml`.

### "FabricBuilder.build() failed"

Check that all components (role, capabilities, domains) are valid according to upstream schemas.

### Tests Failing

```bash
# Run with verbose output
pytest tests/ -v --tb=long

# Run single test
pytest tests/test_fabric_integration.py::test_compiler_compiles_archetypes -v
```

---

## Contributing

1. Create archetype/capability/domain YAML
2. Update `ARCHETYPES` dict in `main.py`
3. Add tests in `tests/`
4. Run `pytest tests/ -v`
5. Submit PR

---

**Built with:**
- [Universal Agent Fabric](https://github.com/mjdevaccount/universal_agent_fabric)
- [Universal Agent Nexus](https://github.com/mjdevaccount/universal_agent_nexus)
- [danielmiessler Fabric](https://github.com/danielmiessler/fabric)

