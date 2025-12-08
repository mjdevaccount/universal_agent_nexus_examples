# Promotion Guide: Experimental Abstractions

## Overview

Abstractions in `_lib/` are **interim implementations** being validated through examples before promotion to production packages.

## Structure

```
_lib/
├── runtime/          → universal-agent-nexus
├── cache_fabric/     → universal-agent-nexus
├── output_parsers/   → universal-agent-nexus
├── tools/            → universal-agent-tools
└── patterns/         → universal-agent-tools
```

## Promotion Process

### Phase 1: Validation (Current)
- ✅ Used by examples
- ✅ API tested in real scenarios
- ✅ Patterns documented

### Phase 2: Stabilization
- [ ] API finalized
- [ ] Tests added
- [ ] Documentation complete
- [ ] Versioning strategy defined

### Phase 3: Promotion
1. **Create/Update Target Package**
   - Add modules to `universal-agent-nexus` or `universal-agent-tools`
   - Follow package structure conventions
   - Add proper package metadata

2. **Update Examples**
   - Change imports from `_lib` to package name
   - Update requirements.txt
   - Test all examples

3. **Remove from _lib/**
   - Delete promoted modules
   - Update documentation
   - Remove backward compatibility shims

## Import Migration

### Current (Interim)
```python
from _lib.runtime import NexusRuntime
from _lib.cache_fabric import create_cache_fabric
from _lib.tools import ModelConfig
```

### After Promotion
```python
from universal_agent_nexus.runtime import NexusRuntime
from universal_agent_nexus.cache_fabric import create_cache_fabric
from universal_agent_tools import ModelConfig
```

## Status Tracking

| Module | Status | Target | ETA |
|--------|--------|--------|-----|
| `runtime/` | ✅ Validated | `universal-agent-nexus` | Q1 2026 |
| `cache_fabric/` | ✅ Validated | `universal-agent-nexus` | Q1 2026 |
| `output_parsers/` | ✅ Validated | `universal-agent-nexus` | Q1 2026 |
| `tools/` | ✅ Validated | `universal-agent-tools` | Q1 2026 |
| `patterns/` | 🔄 In Progress | `universal-agent-tools` | Q2 2026 |

## Conventions

1. **`_lib/` prefix** - Underscore indicates "internal/temporary"
2. **Clear documentation** - Each module documents its promotion target
3. **Backward compatibility** - `shared/` redirects to `_lib/` during transition
4. **Version tracking** - Status table tracks promotion progress

