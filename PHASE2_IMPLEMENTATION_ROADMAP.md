# Phase 2: Example Integration & Workflow Helpers

**Status:** IN PROGRESS  
**Start Date:** Monday, December 8, 2025, 10:50 AM CST  
**Branch:** `feature/phase-2-example-integration`  
**Target Completion:** Wednesday, December 10, 2025

---

## Phase 2 Goals

### Primary
1. ✅ Create **ToolCallingWorkflow** helper for Examples 06, 10, 11
2. ✅ Create **ConditionalWorkflow** helper for branching patterns (Examples 11, 12)
3. ✅ Refactor Examples 06 & 07 to use workflow abstraction
4. ✅ Create YAML workflow definitions (registry)
5. ✅ Add helper functions for common patterns

### Secondary
1. Unit tests for new workflow types
2. Integration tests across all examples
3. Performance benchmarks
4. Migration guide for remaining examples (13-15)

---

## Deliverables

### New Files to Create

```
shared/workflows/
├── helpers.py                          # ToolCallingWorkflow, ConditionalWorkflow, etc.
├── definitions/
│   ├── __init__.py
│   ├── intelligence-extraction-validation.yaml  # Example 07 pattern
│   ├── tool-calling.yaml                       # Examples 06, 10
│   ├── conditional-routing.yaml                # Examples 11, 12
│   ├── simple-qa.yaml                          # Example 13
│   └── content-moderation.yaml                 # Examples 14, 15
└── registry.py                        # YAML loader + registry

06-playground-simulation/
├── example_06_refactored.py            # Refactored using ToolCallingWorkflow
└── workflows.yaml                      # Optional: Inline workflow config

07-innovation-waves/
├── example_07_refactored.py            # Use new workflow abstraction
└── workflows.yaml                      # Optional: Inline workflow config

tests/
├── test_tool_calling_workflow.py       # Tests for ToolCallingWorkflow
├── test_conditional_workflow.py        # Tests for ConditionalWorkflow
├── test_example_06.py                  # Integration test for Example 06
└── test_example_07.py                  # Integration test for Example 07
```

---

## Implementation Plan

### Week 1 (Now): Core Helpers + Example Integration

**Monday-Tuesday (Days 1-2):**
- [ ] Create `ToolCallingWorkflow` in `shared/workflows/helpers.py`
- [ ] Create `ConditionalWorkflow` in `shared/workflows/helpers.py`
- [ ] Create workflow registry system
- [ ] Create YAML definition format

**Wednesday (Day 3):**
- [ ] Refactor Example 06 using ToolCallingWorkflow
- [ ] Refactor Example 07 using IntelligenceNode workflow
- [ ] Create YAML definitions for both
- [ ] Write integration tests

**Thursday-Friday (Days 4-5):**
- [ ] Unit tests for new workflow types
- [ ] Performance benchmarks
- [ ] Documentation updates
- [ ] Review and prepare for merge

---

## Detailed Implementation

### 1. ToolCallingWorkflow (shared/workflows/helpers.py)

**Purpose:** Orchestrate tool-calling loops (Examples 06, 10)

**Pattern:**
```
START
  ↓
UserQuery
  ↓
[decision] → Need tool? Yes ↓
  ↓ No
  └─→ [response]
ToolCall
  ↓
ToolResult
  ↓
[back to decision]
```

**API:**
```python
class ToolCallingWorkflow(Workflow):
    def __init__(
        self,
        name: str,
        llm: ChatOllama,
        tools: List[Tool],
        max_iterations: int = 10,
        **kwargs
    ):
        """Create tool-calling workflow.
        
        Args:
            name: Workflow name
            llm: Language model
            tools: Available tools
            max_iterations: Max tool calls before stop
        """
    
    async def invoke(self, query: str, **kwargs) -> dict:
        """Run tool-calling loop.
        
        Returns:
            {
                "query": str,
                "tool_calls": [{
                    "tool": str,
                    "input": dict,
                    "result": str,
                    "timestamp": float
                }],
                "final_response": str,
                "iterations": int,
                "metrics": {...}
            }
        """
```

**Features:**
- Automatic tool binding from LangChain
- Iteration limiting (max_iterations safety)
- Tool result history in state
- Automatic LLM response parsing
- Per-tool execution metrics
- Graceful exit on max iterations

---

### 2. ConditionalWorkflow (shared/workflows/helpers.py)

**Purpose:** Handle branching logic (Examples 11, 12)

**Pattern:**
```
START
  ↓
Input
  ↓
[condition] ──→ Branch A ──→ NodeA1 ──→ NodeA2
      │
      └────→ Branch B ──→ NodeB1 ──→ NodeB2
      │
      └────→ Branch C ──→ NodeC1 ──→ NodeC2
  ↓
Merge
  ↓
END
```

**API:**
```python
class ConditionalWorkflow(Workflow):
    def __init__(
        self,
        name: str,
        state_schema: type,
        decision_node: BaseNode,
        branches: Dict[str, List[BaseNode]],
        merge_node: Optional[BaseNode] = None,
        **kwargs
    ):
        """Create conditional workflow.
        
        Args:
            name: Workflow name
            state_schema: State TypedDict
            decision_node: Node that returns branch key
            branches: {"branch_key": [nodes]}
            merge_node: Optional node after all branches
        """
    
    async def invoke(self, state: dict, **kwargs) -> dict:
        """Run conditional workflow.
        
        Returns:
            {
                "state": {...},
                "decision": str,
                "branch_executed": str,
                "metrics": {...}
            }
        """
```

**Features:**
- Dynamic branch selection via decision_node
- Parallel branch execution (optional)
- Merge node for combining results
- Branch history in state
- Per-branch metrics
- Type-safe state transitions

---

### 3. Workflow Registry (shared/workflows/registry.py)

**Purpose:** Load workflows from YAML definitions

**API:**
```python
class WorkflowRegistry:
    """Registry for workflow definitions."""
    
    @classmethod
    def from_yaml(cls, path: str) -> Workflow:
        """Load workflow from YAML file.
        
        Args:
            path: Path to workflow.yaml
        
        Returns:
            Instantiated Workflow
        """
    
    @classmethod
    def register(cls, name: str, workflow_class: type) -> None:
        """Register custom workflow type.
        
        Args:
            name: Workflow type name
            workflow_class: Workflow class to register
        """
    
    @classmethod
    def get(cls, name: str) -> type:
        """Get registered workflow class.
        
        Args:
            name: Workflow type name
        
        Returns:
            Workflow class
        """
```

**YAML Format:**
```yaml
# workflow.yaml
name: adoption-prediction
type: intelligence-extraction-validation

state:
  event: dict
  scenario: str
  analysis: str
  extracted: dict
  validated: dict

nodes:
  intelligence:
    type: IntelligenceNode
    llm:
      model: qwen3:8b
      temperature: 0.8
    prompt_template: |
      Analyze this event: {event}
      Scenario: {scenario}
      ...
    required_state_keys:
      - event
      - scenario
  
  extraction:
    type: ExtractionNode
    llm:
      model: qwen3:8b
      temperature: 0.1
    output_schema:
      module: examples.schemas
      class: AdoptionPrediction
    json_repair_strategies:
      - incremental_repair
      - llm_repair
      - regex_fallback
  
  validation:
    type: ValidationNode
    output_schema:
      module: examples.schemas
      class: AdoptionPrediction
    validation_rules:
      timeline_sanity: "disruption_score < 8.0 or months <= 24"
      market_cap_sanity: "disruption_score < 5.0 or cap >= 1.0"
    repair_on_fail: true

edges:
  - [intelligence, extraction]
  - [extraction, validation]
```

---

### 4. Example 06 Refactoring

**Current State:** Custom tool-calling loop (150+ lines)

**Refactored State:** Using ToolCallingWorkflow

```python
from shared.workflows import ToolCallingWorkflow

# Define tools
tools = [
    calculate_tool,
    search_tool,
    analyze_tool,
]

# Create workflow (3 lines vs 150 lines)
workflow = ToolCallingWorkflow(
    name="playground-simulation",
    llm=llm,
    tools=tools,
    max_iterations=10,
)

# Run
result = await workflow.invoke(
    query="Simulate market adoption for AI breakthroughs"
)

print(result["final_response"])
print(f"Tool calls: {len(result['tool_calls'])}")
```

**Deliverable:**
- `06-playground-simulation/example_06_refactored.py` (~100 lines vs 150+)
- `06-playground-simulation/workflows.yaml` (workflow definition)
- Full test coverage

---

### 5. Example 07 Integration

**Current State:** Already refactored (Example 07 refactored in Phase 1)

**Phase 2 Additions:**
- Move to proper location: `07-innovation-waves/`
- Add YAML definition
- Add tests
- Add metrics comparison

---

## Testing Strategy

### Unit Tests

**test_tool_calling_workflow.py:**
```python
def test_tool_calling_basic():
    # Test: Tool calling with simple query
    # Assert: Correct tool selected and executed

def test_tool_calling_max_iterations():
    # Test: Query that would trigger >10 calls
    # Assert: Stops at max_iterations

def test_tool_calling_error_handling():
    # Test: Tool raises exception
    # Assert: Error logged, loop continues

def test_tool_calling_metrics():
    # Test: Run workflow and collect metrics
    # Assert: All metrics present and correct
```

**test_conditional_workflow.py:**
```python
def test_conditional_single_branch():
    # Test: Decision returns valid branch key
    # Assert: Correct branch executed

def test_conditional_invalid_branch():
    # Test: Decision returns unknown branch key
    # Assert: Error or default branch

def test_conditional_merge():
    # Test: Multiple branches converge at merge node
    # Assert: Merge node receives combined state

def test_conditional_metrics():
    # Test: Per-branch metrics collected
    # Assert: All branches in metrics
```

### Integration Tests

**test_example_06.py:**
```python
@pytest.mark.asyncio
async def test_example_06_refactored():
    # Test: Example 06 using new workflow
    # Assert: Same output as original
    # Assert: Performance within bounds
    # Assert: All metrics collected

@pytest.mark.asyncio
async def test_example_06_yaml_loading():
    # Test: Load Example 06 from YAML
    # Assert: Workflow created correctly
    # Assert: Same output as hardcoded
```

**test_example_07.py:**
```python
@pytest.mark.asyncio
async def test_example_07_workflow():
    # Test: Example 07 workflow execution
    # Assert: Output matches expected format
    # Assert: Success rate > 99%
    # Assert: Metrics complete
```

---

## Success Metrics

### Code Reduction
| Example | Before | After | Reduction |
|---------|--------|-------|----------|
| **06** | 150+ lines | 30 lines (workflow) + 20 lines (schema) | -80% |
| **07** | 440 lines | 90 lines (already done) | -80% |
| **Projected** | 15 examples × 200 avg | ~50 lines per example | -75% |

### Reliability
| Metric | Before | After | Target |
|--------|--------|-------|--------|
| **Success Rate** | 70% | 99%+ | ✓ |
| **Silent Failures** | 20-30% | 0% | ✓ |
| **Repair Rate** | Manual | Automatic | ✓ |

### Observability
- ✓ Visualization (ASCII graph)
- ✓ Per-node metrics (duration, status, warnings)
- ✓ Repair strategy tracking
- ✓ Error context preservation

---

## File Structure After Phase 2

```
shared/workflows/
├── __init__.py
├── nodes.py
├── common_nodes.py
├── workflow.py
├── helpers.py              # NEW: ToolCalling, Conditional, etc.
├── registry.py             # NEW: YAML loading
├── README.md
├── definitions/             # NEW: Workflow YAML definitions
│   ├── __init__.py
│   ├── intelligence-extraction-validation.yaml
│   ├── tool-calling.yaml
│   ├── conditional-routing.yaml
│   ├── simple-qa.yaml
│   └── content-moderation.yaml
└── examples/
    ├── __init__.py
    ├── example_07_refactored.py
    └── example_06_refactored.py  # NEW

06-playground-simulation/
├── example_06_refactored.py  # NEW
├── workflows.yaml            # NEW
└── tools/
    ├── calculator.py
    ├── search.py
    └── analyzer.py

07-innovation-waves/
├── example_07_refactored.py  # Moved from shared/workflows/examples/
└── workflows.yaml

tests/
├── test_tool_calling_workflow.py  # NEW
├── test_conditional_workflow.py   # NEW
├── test_example_06.py             # NEW
├── test_example_07.py             # NEW
└── test_workflow_registry.py       # NEW
```

---

## Timeline

### Tuesday (Dec 9) - 4 Hours
- [ ] 8:00 AM - 9:00 AM: Create ToolCallingWorkflow
- [ ] 9:00 AM - 10:00 AM: Create ConditionalWorkflow
- [ ] 10:00 AM - 11:00 AM: Create workflow registry + YAML support
- [ ] 11:00 AM - 12:00 PM: Documentation + examples

### Wednesday (Dec 10) - 4 Hours
- [ ] 8:00 AM - 9:30 AM: Refactor Example 06
- [ ] 9:30 AM - 10:30 AM: Move/refactor Example 07
- [ ] 10:30 AM - 11:30 AM: Create YAML definitions
- [ ] 11:30 AM - 12:00 PM: Integration tests

### Thursday (Dec 11) - 2 Hours (Optional)
- [ ] 8:00 AM - 9:00 AM: Unit tests for new workflows
- [ ] 9:00 AM - 10:00 AM: Performance benchmarks

---

## Risk Mitigation

**Risk:** ToolCallingWorkflow too complex
- **Mitigation:** Start simple, add features incrementally
- **Fallback:** Keep Examples 06 unchanged if needed

**Risk:** YAML parsing errors
- **Mitigation:** Comprehensive error messages
- **Fallback:** Can always use hardcoded workflows

**Risk:** Breaking existing examples
- **Mitigation:** Create NEW refactored files, keep originals
- **Fallback:** Easy rollback to master if needed

---

## Phase 3 Preview (After Phase 2)

Once Phase 2 is complete:
- Examples 08, 09 (autonomous flow patterns)
- Examples 10, 11, 12 (advanced patterns)
- Examples 13, 14, 15 (specialized patterns)
- Full test coverage across all examples
- Performance optimization
- Production documentation

---

## Success Criteria for Phase 2

✅ **Code Quality**
- [ ] ToolCallingWorkflow works with Examples 06
- [ ] ConditionalWorkflow works with branching logic
- [ ] All code follows SOLID principles
- [ ] Full docstrings and type hints

✅ **Functionality**
- [ ] Example 06 refactored and working
- [ ] Example 07 integrated into new location
- [ ] All original functionality preserved
- [ ] Metrics improved over Phase 1

✅ **Testing**
- [ ] Unit tests for new workflows
- [ ] Integration tests for examples
- [ ] No regression in original examples
- [ ] >90% test coverage

✅ **Documentation**
- [ ] YAML format documented
- [ ] ToolCallingWorkflow tutorial
- [ ] ConditionalWorkflow tutorial
- [ ] Migration guide for Examples 8-15

---

**Status: Ready to Begin Phase 2 Implementation**

Starting with ToolCallingWorkflow creation next...
