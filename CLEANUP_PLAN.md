# Code Cleanup Plan: Post v3.1.0 Release

**Date:** December 2025  
**Status:** Ready for Cleanup  
**Prerequisite:** Update all examples to use new imports first

## ✅ Safe to Delete (After Examples Updated)

### 1. Promoted Runtime Modules → `universal-agent-nexus@3.1.0`
- ✅ `_lib/runtime/` - **DELETE** (promoted to nexus)
  - `runtime_base.py` → `universal_agent_nexus.runtime.runtime_base`
  - `standard_integration.py` → `universal_agent_nexus.runtime.standard_integration`

### 2. Promoted Cache Fabric → `universal-agent-nexus@3.1.0`
- ✅ `_lib/cache_fabric/` - **DELETE** (promoted to nexus)
  - Complete module → `universal_agent_nexus.cache_fabric`

### 3. Promoted Output Parsers → `universal-agent-nexus@3.1.0`
- ✅ `_lib/output_parsers/` - **DELETE** (promoted to nexus)
  - Complete module → `universal_agent_nexus.output_parsers`

### 4. Promoted Tools → `universal-agent-tools@1.1.0`
- ✅ `_lib/tools/universal_agent_tools/` - **DELETE** (promoted to tools)
  - `model_config.py` → `universal_agent_tools.model_config`
  - `observability_helper.py` → `universal_agent_tools.observability`
  - `ollama_tools.py` → `universal_agent_tools.ollama_tools`

### 5. Promoted Patterns → `universal-agent-tools@1.1.0`
- ✅ `_lib/patterns/universal_agent_tools/router_patterns.py` - **DELETE** (shim only)
- ✅ `_lib/patterns/universal_agent_tools/scaffolding.py` - **DELETE** (promoted)
- ✅ `_lib/patterns/universal_agent_tools/enrichment.py` - **DELETE** (promoted)
- ✅ `_lib/patterns/universal_agent_tools/self_modifying.py` - **DELETE** (promoted)
- ✅ `_lib/patterns/universal_agent_tools/test_*.py` - **DELETE** (tests moved)

### 6. Backward Compatibility Shims (Keep until Q2 2026)
- ⏸️ `tools/registry/tool_registry.py` - **KEEP** (shim with deprecation warning)
- ⏸️ `tools/universal_agent_tools.py` - **KEEP** (shim with deprecation warning)
- ⏸️ `shared/` - **KEEP** (redirects to `_lib/`)

## ⚠️ Keep (Not Promoted)

### Modules Still in Use
- ✅ `_lib/patterns/universal_agent_tools/dynamic_tools.py` - **KEEP** (not promoted)
- ✅ `_lib/patterns/universal_agent_tools/mcp_stub.py` - **KEEP** (not promoted)
- ✅ `_lib/patterns/universal_agent_tools/README.md` - **KEEP** (documentation)

## 📋 Pre-Cleanup Checklist

Before deleting, ensure:

1. ✅ **v3.1.0 Released** - universal-agent-nexus@3.1.0 is on PyPI
2. ⏳ **Update Examples** - All examples use new imports:
   ```python
   # OLD → NEW
   from _lib.runtime import NexusRuntime
   → from universal_agent_nexus.runtime import NexusRuntime
   
   from _lib.cache_fabric import create_cache_fabric
   → from universal_agent_nexus.cache_fabric import create_cache_fabric
   
   from _lib.output_parsers import get_parser
   → from universal_agent_nexus.output_parsers import get_parser
   
   from _lib.tools.universal_agent_tools.observability_helper import setup_observability
   → from universal_agent_tools.observability import setup_observability
   
   from tools.registry.tool_registry import get_registry
   → from universal_agent_nexus.runtime import get_registry
   ```
3. ⏳ **Test All Examples** - Verify all examples work with new imports
4. ⏳ **Update Documentation** - Update any docs referencing old paths

## 🗑️ Deletion Commands

Once examples are updated:

```powershell
# Delete promoted runtime
Remove-Item -Recurse -Force "universal_agent_nexus_examples\_lib\runtime"

# Delete promoted cache_fabric
Remove-Item -Recurse -Force "universal_agent_nexus_examples\_lib\cache_fabric"

# Delete promoted output_parsers
Remove-Item -Recurse -Force "universal_agent_nexus_examples\_lib\output_parsers"

# Delete promoted tools
Remove-Item -Recurse -Force "universal_agent_nexus_examples\_lib\tools"

# Delete promoted patterns (keep dynamic_tools.py and mcp_stub.py)
Remove-Item -Force "universal_agent_nexus_examples\_lib\patterns\universal_agent_tools\router_patterns.py"
Remove-Item -Force "universal_agent_nexus_examples\_lib\patterns\universal_agent_tools\scaffolding.py"
Remove-Item -Force "universal_agent_nexus_examples\_lib\patterns\universal_agent_tools\enrichment.py"
Remove-Item -Force "universal_agent_nexus_examples\_lib\patterns\universal_agent_tools\self_modifying.py"
Remove-Item -Force "universal_agent_nexus_examples\_lib\patterns\universal_agent_tools\test_*.py"
```

## 📊 Impact Summary

| Category | Files to Delete | Lines Saved | Status |
|----------|----------------|------------|--------|
| Runtime | 2 files | ~500 | ⏳ Pending |
| Cache Fabric | 10 files | ~1,500 | ⏳ Pending |
| Output Parsers | 7 files | ~800 | ⏳ Pending |
| Tools | 3 files | ~400 | ⏳ Pending |
| Patterns | 6 files | ~1,200 | ⏳ Pending |
| **Total** | **28 files** | **~4,400 lines** | ⏳ Pending |

## 🎯 Next Steps

1. **Update Examples** (Priority 1)
   - Update all `from _lib.` imports
   - Update all `from tools.` imports
   - Test each example

2. **Delete Promoted Modules** (Priority 2)
   - Run deletion commands above
   - Update `_lib/__init__.py` to remove exports

3. **Update Documentation** (Priority 3)
   - Update README files
   - Update migration guides
   - Remove references to `_lib/` paths

4. **Q2 2026: Remove Shims**
   - Delete `tools/registry/tool_registry.py` shim
   - Delete `tools/universal_agent_tools.py` shim
   - Delete `shared/` directory

---

**Status:** ⏳ Waiting for example updates before deletion

