# Migration Guide: Q1 2026 Promotion

**Target Release:** Q1 2026  
**Affected Packages:** `universal-agent-nexus@3.1.0`, `universal-agent-tools@1.1.0`

## Quick Reference: Import Changes

### Tool Registry

**Before (Examples):**
```python
from tools.registry.tool_registry import ToolRegistry, ToolDefinition, get_registry
```

**After (Core Package):**
```python
from universal_agent_nexus.runtime import ToolRegistry, ToolDefinition, get_registry
```

**Files Affected:**
- `09-autonomous-flow/backend/main.py`
- `09-autonomous-flow/runtime/autonomous_runtime.py`
- Any other files importing from `tools.registry`

---

### Router Patterns

**Before (Examples):**
```python
from _lib.patterns.universal_agent_tools import RouteDefinition, build_decision_agent_manifest
# OR
from tools.universal_agent_tools import RouteDefinition, build_decision_agent_manifest
```

**After (Core Package):**
```python
from universal_agent_tools.patterns import RouteDefinition, build_decision_agent_manifest
```

**Files Affected:**
- `11-n-decision-router/generate_manifest.py`
- `12-self-modifying-agent/generate_manifest.py`
- `13-practical-quickstart/generate_manifest.py`

---

### Scaffolding

**Before (Examples):**
```python
from _lib.patterns.universal_agent_tools import (
    OrganizationAgentFactory,
    build_organization_manifest
)
```

**After (Core Package):**
```python
from universal_agent_tools.patterns import (
    OrganizationAgentFactory,
    build_organization_manifest
)
```

**Files Affected:**
- `10-local-llm-tool-servers/organization_agent.py` (if applicable)

---

### Enrichment

**Before (Examples):**
```python
from _lib.patterns.universal_agent_tools import (
    TenantIsolationHandler,
    VectorDBIsolationHandler,
    create_tenant_agent
)
```

**After (Core Package):**
```python
from universal_agent_tools.patterns import (
    TenantIsolationHandler,
    VectorDBIsolationHandler,
    create_tenant_agent
)
```

---

### Self-Modifying Agents

**Before (Examples):**
```python
from _lib.patterns.universal_agent_tools import (
    SelfModifyingAgent,
    ExecutionLog,
    deterministic_tool_from_error
)
```

**After (Core Package):**
```python
from universal_agent_tools.patterns import (
    SelfModifyingAgent,
    ExecutionLog,
    deterministic_tool_from_error
)
```

---

## Requirements Updates

### Before
```txt
universal-agent-nexus>=3.0.1
```

### After
```txt
universal-agent-nexus>=3.1.0
universal-agent-tools>=1.1.0
```

---

## Complete Import Map

| Old Import | New Import |
|-----------|-----------|
| `from tools.registry.tool_registry import ...` | `from universal_agent_nexus.runtime import ...` |
| `from _lib.patterns.universal_agent_tools import ...` | `from universal_agent_tools.patterns import ...` |
| `from tools.universal_agent_tools import ...` | `from universal_agent_tools.patterns import ...` |

---

## Migration Steps

### Step 1: Update Package Versions

Update your `requirements.txt` or `pyproject.toml`:

```txt
universal-agent-nexus>=3.1.0
universal-agent-tools>=1.1.0
```

### Step 2: Update Imports

Use find-and-replace or a migration script to update all import statements.

**Find:**
```python
from tools.registry.tool_registry import
```

**Replace:**
```python
from universal_agent_nexus.runtime import
```

**Find:**
```python
from _lib.patterns.universal_agent_tools import
```

**Replace:**
```python
from universal_agent_tools.patterns import
```

### Step 3: Test

Run your examples/tests to ensure everything works:

```bash
# Test each affected example
cd 09-autonomous-flow && python -m pytest
cd 11-n-decision-router && python generate_manifest.py
cd 12-self-modifying-agent && python generate_manifest.py
```

### Step 4: Remove Old Imports

After confirming everything works, you can remove any backward compatibility shims (if they were added).

---

## Backward Compatibility

**Q1 2026:** Deprecation warnings will be shown for old import paths  
**Q2 2026:** Old import paths will be removed

During Q1 2026, you can still use old imports, but you'll see deprecation warnings. Update to new imports as soon as possible.

---

## Common Issues

### Issue: ModuleNotFoundError

**Problem:** `ModuleNotFoundError: No module named 'universal_agent_nexus.runtime'`

**Solution:** 
1. Ensure you've installed `universal-agent-nexus>=3.1.0`
2. Check your Python environment
3. Verify package installation: `pip list | grep universal-agent`

### Issue: Import Path Confusion

**Problem:** Not sure which new import path to use

**Solution:** 
- Tool Registry → `universal_agent_nexus.runtime`
- All patterns → `universal_agent_tools.patterns`

### Issue: Missing Dependencies

**Problem:** `universal-agent-tools` can't find `universal-agent-nexus`

**Solution:** 
- Ensure both packages are installed
- Check that `universal-agent-nexus>=3.1.0` is in your requirements

---

## Examples

### Example 1: Tool Registry Usage

**Before:**
```python
from tools.registry.tool_registry import get_registry

registry = get_registry()
registry.register_server("filesystem", "http://localhost:8000/mcp")
tools = registry.discover_tools()
```

**After:**
```python
from universal_agent_nexus.runtime import get_registry

registry = get_registry()
registry.register_server("filesystem", "http://localhost:8000/mcp")
tools = registry.discover_tools()
```

### Example 2: Router Pattern Usage

**Before:**
```python
from _lib.patterns.universal_agent_tools import RouteDefinition, build_decision_agent_manifest

routes = [
    RouteDefinition(
        name="financial",
        tool_ref="financial_analyzer",
        condition_expression="contains(output, 'financial')"
    ),
]

manifest = build_decision_agent_manifest(
    agent_name="research-director",
    system_message="Classify query intent...",
    llm="local://qwen3",
    routes=routes,
)
```

**After:**
```python
from universal_agent_tools.patterns import RouteDefinition, build_decision_agent_manifest

routes = [
    RouteDefinition(
        name="financial",
        tool_ref="financial_analyzer",
        condition_expression="contains(output, 'financial')"
    ),
]

manifest = build_decision_agent_manifest(
    agent_name="research-director",
    system_message="Classify query intent...",
    llm="local://qwen3",
    routes=routes,
)
```

---

## Need Help?

- Check the [Implementation Plan](./PROMOTION_IMPLEMENTATION_PLAN.md) for detailed steps
- Review the [Promotion Readiness](./_lib/PROMOTION_READINESS.md) document
- Open an issue if you encounter problems

---

**Last Updated:** December 2025  
**Status:** Pre-Release (Q1 2026 Target)

