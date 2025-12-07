# Patterns Extraction Plan

**Identified patterns from content moderation exercise that should be extracted into reusable helpers.**

---

## ✅ Already Extracted

### 1. Observability Helper
**Location:** `universal_agent_tools/observability_helper.py`
- ✅ `setup_observability()` - One-line OpenTelemetry setup
- ✅ `trace_runtime_execution()` - Context manager for tracing

### 2. Router Patterns
**Location:** `tools/universal_agent_tools/router_patterns.py`
- ✅ `RouteDefinition` - Route configuration
- ✅ `build_decision_agent_manifest()` - Single-decision router builder

### 3. Ollama Tools
**Location:** `universal_agent_tools/ollama_tools.py`
- ✅ `create_llm_with_tools()` - Ollama LLM setup
- ✅ `MCPToolLoader` - MCP tool loading
- ✅ `parse_tool_calls_from_content()` - Manual tool parsing

### 4. Model Config
**Location:** `universal_agent_tools/model_config.py`
- ✅ `ModelConfig.resolve_model()` - Standardized model resolution

---

## 🔄 Patterns to Extract

### 1. Convergent Audit Pattern

**Use Case:** All execution paths converge to audit/compliance node.

**Current Implementation:** Manual edge creation in manifest.

**Proposed Helper:**
```python
# universal_agent_tools/compliance_patterns.py

def add_audit_convergence(
    graph: GraphIR,
    audit_node_id: str,
    exclude_nodes: Optional[List[str]] = None
) -> GraphIR:
    """
    Add edges from all terminal nodes to audit node.
    
    Args:
        graph: Graph to modify
        audit_node_id: ID of audit/compliance node
        exclude_nodes: Nodes to exclude from convergence
    
    Returns:
        Modified graph with convergent edges
    """
    # Implementation:
    # 1. Find all nodes without outgoing edges (terminals)
    # 2. Add edge from each terminal to audit_node
    # 3. Exclude specified nodes if provided
```

**Usage:**
```python
from universal_agent_tools.compliance_patterns import add_audit_convergence

graph = add_audit_convergence(graph, audit_node_id="audit_log")
```

**Benefits:**
- Ensures compliance logging
- Reduces manifest boilerplate
- Single source of truth

---

### 2. Escalation Workflow Builder

**Use Case:** Create escalation nodes with queue, priority, SLA tracking.

**Current Implementation:** Manual node creation with config.

**Proposed Helper:**
```python
# universal_agent_tools/workflow_patterns.py

@dataclass
class EscalationConfig:
    queue: str
    priority: str = "normal"  # normal, high, urgent
    sla_hours: int = 24
    notify: Optional[List[str]] = None

def create_escalation_node(
    node_id: str,
    label: str,
    config: EscalationConfig
) -> NodeIR:
    """
    Create escalation task node with SLA tracking.
    
    Args:
        node_id: Unique node identifier
        label: Human-readable label
        config: Escalation configuration
    
    Returns:
        NodeIR for escalation task
    """
    return NodeIR(
        id=node_id,
        kind=NodeKind.TASK,
        label=label,
        config={
            "action": "escalate",
            "queue": config.queue,
            "priority": config.priority,
            "sla_hours": config.sla_hours,
            **({"notify": config.notify} if config.notify else {})
        }
    )
```

**Usage:**
```python
from universal_agent_tools.workflow_patterns import create_escalation_node, EscalationConfig

escalation = create_escalation_node(
    node_id="human_review",
    label="Escalate to Human Review",
    config=EscalationConfig(
        queue="moderation_queue",
        priority="normal",
        sla_hours=24
    )
)
```

**Benefits:**
- Standardized escalation config
- Type-safe configuration
- Reusable across examples

---

### 3. Multi-Tier Router Builder

**Use Case:** Build content moderation-style multi-tier routers.

**Current Implementation:** Manual manifest creation.

**Proposed Helper:**
```python
# universal_agent_tools/router_patterns.py (extend existing)

@dataclass
class RiskTier:
    """Defines a risk tier with handler."""
    name: str              # "safe", "low", "medium", etc.
    handler_node_id: str   # Node to route to
    label: Optional[str] = None
    config: Optional[Dict] = None

def build_multi_tier_router(
    router_id: str,
    router_config: Dict[str, Any],  # system_message, model, etc.
    tiers: List[RiskTier],
    audit_node_id: Optional[str] = None
) -> GraphIR:
    """
    Build multi-tier router graph (content moderation pattern).
    
    Args:
        router_id: Router node ID
        router_config: Router configuration (system_message, model)
        tiers: List of risk tiers
        audit_node_id: Optional audit node for convergence
    
    Returns:
        GraphIR with router and tier handlers
    """
    # Implementation:
    # 1. Create router node
    # 2. Create handler nodes for each tier
    # 3. Create edges with route keys
    # 4. Optionally add audit convergence
```

**Usage:**
```python
from universal_agent_tools.router_patterns import build_multi_tier_router, RiskTier

tiers = [
    RiskTier("safe", "auto_approve", "Auto Approve"),
    RiskTier("low", "policy_check", "Policy Check"),
    RiskTier("medium", "human_review", "Human Review"),
    RiskTier("high", "auto_reject", "Auto Reject"),
    RiskTier("critical", "critical_action", "Critical Action"),
]

graph = build_multi_tier_router(
    router_id="risk_assessment",
    router_config={
        "system_message": "Classify content risk...",
        "model": "ollama://qwen3:8b"
    },
    tiers=tiers,
    audit_node_id="audit_log"
)
```

**Benefits:**
- Reduces boilerplate
- Standardized pattern
- Easy to extend tiers

---

### 4. Policy Validation Pattern

**Use Case:** Validate content with dual outcomes (pass/fail).

**Proposed Helper:**
```python
# universal_agent_tools/validation_patterns.py

def create_policy_validation_flow(
    validator_node_id: str,
    validator_tool_ref: str,
    pass_node_id: str,
    fail_node_id: str,
    pass_config: Optional[Dict] = None,
    fail_config: Optional[Dict] = None
) -> Tuple[List[NodeIR], List[EdgeIR]]:
    """
    Create policy validation flow with dual outcomes.
    
    Args:
        validator_node_id: Policy check tool node ID
        validator_tool_ref: Tool reference for validation
        pass_node_id: Node for compliant content
        fail_node_id: Node for violations
        pass_config: Config for pass node
        fail_config: Config for fail node
    
    Returns:
        Tuple of (nodes, edges) for validation flow
    """
    # Implementation:
    # 1. Create validator tool node
    # 2. Create pass handler node
    # 3. Create fail handler node
    # 4. Create edges with route keys ("compliant", "violation")
```

**Usage:**
```python
from universal_agent_tools.validation_patterns import create_policy_validation_flow

nodes, edges = create_policy_validation_flow(
    validator_node_id="policy_check",
    validator_tool_ref="policy_validator",
    pass_node_id="policy_approve",
    fail_node_id="policy_failed",
    pass_config={"action": "approve"},
    fail_config={"action": "escalate", "queue": "policy_violation_queue"}
)
```

---

### 5. Standard Runtime Template

**Use Case:** Consistent runtime setup across all examples.

**Proposed Helper:**
```python
# universal_agent_tools/runtime_helper.py

async def create_runtime_from_manifest(
    manifest_path: str,
    graph_name: str,
    service_name: str,
    enable_checkpointing: bool = False,
    postgres_url: Optional[str] = None
) -> LangGraphRuntime:
    """
    Create and initialize runtime with standard pattern.
    
    Args:
        manifest_path: Path to manifest.yaml
        graph_name: Graph name to initialize
        service_name: Service name for observability
        enable_checkpointing: Enable checkpointing
        postgres_url: PostgreSQL URL for checkpointing
    
    Returns:
        Initialized LangGraphRuntime
    """
    # Implementation:
    # 1. Setup observability
    # 2. Parse manifest
    # 3. Run optimization passes
    # 4. Initialize runtime
    # 5. Return runtime
```

**Usage:**
```python
from universal_agent_tools.runtime_helper import create_runtime_from_manifest

runtime = await create_runtime_from_manifest(
    manifest_path="manifest.yaml",
    graph_name="moderate_content",
    service_name="content-moderation"
)

result = await runtime.execute(
    execution_id="exec-001",
    input_data={"messages": [HumanMessage(content="...")]}
)
```

---

## Implementation Priority

### High Priority (Immediate Value)
1. ✅ **Standard Runtime Template** - Used in every example
2. ✅ **Convergent Audit Pattern** - Common compliance requirement
3. ✅ **Escalation Workflow Builder** - Reusable across workflows

### Medium Priority (Nice to Have)
4. **Multi-Tier Router Builder** - Specific to content moderation
5. **Policy Validation Pattern** - Common but less frequent

### Low Priority (Future)
6. **Advanced Routing Patterns** - Complex scenarios
7. **State Management Helpers** - If custom state needed

---

## Extraction Guidelines

1. **Keep It Simple:** Helpers should reduce boilerplate, not add complexity
2. **Type Safety:** Use dataclasses and type hints
3. **Documentation:** Include usage examples
4. **Testing:** Add tests for each helper
5. **Backwards Compatible:** Don't break existing code

---

## Next Steps

1. Create `universal_agent_tools/compliance_patterns.py`
2. Create `universal_agent_tools/workflow_patterns.py`
3. Extend `tools/universal_agent_tools/router_patterns.py`
4. Create `universal_agent_tools/runtime_helper.py`
5. Update examples to use new helpers
6. Add tests for each helper

---

### 6. JSON Parsing Helper

**Use Case:** Parse JSON from LLM router responses (common in ETL pipelines).

**Current Implementation:** Manual parsing in each example.

**Proposed Helper:**
```python
# universal_agent_tools/llm_helpers.py

def parse_json_from_message(content: str) -> Optional[Dict]:
    """
    Extract and parse JSON from LLM message content.
    
    Handles:
    - Pretty-printed JSON with newlines
    - JSON embedded in text
    - Whitespace normalization
    
    Args:
        content: Message content string
    
    Returns:
        Parsed dict or None if no valid JSON found
    """
    # Implementation
```

**Usage:**
```python
from universal_agent_tools.llm_helpers import parse_json_from_message

for msg in messages:
    if hasattr(msg, 'content'):
        enriched_data = parse_json_from_message(msg.content)
        if enriched_data:
            break
```

**Benefits:**
- Consistent JSON parsing
- Handles edge cases (newlines, whitespace)
- Reusable across examples

---

## New Patterns from Example 03

### Router-Based Data Enrichment

**Pattern:** Use router node to generate structured JSON output for data enrichment.

**Key Learnings:**
- Router system message must explicitly request JSON format
- Use `router_ref` to reference router configuration
- LLM response becomes the enriched data (not just routing decision)
- JSON parsing helper needed for reliable extraction

**See:** `03-data-pipeline/manifest.yaml` for full example

### Sequential Pipeline Flow

**Pattern:** Linear ETL flow without complex routing.

**Key Learnings:**
- Simple edges (no conditions needed for linear flow)
- Each stage transforms data
- Final stage logs completion
- Easy to extend with additional stages

---

**Last Updated:** December 7, 2025 - Content moderation and ETL pipeline exercise analysis

