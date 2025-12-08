# Promotion Readiness Analysis

**Date:** December 2025  
**Status:** Ready for Q1 2026 Promotion

## Executive Summary

Abstractions in `_lib/` and `tools/` are **production-ready patterns**, not examples. They should be promoted to core libraries once validated.

## Promotion Priority Matrix

| Module | Current Location | Target Package | Readiness | Q1 2026 | Q2 2026 | Status |
|--------|-----------------|----------------|-----------|---------|---------|--------|
| **Tool Registry** | `tools/registry/tool_registry.py` | `universal-agent-nexus.runtime` | ✅ HIGH | ✅ YES | — | **TIER 1** |
| **Router Patterns** | `_lib/patterns/router_patterns.py` | `universal-agent-tools.patterns` | ✅ HIGH | ✅ YES | — | **TIER 2** |
| **Scaffolding** | `_lib/patterns/scaffolding.py` | `universal-agent-tools.patterns` | ✅ HIGH | ✅ YES | — | **TIER 2** |
| **Enrichment** | `_lib/patterns/enrichment.py` | `universal-agent-tools.patterns` | ✅ HIGH | ✅ YES | — | **TIER 2** |
| **Self-Modifying** | `_lib/patterns/self_modifying.py` | `universal-agent-tools.patterns` | ✅ MEDIUM | ✅ YES | — | **TIER 2** |
| **Dynamic Tools** | `_lib/patterns/dynamic_tools.py` | `universal-agent-tools.patterns` | ✅ MEDIUM | — | ✅ YES | **TIER 3** |
| **MCP Stub** | `_lib/patterns/mcp_stub.py` | `universal-agent-tools.testing` | ✅ MEDIUM | — | ✅ YES | **TIER 3** |

## TIER 1: Core Runtime (universal-agent-nexus)

### Tool Registry → `universal-agent-nexus.runtime.registry`

**Location:** `tools/registry/tool_registry.py`

**Why Promote:**
- ✅ Core abstraction for tool discovery in runtime
- ✅ Used by examples 08, 09, 10, 11, 12
- ✅ Generic, runtime-agnostic
- ✅ Fully self-contained
- ✅ Essential for dynamic tool integration

**Target:**
```python
from universal_agent_nexus.runtime.registry import ToolRegistry, ToolDefinition
```

**Blockers:**
- [ ] Add unit tests (>70% coverage)
- [ ] Add type hints
- [ ] Update documentation

**ETA:** Q1 2026 (universal-agent-nexus@3.1.0)

## TIER 2: Advanced Patterns (universal-agent-tools)

### Router Patterns → `universal-agent-tools.patterns.router`

**Location:** `_lib/patterns/universal_agent_tools/router_patterns.py`

**Why Promote:**
- ✅ Stable API (used by examples 11, 12)
- ✅ Highly reusable (core pattern for N-decision routers)
- ✅ Production-ready (no TODOs)

**Target:**
```python
from universal_agent_tools.patterns import RouteDefinition, build_decision_agent_manifest
```

**Blockers:**
- [ ] Add unit tests
- [ ] Document dependency on universal-agent-nexus IR

**ETA:** Q1 2026 (universal-agent-tools@1.1.0)

### Scaffolding → `universal-agent-tools.patterns.scaffolding`

**Location:** `_lib/patterns/universal_agent_tools/scaffolding.py`

**Why Promote:**
- ✅ Stable (used by examples 10, 12)
- ✅ Well-tested (complex nested graph building)
- ✅ Clear documentation

**Target:**
```python
from universal_agent_tools.patterns import OrganizationAgentFactory, build_organization_manifest
```

**ETA:** Q1 2026 (universal-agent-tools@1.1.0)

### Enrichment → `universal-agent-tools.patterns.enrichment`

**Location:** `_lib/patterns/universal_agent_tools/enrichment.py`

**Why Promote:**
- ✅ Stable (used by example 10)
- ✅ Clear tenant abstraction
- ✅ Complements scaffolding

**Target:**
```python
from universal_agent_tools.patterns import TenantEnrichmentHandler, create_tenant_agent
```

**ETA:** Q1 2026 (universal-agent-tools@1.1.0)

### Self-Modifying → `universal-agent-tools.patterns.self_modifying`

**Location:** `_lib/patterns/universal_agent_tools/self_modifying.py`

**Why Promote:**
- ✅ Stable (used by example 12)
- ✅ Unique pattern (self-healing agents)
- ✅ Production-ready

**Target:**
```python
from universal_agent_tools.patterns import SelfModifyingAgent, deterministic_tool_from_error
```

**ETA:** Q1 2026 (universal-agent-tools@1.1.0)

## TIER 3: Utilities (Q2 2026)

### Dynamic Tools → `universal-agent-tools.patterns.dynamic`

**Location:** `_lib/patterns/universal_agent_tools/dynamic_tools.py`

**Why Later:**
- ✅ Useful but specialized (CSV tool injection)
- ✅ Less widely used than routing/scaffolding
- ✅ Can wait for Q2 once core patterns are stable

**ETA:** Q2 2026

### MCP Stub → `universal-agent-tools.testing.mcp_stub`

**Location:** `_lib/patterns/universal_agent_tools/mcp_stub.py`

**Why Later:**
- ✅ Useful for demos/testing
- ✅ Not production code
- ✅ Niche use case (local development)

**ETA:** Q2 2026

## Keep in Examples (Don't Promote)

| Module | Reason |
|--------|--------|
| `tools/standard_template.py` | Example boilerplate, not library code |
| `tools/example_runner.py` | Test/dev infrastructure specific to examples |
| `tools/mcp_servers/*` | Example implementations, not libraries |
| `tools/*.md` | Documentation, move alongside code promotion |

## Q1 2026 Promotion Bundle

### Package: `universal-agent-nexus@3.1.0`

**New Module:**
```python
# Tool discovery at runtime
from universal_agent_nexus.runtime.registry import ToolRegistry, ToolDefinition
```

### Package: `universal-agent-tools@1.1.0`

**New Module:**
```python
# Advanced patterns
from universal_agent_tools.patterns import (
    RouteDefinition,
    build_decision_agent_manifest,
    build_organization_manifest,
    create_tenant_agent,
    SelfModifyingAgent,
    deterministic_tool_from_error,
    TenantEnrichmentHandler,
)
```

## Migration Path

### Pre-Promotion (Current)
```python
from tools.registry import ToolRegistry
from _lib.patterns.universal_agent_tools import RouteDefinition
```

### Post-Promotion (Q1 2026)
```python
from universal_agent_nexus.runtime.registry import ToolRegistry
from universal_agent_tools.patterns import RouteDefinition
```

## Blocking Issues

### Issue 1: Dependency Direction
**Current:** `_lib/patterns/*` depends on `universal_agent_nexus.ir`

**Solution:** Accept natural dependency
- `universal-agent-tools` → `universal-agent-nexus` (IR types)
- This is natural and expected

### Issue 2: Test Coverage
**Current:** Missing unit tests for promoted modules

**Requirement:** >70% coverage before promotion

**Action:** Add tests in Q1 2026 before promotion

### Issue 3: Version Coordination
**Current:** Examples pin `universal-agent-nexus>=3.0.1`

**Solution:**
- Promotion happens in `universal-agent-nexus@3.1.0`
- Update examples to require `>=3.1.0`
- Document in `PROMOTION_GUIDE.md`

## Implementation Checklist

For each module being promoted:

- [ ] Extract to target package structure
- [ ] Add unit tests (>70% coverage)
- [ ] Add type hints (if missing)
- [ ] Update documentation/docstrings
- [ ] Create deprecation notice in examples/
- [ ] Update all example imports
- [ ] Pin dependencies in target package
- [ ] Create migration guide
- [ ] Update `PROMOTION_GUIDE.md`

## Benefits

### For Users
- ✅ Patterns available in stable packages
- ✅ Clear versioning and SemVer guarantees
- ✅ Better documentation in official packages
- ✅ Don't need to clone examples to use patterns

### For Core Teams
- ✅ Validated patterns proven at scale
- ✅ Reduced maintenance (patterns in core, examples clean)
- ✅ Easier to evolve core without breaking examples

### For Ecosystem
- ✅ Examples stay focused on "how to use"
- ✅ Toolkit packages become richer
- ✅ Clear separation: learning (examples) vs. building (packages)

