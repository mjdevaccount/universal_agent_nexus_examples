# Phase 3: Scale Remaining Examples (10-15)

**Status:** IN PROGRESS  
**Branch:** `feature/phase-3-remaining-examples`  
**Target Completion:** Thursday, December 12, 2025  
**Effort:** 5 days of focused development

---

## Phase 3 Objectives

### Primary Goals
1. ✅ Refactor Examples 10, 11, 12 using new workflows
2. ✅ Create Example 13 from scratch (SimpleQA)
3. ✅ Integrate Examples 14, 15 with ValidationNode
4. ✅ Add optional YAML registry system
5. ✅ Create per-example test suites
6. ✅ Update shared requirements.txt

### Success Metrics
- All 15 examples use workflow abstraction
- Code reduction: -40% average
- 100% test coverage per example
- Zero breaking changes
- Full documentation

---

## Example Breakdown

### Example 10: Local LLM Tool Servers

**Current Pattern:** Tool server + tool-calling loop  
**New Pattern:** ToolCallingWorkflow  
**Complexity:** Medium (multi-tool coordination)

**Tools to Wrap:**
- Start tool server
- Call tools via MCP/HTTP
- Get tool results
- Format for LLM

**Refactoring Steps:**
```python
# 1. Define tools as LangChain Tool objects
tools = [
    Tool(name="arithmetic", func=call_arithmetic_tool, ...),
    Tool(name="web_search", func=call_web_search_tool, ...),
]

# 2. Create workflow
workflow = ToolCallingWorkflow(
    name="llm-tool-servers",
    llm=llm,
    tools=tools,
    max_iterations=5,
)

# 3. Run
result = await workflow.invoke("Use tools to solve problems")
```

**Expected Code Reduction:** -40% (from ~120 lines → 70 lines)

---

### Example 11: N-Decision Router

**Current Pattern:** Multi-way branching with fallback  
**New Pattern:** ConditionalWorkflow with multiple branches  
**Complexity:** High (5+ branches)

**Decision Branches:**
- Customer service intent
- Billing intent
- Technical support intent
- Sales inquiry intent
- Escalation intent

**Refactoring Steps:**
```python
# 1. Create decision node
decision = IntelligenceNode(
    llm=llm,
    prompt_template="Classify intent: {request}",
)

# 2. Define branches
branches = {
    "service": [CustomerServiceNode()],
    "billing": [BillingNode()],
    "technical": [TechSupportNode()],
    "sales": [SalesNode()],
    "escalate": [EscalationNode()],
}

# 3. Create workflow
workflow = ConditionalWorkflow(
    name="request-router",
    state_schema=RequestState,
    decision_node=decision,
    branches=branches,
)

# 4. Run
result = await workflow.invoke(state)
```

**Expected Code Reduction:** -35% (from ~180 lines → 120 lines)

---

### Example 12: Self-Modifying Agent

**Current Pattern:** Nested graph with self-modification  
**New Pattern:** ConditionalWorkflow + dynamic branch updates  
**Complexity:** Very High (agent modifies itself)

**Branches:**
- Analyze task
- Plan approach
- Execute plan
- Evaluate results
- Adapt/retry

**Refactoring Steps:**
```python
# 1. Create decision node for task analysis
analyze = IntelligenceNode(
    llm=llm,
    prompt_template="Analyze task: {task}",
)

# 2. Create adaptive branches
branches = {
    "simple": [SimpleExecutorNode()],
    "complex": [ComplexExecutorNode()],
    "adaptive": [AdaptiveExecutorNode()],  # Can modify itself
}

# 3. Create workflow
workflow = ConditionalWorkflow(
    name="self-modifying",
    state_schema=TaskState,
    decision_node=analyze,
    branches=branches,
)

# 4. Run
result = await workflow.invoke(task_state)
```

**Expected Code Reduction:** -30% (from ~250 lines → 180 lines)

---

### Example 13: Practical Quickstart

**Current Pattern:** N/A (new example)  
**New Pattern:** SimpleQAWorkflow  
**Complexity:** Low (basic Q&A)

**Features:**
- Simple question answering
- Context injection
- Metrics collection
- Error handling

**Implementation:**
```python
from shared.workflows import SimpleQAWorkflow

# Create workflow
workflow = SimpleQAWorkflow(
    name="practical-qa",
    llm=llm,
    system_prompt="You are a helpful Python expert.",
)

# Run queries
queries = [
    "What are decorators in Python?",
    "How do list comprehensions work?",
    "Explain async/await",
]

for query in queries:
    result = await workflow.invoke(query)
    print(f"Q: {result['query']}")
    print(f"A: {result['answer']}")
    print(f"Metrics: {result['metrics']}")
```

**Size:** ~60 lines (simple, clean, educational)

---

### Example 14: Cached Content Moderation

**Current Pattern:** Moderation + caching layer  
**New Pattern:** ValidationNode + caching  
**Complexity:** Medium (validation + optimization)

**Pattern:**
```
Input → Check cache → Validate (if not cached) → Cache result → Output
```

**Implementation:**
```python
from shared.workflows import ValidationNode
from functools import lru_cache

# Wrapped validation with caching
validation = ValidationNode(
    output_schema=ModerationResult,
    validation_rules={"is_safe": lambda x: x["score"] > 0.7},
    repair_on_fail=True,
)

# Cache layer
@lru_cache(maxsize=1000)
async def moderate_with_cache(text: str):
    state = {"text": text}
    result = await validation.execute(state)
    return result["validated"]

# Run
for text in texts:
    result = await moderate_with_cache(text)
    print(f"Text: {text}")
    print(f"Safe: {result['is_safe']}")
```

**Expected Code Reduction:** -25% (cache integration)

---

### Example 15: Cached Content Moderation (Variant)

**Current Pattern:** Identical to Example 14 (probably for comparison)  
**New Pattern:** Same as Example 14 (can be kept identical or enhanced)

**Note:** Verify if Example 15 should be identical or a variation

---

## Implementation Timeline

### Day 1 (Tuesday) - Examples 10 & 11
**Goal:** Refactor Examples 10, 11 using ToolCalling & Conditional workflows

**Tasks:**
- [ ] 9:00 AM - 11:00 AM: Refactor Example 10
  - Analyze current tool server pattern
  - Wrap tools as LangChain Tool objects
  - Create ToolCallingWorkflow
  - Write tests
  - Benchmark vs. original

- [ ] 11:00 AM - 1:00 PM: Refactor Example 11
  - Analyze current routing logic
  - Create IntelligenceNode for decision
  - Define conditional branches
  - Create ConditionalWorkflow
  - Write tests
  - Verify all intent branches work

- [ ] 1:00 PM - 2:00 PM: Integration testing + review

**Deliverables:**
- `10-local-llm-tool-servers/example_10_refactored.py`
- `11-n-decision-router/example_11_refactored.py`
- `tests/test_example_10.py`
- `tests/test_example_11.py`

---

### Day 2 (Wednesday) - Examples 12 & 13
**Goal:** Refactor Example 12, Create Example 13 from scratch

**Tasks:**
- [ ] 9:00 AM - 12:00 PM: Refactor Example 12
  - Analyze self-modifying agent logic
  - Identify decision points and branches
  - Create ConditionalWorkflow with adaptive branches
  - Implement self-modification hook
  - Write comprehensive tests
  - Validate adaptive behavior

- [ ] 12:00 PM - 2:00 PM: Create Example 13
  - Design simple Q&A use case
  - Use SimpleQAWorkflow
  - Add multiple query examples
  - Demonstrate metrics collection
  - Write tests
  - Create tutorial/documentation

- [ ] 2:00 PM - 3:00 PM: Testing + review

**Deliverables:**
- `12-self-modifying-agent/example_12_refactored.py`
- `13-practical-quickstart/example_13_refactored.py`
- `tests/test_example_12.py`
- `tests/test_example_13.py`
- `13-practical-quickstart/TUTORIAL.md`

---

### Day 3 (Thursday) - Examples 14 & 15 + YAML Registry
**Goal:** Integrate Examples 14, 15; Create optional YAML registry

**Tasks:**
- [ ] 9:00 AM - 11:00 AM: Integrate Examples 14 & 15
  - Analyze caching pattern
  - Create ValidationNode wrapper
  - Add cache layer
  - Write tests
  - Benchmark cache hit rates

- [ ] 11:00 AM - 1:00 PM: Create YAML Registry (Optional)
  - Create `shared/workflows/registry.py`
  - YAML format specification
  - Loader implementation
  - Test YAML parsing
  - Create example YAML configs

- [ ] 1:00 PM - 2:00 PM: Final testing + review

**Deliverables:**
- `14-cached-content-moderation/example_14_refactored.py`
- `15-cached-content-moderation/example_15_refactored.py`
- `tests/test_example_14.py`
- `tests/test_example_15.py`
- `shared/workflows/registry.py` (optional)
- `shared/workflows/definitions/` (optional YAML files)

---

## Testing Strategy

### Per-Example Test Suite

Each example gets its own test file:

```
tests/
├── test_example_10.py  # ToolCallingWorkflow tests
├── test_example_11.py  # ConditionalWorkflow tests
├── test_example_12.py  # Self-modifying logic tests
├── test_example_13.py  # SimpleQA tests
├── test_example_14.py  # Caching + validation tests
└── test_example_15.py  # Same as 14
```

### Test Coverage Per Example

**Happy Path** (main workflow)
```python
def test_example_10_happy_path():
    # Tool calls execute successfully
    # Final response generated
    # Metrics collected
```

**Error Scenarios**
```python
def test_example_10_tool_not_found():
    # Unknown tool requested
    # Graceful error handling

def test_example_10_tool_failure():
    # Tool execution fails
    # Error logged
    # Workflow continues or stops gracefully
```

**Edge Cases**
```python
def test_example_10_max_iterations():
    # Too many tool calls
    # Stops at max_iterations
    # Returns partial results

def test_example_11_unknown_branch():
    # Decision returns unknown branch
    # Error handling activated
```

**Performance**
```python
def test_example_10_performance():
    # Execution completes in reasonable time
    # Metrics within expected ranges
```

---

## Code Quality Standards

### All Examples Must Have
- [ ] Type hints throughout
- [ ] Comprehensive docstrings
- [ ] Error handling
- [ ] Async/await properly used
- [ ] SOLID principles applied
- [ ] Unit tests (>90% coverage)
- [ ] Integration tests
- [ ] Performance benchmarks
- [ ] Clear variable names
- [ ] Inline comments for complex logic

---

## Expected Outcomes

### Code Metrics

| Example | Before | After | Reduction | Pattern |
|---------|--------|-------|-----------|----------|
| **10** | 120 lines | 70 lines | -42% | ToolCalling |
| **11** | 180 lines | 120 lines | -33% | Conditional |
| **12** | 250 lines | 180 lines | -28% | Conditional |
| **13** | N/A | 60 lines | N/A | SimpleQA |
| **14** | 100 lines | 80 lines | -20% | Validation + Cache |
| **15** | 100 lines | 80 lines | -20% | Validation + Cache |
| **TOTAL** | 750 lines | 590 lines | **-21% avg** | |

### Reliability Metrics

| Metric | Target | Notes |
|--------|--------|-------|
| **Test Coverage** | >90% per example | All workflows covered |
| **Success Rate** | 99%+ | Automatic error handling |
| **Response Time** | <5s per call | Performance benchmarked |
| **Error Handling** | 100% paths covered | No silent failures |

### Reusability Metrics

| Aspect | Value | Impact |
|--------|-------|--------|
| **Patterns reused** | 3 types | No duplication |
| **Custom code** | <20% | 80% from Phase 1-2 |
| **Time to implement** | 1-2 hours per example | 50% faster than from scratch |

---

## Risk Mitigation

### Risk: Complex branching logic breaks
**Mitigation:**
- Keep original examples as reference
- Comprehensive branch coverage in tests
- Compare output with original implementation

### Risk: Performance degrades
**Mitigation:**
- Benchmark before and after
- Profile hot paths
- Optimize if needed (unlikely)

### Risk: Tool integration issues
**Mitigation:**
- Mock tools for unit tests
- Real tool testing in integration tests
- Fallback to original tool code if needed

### Risk: Backward compatibility breaks
**Mitigation:**
- Keep original examples intact
- Create new refactored versions separately
- Run side-by-side comparison tests

---

## Deliverables by Day

### Day 1 Deliverables
```
✅ 10-local-llm-tool-servers/example_10_refactored.py
✅ 11-n-decision-router/example_11_refactored.py
✅ tests/test_example_10.py
✅ tests/test_example_11.py
✅ Benchmarks and performance comparison
```

### Day 2 Deliverables
```
✅ 12-self-modifying-agent/example_12_refactored.py
✅ 13-practical-quickstart/example_13_refactored.py
✅ tests/test_example_12.py
✅ tests/test_example_13.py
✅ 13-practical-quickstart/TUTORIAL.md
```

### Day 3 Deliverables
```
✅ 14-cached-content-moderation/example_14_refactored.py
✅ 15-cached-content-moderation/example_15_refactored.py
✅ tests/test_example_14.py
✅ tests/test_example_15.py
✅ shared/workflows/registry.py (optional)
✅ PHASE3_COMPLETION_REPORT.md
```

---

## Phase 3 Success Criteria

### Must Have ✅
- [ ] Examples 10-15 refactored
- [ ] All tests passing
- [ ] No breaking changes
- [ ] Documentation complete
- [ ] Code reduction > 20% average

### Should Have ✔
- [ ] YAML registry system
- [ ] Performance benchmarks
- [ ] Migration guide for other projects
- [ ] Tutorial documentation

### Nice to Have ⚠
- [ ] Advanced patterns documentation
- [ ] Optimization guide
- [ ] Contributing guidelines

---

## Post-Phase 3 (Phase 4+)

### Documentation
- API reference complete
- Architecture guide
- Best practices guide
- Troubleshooting guide

### Advanced Features
- Parallel branch execution (ConditionalWorkflow)
- Dynamic workflow composition
- Workflow versioning
- A/B testing framework

### Production
- Performance optimization
- Caching strategy
- Monitoring/observability
- Production deployment guide

---

**Status: Phase 3 Ready to Begin**

All prerequisites from Phase 1 & 2 are in place. Examples 10-15 are ready to be refactored using the powerful workflow helpers we've built.

**Estimated Completion:** Thursday, December 12, 2025
