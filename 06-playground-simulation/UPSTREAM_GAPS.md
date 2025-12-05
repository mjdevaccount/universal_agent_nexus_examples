# Upstream Library Gaps Analysis

This document identifies potential improvements for the upstream Universal Agent libraries based on integration testing in this playground example.

---

## 📦 universal-agent-fabric (v0.1.1)

### Current Exports
```python
from universal_agent_fabric import (
    Role,           # ✅ Works well
    Capability,     # ✅ Works well  
    Domain,         # ⚠️ See below
    GovernanceRule, # ✅ Works well
    FabricSpec,     # ✅ Works well
    FabricBuilder,  # ✅ Works well
)
```

### Gap 1: Domain.capabilities Requires Full Objects

**Issue:** `Domain.capabilities` is typed as `List[Capability]`, requiring full Capability objects to be embedded.

**Current behavior:**
```yaml
# This FAILS - capabilities as strings
name: "playground_social"
capabilities:
  - "speak"
  - "analyze_situation"

# This WORKS - full capability objects embedded
name: "playground_social"
capabilities:
  - name: "speak"
    description: "..."
    protocol: "local"
```

**Impact:** Cannot reference capabilities by name; must duplicate capability definitions in every domain.

**Suggested Fix:**
```python
# Option A: Support both string references and full objects
capabilities: List[Union[str, Capability]] = Field(default_factory=list)

# Option B: Add a resolver that looks up capabilities by name
class FabricBuilder:
    def __init__(self, spec: FabricSpec, capability_registry: Dict[str, Capability] = None):
        ...
```

**Priority:** Medium - Workaround exists (embed full objects)

---

### Gap 2: No Capability Registry

**Issue:** No built-in way to register and reference capabilities across the system.

**Current behavior:** Each component loads capabilities independently.

**Suggested Fix:**
```python
# Add to universal_agent_fabric
class CapabilityRegistry:
    def register(self, capability: Capability) -> None: ...
    def get(self, name: str) -> Capability: ...
    def load_from_directory(self, path: Path) -> None: ...
```

**Priority:** Low - Can implement at application level

---

### Gap 3: GovernanceRule.conditions is Untyped

**Issue:** `GovernanceRule.conditions` is `Optional[dict]` - no schema for what conditions can contain.

**Current schema:**
```python
class GovernanceRule(BaseModel):
    name: str
    target_pattern: Optional[str] = None
    action: str
    conditions: Optional[dict] = None  # ← Untyped
```

**Suggested Fix:**
```python
class RuleCondition(BaseModel):
    severity: Optional[str] = None  # "low", "medium", "high"
    message: Optional[str] = None
    requires_approval: bool = False
    custom: Dict[str, Any] = Field(default_factory=dict)

class GovernanceRule(BaseModel):
    ...
    conditions: Optional[RuleCondition] = None
```

**Priority:** Low - Flexibility is useful

---

### Gap 4: No Policy Enforcement at Runtime

**Issue:** Governance rules are compiled but there's no built-in enforcement mechanism.

**Current behavior:** Rules are included in `FabricBuilder.build()` output but not enforced.

**Suggested Fix:**
```python
# Add to universal_agent_fabric
class PolicyEnforcer:
    def __init__(self, rules: List[GovernanceRule]): ...
    def check(self, content: str) -> PolicyResult: ...
    
class PolicyResult(BaseModel):
    allowed: bool
    violations: List[str]
    warnings: List[str]
```

**Priority:** High - Essential for production use

---

## 📦 universal-agent-nexus (v1.0.1)

### Current Exports
```python
from universal_agent_nexus import (
    load_manifest,      # ✅ Works
    load_manifest_str,  # ✅ Works
    adapters,           # Needs exploration
    cli,                # Needs exploration
    observability,      # Needs exploration
)
```

### Gap 5: No Direct Fabric Integration

**Issue:** No built-in way to compile Fabric specs into Nexus manifests.

**Suggested Fix:**
```python
# Add to universal_agent_nexus
def from_fabric_spec(spec: FabricSpec) -> Manifest:
    """Convert Universal Agent Fabric spec to UAA manifest."""
    ...
```

**Priority:** Medium - Would enable seamless compilation pipeline

---

### Gap 6: Adapter Documentation

**Issue:** The `adapters` module needs documentation for available runtime targets.

**Questions:**
- What adapters are available? (LangGraph? AWS? MCP?)
- How to use them programmatically?
- How to compile to specific targets?

**Priority:** High - Essential for users

---

## 📦 universal-agent-arch (v0.1.0)

**Note:** Module not directly importable (`ModuleNotFoundError`). May be an internal dependency.

### Questions:
- Is this the runtime/kernel?
- Should it be used directly?
- What's the relationship with Nexus?

---

## 🎯 Summary

| Gap | Library | Priority | Status |
|-----|---------|----------|--------|
| Domain capability references | fabric | Medium | Workaround exists |
| Capability registry | fabric | Low | App-level solution |
| GovernanceRule typing | fabric | Low | Flexibility useful |
| Policy enforcement | fabric | **High** | Needed for production |
| Fabric→Nexus bridge | nexus | Medium | Manual conversion |
| Adapter documentation | nexus | **High** | Needed for users |

---

## 🔧 Workarounds Implemented

### Domain Capabilities
Embed full capability objects in domain YAML instead of string references.

### Policy Enforcement
Implement at application level in playground backend (not yet done - TODO).

### Capability Registry
Implemented in `PlaygroundCompiler._load_capabilities()` as local registry.

---

## 📝 Recommended Upstream PRs

1. **universal-agent-fabric:** Add `PolicyEnforcer` class
2. **universal-agent-fabric:** Support capability string references in Domain
3. **universal-agent-nexus:** Add adapter documentation
4. **universal-agent-nexus:** Add `from_fabric_spec()` bridge function

