# Upstream Library Analysis

Analysis of the Universal Agent stack after examining the source code.

---

## 📐 Architecture Overview

```
universal_agent_nexus (Compiler)
         ↓ Compiles manifests
universal_agent_fabric (Composition Layer)
    ├─ Role, Capability, Domain, GovernanceRule
    └─ FabricBuilder → builds composed specs
         ↓ Produces
universal_agent_architecture (Runtime/Kernel)
    ├─ AgentManifest, PolicySpec, PolicyRule
    ├─ PolicyEngine → enforces at runtime
    ├─ GraphEngine → executes graphs
    └─ Handlers (Router, Tool, Human)
```

---

## ✅ What EXISTS (Examined in Source)

### `universal_agent_architecture` (The Kernel)

**Location:** `C:\universal_agent_architecture\`

#### PolicyEngine (EXISTS!)

```python
# universal_agent/policy/engine.py
class PolicyEngine:
    def __init__(self, policies: List[PolicySpec]):
        self.policies = {p.name: p for p in policies}

    def check(self, policy_name: str, target: str, context: Dict[str, Any] | None = None) -> PolicyAction:
        """
        Check if an action on a target is allowed by the named policy.
        Returns: PolicyAction (ALLOW, DENY, REQUIRE_APPROVAL)
        """
```

**Capabilities:**
- ✅ `check(policy_name, target, context)` → Returns `PolicyAction`
- ✅ Target matching with wildcards (`*`)
- ✅ Condition evaluation (key/value matching)
- ✅ Logging of matched rules

#### PolicySpec Schema (EXISTS!)

```python
# universal_agent/manifests/schema.py
class PolicyRule(BaseModel):
    id: Optional[str]
    description: Optional[str]
    target: List[str]  # e.g., 'tool:delete_db', 'model:gpt-4'
    conditions: Dict[str, Any]
    action: PolicyAction  # ALLOW, DENY, REQUIRE_APPROVAL
    approval_channel: Optional[str]

class PolicySpec(BaseModel):
    name: str
    description: Optional[str]
    rules: List[PolicyRule]
```

#### Integration Points (WHERE POLICIES SHOULD BE CALLED)

Looking at the handlers in `universal_agent/runtime/handlers.py`:

```python
class ToolHandler(NodeHandler):
    async def execute(self, node: Node, inputs: Dict[str, Any], context: Dict[str, Any]):
        # TODO: Policy check should happen HERE before execution
        # action = policy_engine.check("tool_policy", f"tool:{spec.name}", context)
        # if action == PolicyAction.DENY:
        #     raise PolicyViolation(...)
        
        result = await executor.execute(spec.config, inputs)
        return {"status": "success", "data": result}

class RouterHandler(NodeHandler):
    async def execute(self, node: Node, inputs: Dict[str, Any], context: Dict[str, Any]):
        # TODO: Policy check should happen HERE before LLM call
        # action = policy_engine.check("router_policy", f"model:{model}", context)
        
        response = await self.llm_client.chat(model, messages)
```

---

## ⚠️ ACTUAL GAPS (After Code Review)

### Gap 1: PolicyEngine Not Injected into Handlers

**Current State:** `PolicyEngine` exists but handlers don't receive it.

**Location:** `universal_agent/runtime/handlers.py`

**Fix Required:**
```python
class ToolHandler(NodeHandler):
    def __init__(
        self, 
        manifest: AgentManifest, 
        executors: Dict[ToolProtocol, IToolExecutor],
        policy_engine: Optional[PolicyEngine] = None,  # ← ADD THIS
    ):
        self.policy_engine = policy_engine
        
    async def execute(self, node: Node, inputs: Dict[str, Any], context: Dict[str, Any]):
        if self.policy_engine:
            tool_ref = node.spec.tool
            spec = self._tools.get(tool_ref.name)
            
            # Check tool policy
            if spec.policy:
                action = self.policy_engine.check(spec.policy.name, f"tool:{spec.name}", context)
                if action == PolicyAction.DENY:
                    return {"status": "denied", "reason": "Policy violation"}
                elif action == PolicyAction.REQUIRE_APPROVAL:
                    # Suspend for HITL
                    ...
```

**Priority:** 🔴 HIGH - Core enforcement missing

---

### Gap 2: Fabric → Architecture Schema Mapping

**Current State:** `universal_agent_fabric.GovernanceRule` ≠ `universal_agent_architecture.PolicyRule`

| Fabric Schema | Architecture Schema |
|--------------|---------------------|
| `name` | `id` or `description` |
| `target_pattern` (regex) | `target` (list of strings) |
| `action` (string) | `action` (PolicyAction enum) |
| `conditions` (dict) | `conditions` (dict) |

**Fix Required:** Add conversion function in Fabric or Nexus:

```python
# In universal_agent_fabric or nexus
def governance_rule_to_policy_rule(rule: GovernanceRule) -> PolicyRule:
    return PolicyRule(
        description=rule.name,
        target=[rule.target_pattern] if rule.target_pattern else ["*"],
        action=PolicyAction(rule.action),
        conditions=rule.conditions or {},
    )
```

**Priority:** 🟡 MEDIUM - Bridging layer needed

---

### Gap 3: Domain.capabilities Type Mismatch

**Already Documented:** Domain expects `List[Capability]` objects, not string references.

**Workaround:** Embed full capability objects in YAML (implemented in playground).

**Priority:** 🟢 LOW - Workaround exists

---

## 🎯 Recommended Upstream PRs

### PR 1: Inject PolicyEngine into Handlers (HIGH)

**File:** `universal_agent_architecture/universal_agent/runtime/handlers.py`

```python
class ToolHandler(NodeHandler):
    def __init__(
        self, 
        manifest: AgentManifest, 
        executors: Dict[ToolProtocol, IToolExecutor],
        policy_engine: Optional[PolicyEngine] = None,
    ):
        self.manifest = manifest
        self.executors = executors
        self.policy_engine = policy_engine
        self._tools = {tool.name: tool for tool in manifest.tools}

    async def execute(self, node: Node, inputs: Dict[str, Any], context: Dict[str, Any]):
        tool_ref = node.spec.tool
        spec = self._tools.get(tool_ref.name)
        
        # POLICY ENFORCEMENT
        if self.policy_engine and spec.policy:
            action = self.policy_engine.check(
                spec.policy.name, 
                f"tool:{spec.name}", 
                context
            )
            if action == PolicyAction.DENY:
                logger.warning("Policy DENIED tool %s", spec.name)
                return {"status": "denied", "policy": spec.policy.name}
            elif action == PolicyAction.REQUIRE_APPROVAL:
                logger.info("Policy requires approval for tool %s", spec.name)
                # TODO: Integrate with HumanHandler/HITL
        
        # ... existing execution code
```

### PR 2: Add Fabric → Architecture Converter (MEDIUM)

**File:** `universal_agent_nexus/adapters/fabric_bridge.py` (new)

```python
from universal_agent_fabric import GovernanceRule as FabricRule
from universal_agent.manifests.schema import PolicyRule, PolicyAction

def convert_governance_rules(fabric_rules: List[FabricRule]) -> List[PolicyRule]:
    """Convert Fabric GovernanceRules to Architecture PolicyRules."""
    return [
        PolicyRule(
            description=r.name,
            target=[r.target_pattern] if r.target_pattern else ["*"],
            action=PolicyAction(r.action.upper()),
            conditions=r.conditions or {},
        )
        for r in fabric_rules
    ]
```

---

## 📋 Summary

| Component | Status | Notes |
|-----------|--------|-------|
| **PolicyEngine** | ✅ EXISTS | `universal_agent/policy/engine.py` |
| **PolicySpec/Rule** | ✅ EXISTS | `universal_agent/manifests/schema.py` |
| **Handler Injection** | ❌ MISSING | Handlers don't receive PolicyEngine |
| **Fabric→Arch Bridge** | ❌ MISSING | Schema conversion needed |
| **Domain.capabilities** | ⚠️ WORKAROUND | Embed full objects |

**The PolicyEngine EXISTS and WORKS - it just needs to be wired into the handlers!**

---

## 🔧 Workaround for Playground

Until upstream PRs are merged, enforce policies at the application layer:

```python
# backend/llm_provider.py (playground)
from universal_agent.policy.engine import PolicyEngine
from universal_agent.manifests.schema import PolicySpec, PolicyRule, PolicyAction

# Load policies from our YAML
policy_engine = PolicyEngine([
    PolicySpec(name="playground_safety", rules=[...])
])

# Check before generating
action = policy_engine.check("playground_safety", f"content:{message}", context)
if action == PolicyAction.DENY:
    return "[Content blocked by policy]"
```

This is the **correct architectural boundary** - the kernel provides the engine, apps wire it up.
