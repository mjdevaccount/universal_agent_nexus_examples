# Promotion Implementation Plan: Q1 2026

**Date:** December 2025  
**Status:** Ready for Implementation  
**Target:** Q1 2026 Release

## Executive Summary

This document provides a step-by-step implementation plan for promoting validated patterns from `tools/` and `_lib/patterns/` into core libraries (`universal-agent-nexus` and `universal-agent-tools`).

## Promotion Targets

### TIER 1: Core Runtime → `universal-agent-nexus@3.1.0`

| Module | Current Location | Target Location | Priority |
|--------|-----------------|-----------------|----------|
| `ToolRegistry` | `tools/registry/tool_registry.py` | `universal_agent_nexus.runtime.registry` | **HIGH** |

### TIER 2: Advanced Patterns → `universal-agent-tools@1.1.0`

| Module | Current Location | Target Location | Priority |
|--------|-----------------|-----------------|----------|
| `router_patterns` | `_lib/patterns/universal_agent_tools/router_patterns.py` | `universal_agent_tools.patterns.router` | **HIGH** |
| `scaffolding` | `_lib/patterns/universal_agent_tools/scaffolding.py` | `universal_agent_tools.patterns.scaffolding` | **HIGH** |
| `enrichment` | `_lib/patterns/universal_agent_tools/enrichment.py` | `universal_agent_tools.patterns.enrichment` | **HIGH** |
| `self_modifying` | `_lib/patterns/universal_agent_tools/self_modifying.py` | `universal_agent_tools.patterns.self_modifying` | **MEDIUM** |

## Phase 1: Pre-Promotion Validation

### 1.1 Code Quality Checks

- [ ] **Type Hints**: Ensure all promoted modules have complete type hints
  - [ ] `tool_registry.py` - ✅ Already has type hints
  - [ ] `router_patterns.py` - ✅ Already has type hints
  - [ ] `scaffolding.py` - ✅ Already has type hints
  - [ ] `enrichment.py` - ⚠️ Check for missing hints
  - [ ] `self_modifying.py` - ✅ Already has type hints

- [ ] **Documentation**: Review and enhance docstrings
  - [ ] All public classes/functions have docstrings
  - [ ] Examples in docstrings are accurate
  - [ ] Parameter descriptions are complete

- [ ] **Dependencies**: Audit external dependencies
  - [ ] `tool_registry.py`: `httpx`, `pydantic` ✅
  - [ ] `router_patterns.py`: `universal_agent_nexus.ir` ✅
  - [ ] `scaffolding.py`: `universal_agent_nexus.builder`, `universal_agent_nexus.ir` ✅
  - [ ] `enrichment.py`: `universal_agent_nexus.enrichment` ⚠️ Check if this exists
  - [ ] `self_modifying.py`: `universal_agent_nexus.compiler`, `universal_agent_nexus.ir` ✅

### 1.2 Test Coverage

**Target: >70% coverage for all promoted modules**

- [ ] **ToolRegistry Tests**
  - [ ] Test `register_server()`
  - [ ] Test `discover_tools()` with mock MCP server
  - [ ] Test `discover_tools()` with invalid server
  - [ ] Test `get_tool()` (found and not found)
  - [ ] Test `list_tools()` and `list_servers()`
  - [ ] Test singleton pattern (`get_registry()`)

- [ ] **Router Patterns Tests**
  - [ ] Test `RouteDefinition` dataclass
  - [ ] Test `build_decision_agent_manifest()` with 1 route
  - [ ] Test `build_decision_agent_manifest()` with N routes
  - [ ] Test edge creation and routing logic
  - [ ] Test formatter node creation

- [ ] **Scaffolding Tests**
  - [ ] Test `create_team_agent()`
  - [ ] Test `create_organization_manifest()`
  - [ ] Test graph structure and connections
  - [ ] Test tool definitions

- [ ] **Enrichment Tests**
  - [ ] Test `TenantIsolationHandler.handle()`
  - [ ] Test `VectorDBIsolationHandler.handle()`
  - [ ] Test `create_tenant_agent()` integration

- [ ] **Self-Modifying Tests**
  - [ ] Test `SelfModifyingAgent.analyze_and_generate_tool()`
  - [ ] Test `SelfModifyingAgent.register_generated_tool()`
  - [ ] Test `deterministic_tool_from_error()`
  - [ ] Test tool injection into manifest

### 1.3 Dependency Resolution

- [ ] **Verify `universal-agent-nexus` dependency**
  - [ ] Confirm `universal_agent_nexus.ir` module exists
  - [ ] Confirm `universal_agent_nexus.compiler` module exists
  - [ ] Confirm `universal_agent_nexus.builder` module exists
  - [ ] ⚠️ Check if `universal_agent_nexus.enrichment` exists (used by enrichment.py)

- [ ] **Update `universal-agent-tools` dependencies**
  - [ ] Add `universal-agent-nexus>=3.1.0` to `setup.py`
  - [ ] Update `requirements.txt`

## Phase 2: Package Structure Setup

### 2.1 Universal-Agent-Nexus Structure

**Target:** `universal-agent-nexus@3.1.0`

```
universal_agent_nexus/
├── runtime/
│   ├── __init__.py
│   └── registry/
│       ├── __init__.py
│       ├── tool_registry.py      # Promoted from tools/registry/
│       └── models.py             # ToolDefinition (if separate)
```

**Actions:**
- [ ] Create `runtime/registry/` directory structure
- [ ] Copy `tool_registry.py` to `runtime/registry/`
- [ ] Update imports in `tool_registry.py` (if needed)
- [ ] Create `runtime/registry/__init__.py` with exports:
  ```python
  from .tool_registry import ToolRegistry, get_registry
  from .models import ToolDefinition  # if separated
  ```
- [ ] Update `runtime/__init__.py` to export registry:
  ```python
  from .registry import ToolRegistry, ToolDefinition, get_registry
  ```

### 2.2 Universal-Agent-Tools Structure

**Target:** `universal-agent-tools@1.1.0`

```
universal_agent_tools/
├── patterns/
│   ├── __init__.py
│   ├── router.py                 # Promoted from _lib/patterns/.../router_patterns.py
│   ├── scaffolding.py            # Promoted from _lib/patterns/.../scaffolding.py
│   ├── enrichment.py             # Promoted from _lib/patterns/.../enrichment.py
│   └── self_modifying.py         # Promoted from _lib/patterns/.../self_modifying.py
```

**Actions:**
- [ ] Create `patterns/` directory in `universal_agent_tools/`
- [ ] Copy all pattern modules to `patterns/`
- [ ] Rename `router_patterns.py` → `router.py`
- [ ] Update imports in each module:
  - [ ] `router.py`: Update internal imports
  - [ ] `scaffolding.py`: Update internal imports
  - [ ] `enrichment.py`: Update internal imports
  - [ ] `self_modifying.py`: Update internal imports
- [ ] Create `patterns/__init__.py` with exports:
  ```python
  from .router import RouteDefinition, build_decision_agent_manifest
  from .scaffolding import OrganizationAgentFactory, build_organization_manifest
  from .enrichment import TenantIsolationHandler, VectorDBIsolationHandler, create_tenant_agent
  from .self_modifying import SelfModifyingAgent, ExecutionLog, deterministic_tool_from_error
  ```
- [ ] Update `universal_agent_tools/__init__.py` to export patterns:
  ```python
  from .patterns import (
      RouteDefinition,
      build_decision_agent_manifest,
      # ... etc
  )
  ```

## Phase 3: Code Migration

### 3.1 ToolRegistry Migration

**Source:** `universal_agent_nexus_examples/tools/registry/tool_registry.py`  
**Target:** `universal_agent_nexus/runtime/registry/tool_registry.py`

**Steps:**
1. [ ] Copy file to target location
2. [ ] Update module docstring to reflect new location
3. [ ] Ensure `ToolDefinition` is either:
   - In same file, OR
   - Moved to `models.py` and imported
4. [ ] Update any internal imports
5. [ ] Add version info to docstring
6. [ ] Run tests to verify functionality

### 3.2 Pattern Modules Migration

**Source:** `universal_agent_nexus_examples/_lib/patterns/universal_agent_tools/*.py`  
**Target:** `universal_agent_tools/patterns/*.py`

**Steps for each module:**
1. [ ] Copy file to target location
2. [ ] Update module docstring
3. [ ] Update imports:
   - [ ] Change `from universal_agent_nexus.ir import ...` (should work as-is)
   - [ ] Update any relative imports
4. [ ] Rename `router_patterns.py` → `router.py`
5. [ ] Update `__all__` exports if present
6. [ ] Add version info
7. [ ] Run tests

### 3.3 Dependency Updates

- [ ] **Update `universal-agent-tools/setup.py`**
  ```python
  install_requires=[
      "universal-agent-nexus>=3.1.0",  # Add this
      # ... existing dependencies
  ]
  ```

- [ ] **Update `universal-agent-nexus/setup.py`** (if exists)
  - [ ] Ensure `httpx` and `pydantic` are in dependencies

## Phase 4: Example Migration

### 4.1 Update All Example Imports

**Files to update:**

- [ ] `09-autonomous-flow/backend/main.py`
  ```python
  # OLD
  from tools.registry.tool_registry import get_registry
  
  # NEW
  from universal_agent_nexus.runtime import get_registry
  ```

- [ ] `09-autonomous-flow/runtime/autonomous_runtime.py`
  ```python
  # OLD
  from tools.registry.tool_registry import get_registry
  
  # NEW
  from universal_agent_nexus.runtime import get_registry
  ```

- [ ] `11-n-decision-router/generate_manifest.py`
  ```python
  # OLD
  from tools.universal_agent_tools import RouteDefinition, build_decision_agent_manifest
  
  # NEW
  from universal_agent_tools.patterns import RouteDefinition, build_decision_agent_manifest
  ```

- [ ] `12-self-modifying-agent/generate_manifest.py`
  ```python
  # OLD
  from tools.universal_agent_tools import RouteDefinition, build_decision_agent_manifest
  
  # NEW
  from universal_agent_tools.patterns import RouteDefinition, build_decision_agent_manifest
  ```

- [ ] `13-practical-quickstart/generate_manifest.py`
  ```python
  # OLD
  from tools.universal_agent_tools import RouteDefinition, build_decision_agent_manifest
  
  # NEW
  from universal_agent_tools.patterns import RouteDefinition, build_decision_agent_manifest
  ```

- [ ] `10-local-llm-tool-servers/organization_agent.py` (if uses scaffolding)
  ```python
  # OLD
  from _lib.patterns.universal_agent_tools import build_organization_manifest
  
  # NEW
  from universal_agent_tools.patterns import build_organization_manifest
  ```

### 4.2 Update Requirements Files

- [ ] Update all example `requirements.txt` files:
  ```txt
  universal-agent-nexus>=3.1.0
  universal-agent-tools>=1.1.0
  ```

- [ ] Update `requirements-consolidated.txt` if it exists

### 4.3 Backward Compatibility (Optional)

**Option A: Deprecation Warnings**
- [ ] Create shim modules in `tools/registry/`:
  ```python
  # tools/registry/tool_registry.py
  import warnings
  warnings.warn(
      "tools.registry is deprecated. Use universal_agent_nexus.runtime instead.",
      DeprecationWarning,
      stacklevel=2
  )
  from universal_agent_nexus.runtime import ToolRegistry, ToolDefinition, get_registry
  ```

- [ ] Create shim in `_lib/patterns/universal_agent_tools/`:
  ```python
  # _lib/patterns/universal_agent_tools/router_patterns.py
  import warnings
  warnings.warn(
      "_lib.patterns is deprecated. Use universal_agent_tools.patterns instead.",
      DeprecationWarning,
      stacklevel=2
  )
  from universal_agent_tools.patterns import RouteDefinition, build_decision_agent_manifest
  ```

**Option B: Remove Immediately**
- [ ] Delete old files after migration
- [ ] Update all imports (no shims)

**Recommendation:** Use Option A for Q1 2026, remove shims in Q2 2026.

## Phase 5: Documentation Updates

### 5.1 Package Documentation

- [ ] **Update `universal-agent-nexus` README**
  - [ ] Add `runtime.registry` section
  - [ ] Add usage examples for `ToolRegistry`
  - [ ] Update API reference

- [ ] **Update `universal-agent-tools` README**
  - [ ] Add `patterns` section
  - [ ] Document all pattern modules
  - [ ] Add usage examples for each pattern
  - [ ] Update API reference

### 5.2 Example Documentation

- [ ] Update `API_REFERENCE.md` in examples
  - [ ] Update import paths
  - [ ] Update code examples

- [ ] Update `PROMOTION_GUIDE.md`
  - [ ] Mark promoted modules as complete
  - [ ] Update status table

- [ ] Update example READMEs
  - [ ] `11-n-decision-router/README.md`
  - [ ] `12-self-modifying-agent/README.md`
  - [ ] `09-autonomous-flow/README.md`

### 5.3 Migration Guide

- [ ] Create `MIGRATION_GUIDE_Q1_2026.md`
  - [ ] List all import changes
  - [ ] Provide before/after examples
  - [ ] Document breaking changes (if any)
  - [ ] Provide migration script (optional)

## Phase 6: Testing & Validation

### 6.1 Unit Tests

- [ ] Run all new unit tests
- [ ] Achieve >70% coverage for all promoted modules
- [ ] Fix any failing tests

### 6.2 Integration Tests

- [ ] Test all examples with new imports
- [ ] Verify examples 08, 09, 10, 11, 12 work correctly
- [ ] Test backward compatibility shims (if implemented)

### 6.3 Package Installation Tests

- [ ] Test installing `universal-agent-nexus@3.1.0`
- [ ] Test installing `universal-agent-tools@1.1.0`
- [ ] Verify dependencies resolve correctly
- [ ] Test import paths work as expected

## Phase 7: Release Preparation

### 7.1 Version Bumping

- [ ] Update `universal-agent-nexus` to `3.1.0`
  - [ ] Update `setup.py` or `pyproject.toml`
  - [ ] Update `__version__` in package
  - [ ] Create changelog entry

- [ ] Update `universal-agent-tools` to `1.1.0`
  - [ ] Update `setup.py`
  - [ ] Update `__version__` in package
  - [ ] Create changelog entry

### 7.2 Release Notes

- [ ] Create release notes for `universal-agent-nexus@3.1.0`
  - [ ] Document `ToolRegistry` addition
  - [ ] List breaking changes (if any)
  - [ ] Migration guide link

- [ ] Create release notes for `universal-agent-tools@1.1.0`
  - [ ] Document new `patterns` module
  - [ ] List all promoted patterns
  - [ ] Migration guide link

### 7.3 Communication

- [ ] Update main project README
- [ ] Announce promotion in project communication channels
- [ ] Update documentation site (if applicable)

## Phase 8: Post-Release Cleanup

### 8.1 Remove Deprecated Code

**After Q1 2026 (or Q2 if using deprecation warnings):**

- [ ] Remove shim modules from `tools/registry/`
- [ ] Remove shim modules from `_lib/patterns/`
- [ ] Update `PROMOTION_READINESS.md` to mark as complete
- [ ] Archive old code (optional)

### 8.2 Final Validation

- [ ] All examples work with new imports
- [ ] No references to old import paths remain
- [ ] Documentation is up to date
- [ ] Tests pass in CI/CD

## Implementation Timeline

### Week 1-2: Pre-Promotion Validation
- Complete Phase 1 (Code Quality, Tests, Dependencies)

### Week 3: Package Structure Setup
- Complete Phase 2 (Create package structures)

### Week 4: Code Migration
- Complete Phase 3 (Move code, update imports)

### Week 5: Example Migration
- Complete Phase 4 (Update all examples)

### Week 6: Documentation
- Complete Phase 5 (Update all docs)

### Week 7: Testing
- Complete Phase 6 (All tests pass)

### Week 8: Release
- Complete Phase 7 (Release packages)
- Complete Phase 8 (Post-release cleanup)

## Risk Mitigation

### Risk 1: Breaking Changes
**Mitigation:** Use deprecation warnings for Q1, remove in Q2

### Risk 2: Missing Dependencies
**Mitigation:** Audit all dependencies in Phase 1.1

### Risk 3: Test Coverage Gaps
**Mitigation:** Require >70% coverage before promotion

### Risk 4: Import Path Confusion
**Mitigation:** Clear migration guide, backward compatibility shims

## Success Criteria

✅ All promoted modules have >70% test coverage  
✅ All examples work with new import paths  
✅ Documentation is complete and accurate  
✅ Packages install and import correctly  
✅ No breaking changes (or clearly documented)  
✅ Migration guide is available  
✅ Release notes are published  

## Next Steps

1. **Review this plan** with team
2. **Assign owners** for each phase
3. **Set up tracking** (GitHub issues, project board, etc.)
4. **Begin Phase 1** (Pre-Promotion Validation)

---

**Questions or Issues?**  
Update this document as implementation progresses. Track blockers and decisions here.

