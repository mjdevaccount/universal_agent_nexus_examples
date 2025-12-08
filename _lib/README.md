# Experimental Abstractions Library

**⚠️ INTERIM LOCATION - TO BE PROMOTED**

This directory contains abstractions and utilities that are being validated through examples before promotion to the main `universal-agent-nexus` package or other production packages.

## Purpose

These modules serve as **proof-of-concept** implementations that:
1. Demonstrate patterns through working examples
2. Validate API design and usability
3. Will be promoted once patterns are proven stable

## Structure

```
_lib/
├── runtime/          # Runtime abstractions (→ universal-agent-nexus)
│   ├── runtime_base.py
│   └── standard_integration.py
├── cache_fabric/     # Cache Fabric layer (→ universal-agent-nexus)
│   ├── base.py
│   ├── backends/
│   └── ...
├── output_parsers/   # Output parsers (→ universal-agent-nexus)
│   └── ...
├── tools/            # Tool utilities (→ universal-agent-tools or separate package)
│   ├── model_config.py
│   ├── observability_helper.py
│   └── ollama_tools.py
└── patterns/         # Advanced patterns (→ universal-agent-tools)
    └── ...
```

## Promotion Path

### Phase 1: Validation (Current)
- ✅ Used by examples
- ✅ API tested in real scenarios
- ✅ Patterns documented

### Phase 2: Stabilization
- [ ] API finalized
- [ ] Tests added
- [ ] Documentation complete

### Phase 3: Promotion
- [ ] Move to `universal-agent-nexus` or appropriate package
- [ ] Update examples to use promoted packages
- [ ] Remove from `_lib/`

## Usage in Examples

Examples import from `_lib` using relative imports:

```python
from _lib.runtime import NexusRuntime
from _lib.cache_fabric import create_cache_fabric
from _lib.tools import ModelConfig
```

## Migration Notes

When promoting:
1. Update package structure to match target package
2. Update imports in all examples
3. Add proper package metadata (setup.py, pyproject.toml)
4. Version appropriately
5. Update documentation

## Status

| Module | Status | Target Package | ETA |
|--------|--------|----------------|-----|
| `runtime/` | ✅ Validated | `universal-agent-nexus` | Q1 2026 |
| `cache_fabric/` | ✅ Validated | `universal-agent-nexus` | Q1 2026 |
| `output_parsers/` | ✅ Validated | `universal-agent-nexus` | Q1 2026 |
| `tools/` | ✅ Validated | `universal-agent-tools` | Q1 2026 |
| `patterns/` | 🔄 In Progress | `universal-agent-tools` | Q2 2026 |

