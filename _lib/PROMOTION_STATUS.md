# _lib Promotion Status

**Date:** December 2025  
**Status:** Patterns Complete, Core Modules Pending

## ✅ Already Promoted (Q1 2026)

### To `universal-agent-tools@1.1.0`
- ✅ `patterns/router_patterns.py` → `universal_agent_tools.patterns.router`
- ✅ `patterns/scaffolding.py` → `universal_agent_tools.patterns.scaffolding`
- ✅ `patterns/enrichment.py` → `universal_agent_tools.patterns.enrichment`
- ✅ `patterns/self_modifying.py` → `universal_agent_tools.patterns.self_modifying`

## 📦 Remaining Modules - Promotion Targets

### → `universal-agent-nexus` (Core Runtime)

| Module | Current Location | Target Location | Priority | Status |
|--------|-----------------|-----------------|----------|--------|
| **Runtime** | `_lib/runtime/` | `universal_agent_nexus.runtime` | HIGH | ⏳ Pending |
| **Cache Fabric** | `_lib/cache_fabric/` | `universal_agent_nexus.cache_fabric` | HIGH | ⏳ Pending |
| **Output Parsers** | `_lib/output_parsers/` | `universal_agent_nexus.output_parsers` | HIGH | ⏳ Pending |

**Why Nexus?** These are core runtime components that are fundamental to the compiler and execution engine.

### → `universal-agent-tools` (Tool Utilities)

| Module | Current Location | Target Location | Priority | Status |
|--------|-----------------|-----------------|----------|--------|
| **Tools** | `_lib/tools/universal_agent_tools/` | `universal_agent_tools.*` | HIGH | ⏳ Pending |
| - `model_config.py` | | `universal_agent_tools.model_config` | | |
| - `observability_helper.py` | | `universal_agent_tools.observability` | | |
| - `ollama_tools.py` | | `universal_agent_tools.ollama_tools` | | |

**Why Tools?** These are utility modules for working with tools, models, and observability - not core compiler functionality.

### → `universal-agent-tools` (Q2 2026 - Lower Priority)

| Module | Current Location | Target Location | Priority | Status |
|--------|-----------------|-----------------|----------|--------|
| **Dynamic Tools** | `_lib/patterns/dynamic_tools.py` | `universal_agent_tools.patterns.dynamic` | MEDIUM | ⏳ Q2 2026 |
| **MCP Stub** | `_lib/patterns/mcp_stub.py` | `universal_agent_tools.testing.mcp_stub` | MEDIUM | ⏳ Q2 2026 |

**Why Later?** These are specialized/testing utilities, less critical than core patterns.

## 📋 Summary

### To `universal-agent-nexus` (3 modules)
1. ✅ **Runtime** (`_lib/runtime/`) - Core runtime abstractions
2. ✅ **Cache Fabric** (`_lib/cache_fabric/`) - Caching layer
3. ✅ **Output Parsers** (`_lib/output_parsers/`) - Output parsing utilities

### To `universal-agent-tools` (3-5 modules)
1. ✅ **Tools** (`_lib/tools/universal_agent_tools/`) - Tool utilities
2. ⏳ **Dynamic Tools** (`_lib/patterns/dynamic_tools.py`) - Q2 2026
3. ⏳ **MCP Stub** (`_lib/patterns/mcp_stub.py`) - Q2 2026

## 🎯 Answer: Mostly Yes!

**Yes, everything left in `_lib` should be promoted, but:**

- **3 modules** → `universal-agent-nexus` (core runtime)
- **1 module** → `universal-agent-tools` (tool utilities)  
- **2 modules** → `universal-agent-tools` (Q2 2026, lower priority)

The distinction:
- **Nexus** = Core compiler/runtime functionality
- **Tools** = Utilities and helper libraries

## 🚀 Next Steps

### Immediate (Q1 2026)
1. Promote `runtime/`, `cache_fabric/`, `output_parsers/` to `universal-agent-nexus@3.1.0`
2. Promote `tools/universal_agent_tools/` to `universal-agent-tools@1.2.0`

### Q2 2026
3. Promote `dynamic_tools.py` and `mcp_stub.py` to `universal-agent-tools@1.3.0`

## 📝 Current State

```
_lib/
├── runtime/          → universal-agent-nexus.runtime          [PENDING]
├── cache_fabric/     → universal-agent-nexus.cache_fabric     [PENDING]
├── output_parsers/   → universal-agent-nexus.output_parsers   [PENDING]
├── tools/            → universal-agent-tools.*                [PENDING]
└── patterns/         → universal-agent-tools.patterns         [✅ DONE]
    ├── router_patterns.py      [✅ PROMOTED]
    ├── scaffolding.py           [✅ PROMOTED]
    ├── enrichment.py            [✅ PROMOTED]
    ├── self_modifying.py       [✅ PROMOTED]
    ├── dynamic_tools.py         [⏳ Q2 2026]
    └── mcp_stub.py             [⏳ Q2 2026]
```

---

**Bottom Line:** Yes, everything in `_lib` should be promoted. The patterns are done. The remaining modules are core runtime (→ nexus) and utilities (→ tools).

