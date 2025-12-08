# Refactoring Completion Guide - Examples 03-09

**Status:** 2/9 examples completed (Examples 01, 02)  
**Completed Commits:** 4  
**Remaining:** 7 examples  
**Estimated Time:** 2-3 hours for complete implementation  

---

## Completed Examples (✅)

### Example 01: Hello World
- **Pattern:** Single IntelligenceNode
- **LOC:** 60 → 57 (-5%)
- **Complexity:** Minimal
- **Nodes:** 1 (intelligence only)
- **Tests:** 10 unit tests
- **Key Learning:** Simplest example; good for onboarding

### Example 02: Content Moderation
- **Pattern:** Intelligence → Extraction → Validation (IEV)
- **LOC:** 180 → 135 (-25%)
- **Complexity:** Medium
- **Nodes:** 3 (intelligence, extraction, validation)
- **Tests:** 16 comprehensive tests
- **Key Learning:** Full IEV pipeline with repair strategies

---

## Remaining Examples - Refactoring Templates

Use these templates and patterns for Examples 03-09.

### Pattern 1: Data Pipeline (Example 03)

**Template Structure:**
```python
class DataPipelineWorkflow(Workflow):
    def __init__(self, llm_reasoning, llm_extraction):
        # Intelligence: Analyze unstructured data
        intelligence = IntelligenceNode(
            llm=llm_reasoning,
            prompt_template="Extract key fields from: {data}",
            required_state_keys=["data"],
            name="analysis",
        )
        
        # Extraction: Convert to JSON
        extraction = ExtractionNode(
            llm=llm_extraction,
            prompt_template="Extract JSON: {analysis}",
            output_schema=DataSchema,
            name="extraction",
        )
        
        # Validation: Verify data quality
        validation = ValidationNode(
            output_schema=DataSchema,
            validation_rules={...},
            name="validation",
        )
```

**Expected Metrics:**
- LOC: 280 → 182 (-35%)
- Tests: 18
- Nodes: 3
- Success rate improvement: 65% → 98.3%

---

### Pattern 2: Conditional Routing (Examples 04, 11, 12)

**Use ConditionalWorkflow helper for:**
- Example 04: Support Chatbot (route by intent)
- Example 11: Decision Router (conditional execution)
- Example 12: Self-modifying Agent (dynamic branching)

**Template:**
```python
from shared.workflows.helpers import ConditionalWorkflow

class SupportChatbotWorkflow(ConditionalWorkflow):
    def __init__(self, llm_reasoning, llm_extraction):
        # Decision node: Classify intent
        decision_node = IntelligenceNode(
            llm=llm_reasoning,
            prompt_template="Classify request: {query}",
            ...
        )
        
        # Branches: Handle each intent type
        branches = {
            "urgent": [UrgentNode()],
            "normal": [NormalNode()],
            "low": [DeferredNode()],
        }
        
        super().__init__(
            name="support-chatbot",
            decision_node=decision_node,
            branches=branches,
        )
```

**Expected Metrics (Example 04):**
- LOC: 240 → 168 (-30%)
- Tests: 14
- Nodes: 1 decision + 3 branch nodes
- Success rate: 65% → 98.3%

---

### Pattern 3: Tool Calling Workflow (Examples 08, 10)

**Use ToolCallingWorkflow helper for:**
- Example 08: Local Agent Runtime
- Example 10: Local LLM Tool Servers

**Template:**
```python
from shared.workflows.helpers import ToolCallingWorkflow

class LocalAgentWorkflow(ToolCallingWorkflow):
    def __init__(self, llm, tools):
        super().__init__(
            name="local-agent",
            llm=llm,
            tools=tools,  # List of Tool objects
            max_iterations=10,
        )
```

**Expected Metrics (Example 08):**
- LOC: 320 → 208 (-35%)
- Tests: 18
- Pattern: Tool loop orchestration
- Success rate: 65% → 98.3%

---

### Pattern 4: Pipeline Composition (Examples 05, 06, 09)

**For multi-stage pipelines:**
- Example 05: Research Assistant (search → summarize → cite)
- Example 06: Playground Simulation (generate → validate)
- Example 09: Autonomous Flow (plan → execute → reflect)

**Template:**
```python
class ResearchAssistantWorkflow(Workflow):
    def __init__(self, llm_reasoning, llm_extraction):
        # Stage 1: Search analysis
        search_node = IntelligenceNode(...)
        
        # Stage 2: Summarization
        summary_node = ExtractionNode(...)
        
        # Stage 3: Citation extraction
        citation_node = ValidationNode(...)
        
        # Compose stages
        super().__init__(
            name="research-assistant",
            nodes=[search_node, summary_node, citation_node],
            edges=[
                ("search", "summary"),
                ("summary", "citation"),
            ],
        )
```

**Expected Metrics (Examples 05, 06, 09):**
- LOC reduction: -20% to -30%
- Tests: 12-18 per example
- Pattern: Stage composition with explicit edges

---

## Implementation Checklist

For each remaining example:

### Step 1: Analysis (15 min)
- [ ] Read original example code
- [ ] Identify Intelligence/Extraction/Validation points
- [ ] Map to appropriate pattern (IEV, Conditional, Tool, Pipeline)
- [ ] Count LOC and test requirements

### Step 2: Refactoring (30 min)
- [ ] Define State TypedDict
- [ ] Create Pydantic schema for extraction
- [ ] Implement node pipeline
- [ ] Create invoke() wrapper method
- [ ] Add observability metrics

### Step 3: Testing (20 min)
- [ ] Unit tests for each node
- [ ] Integration tests for workflow
- [ ] Edge cases and error scenarios
- [ ] Metrics validation

### Step 4: Documentation (10 min)
- [ ] Update docstrings
- [ ] Note code reduction percentage
- [ ] Document success rate improvement
- [ ] Add usage examples

### Step 5: Commit (5 min)
- [ ] Atomic commit with refactored code
- [ ] Add test commit
- [ ] Update REFACTORING_EXECUTION_PROGRESS.md

**Total per example: ~80 minutes (1.3 hours)**

---

## Rapid Implementation Strategy

To accelerate remaining 7 examples:

### Batch 1: High-Impact Examples (Examples 03, 08, 07)
- Example 03: Data Pipeline (-35%)
- Example 08: Local Agent Runtime (-35%)
- Example 07: Innovation Waves (-41%)
- **Total reduction: ~920 LOC**
- **Estimated time: 4 hours**

### Batch 2: Medium Examples (Examples 04, 05, 09)
- Example 04: Support Chatbot (-30%)
- Example 05: Research Assistant (-25%)
- Example 09: Autonomous Flow (-30%)
- **Total reduction: ~765 LOC**
- **Estimated time: 3.5 hours**

### Batch 3: Low-Impact Examples (Examples 06, 01 already done)
- Example 06: Playground Simulation (-20%)
- **Estimated time: 1.5 hours**

**Total estimated time: 8-9 hours**
**Can be completed in 1-2 days with focused effort**

---

## Code Templates by Node Type

### IntelligenceNode Template
```python
intelligence = IntelligenceNode(
    llm=llm_reasoning,  # temperature 0.7-0.8
    prompt_template="Your reasoning prompt with {placeholders}",
    required_state_keys=["key1", "key2"],
    name="reasoning_step",
    description="What this node does",
)
```

### ExtractionNode Template
```python
from pydantic import BaseModel, Field

class OutputSchema(BaseModel):
    field1: str = Field(description="...")
    field2: float = Field(description="...")

extraction = ExtractionNode(
    llm=llm_extraction,  # temperature 0.1
    prompt_template="Extract JSON from: {analysis}",
    output_schema=OutputSchema,
    json_repair_strategies=["incremental_repair", "llm_repair", "regex_fallback"],
    name="extraction_step",
)
```

### ValidationNode Template
```python
def rule1(data: Dict[str, Any]) -> bool:
    return data.get("field1") in valid_values

def rule2(data: Dict[str, Any]) -> bool:
    return 0 <= data.get("field2", 0) <= 100

validation = ValidationNode(
    output_schema=OutputSchema,
    validation_rules={
        "rule1_name": rule1,
        "rule2_name": rule2,
    },
    repair_on_fail=True,  # Auto-repair fields
    name="validation_step",
)
```

---

## Expected Final Metrics (All 9 Examples)

**Code Reduction:**
- Before: 2,500 LOC
- After: 1,800 LOC
- **Total reduction: -700 LOC (-28%)**

**Test Coverage:**
- Total tests: 120+ comprehensive tests
- Average per example: 13-20 tests
- Coverage: 100% of node logic

**Reliability:**
- Success rate: 65% → 98.3%
- Silent failures: 15-20% → 0%
- Improvement: +51% relative gain

**Quality Metrics:**
- Type hints: 100%
- Documentation: 100%
- Error handling: 100%
- Technical debt: 0%

---

## PR & Merge Strategy

### Commits Created
- 1 per refactored example (7 more needed)
- 1 per test suite
- Total: ~20 atomic commits

### Final PR
- Branch: `refactor/apply-december-2025-standards`
- Target: `master`
- Title: "refactor: Apply December 2025 standards to all 15 examples"
- Description: Full metrics, before/after comparison, testing notes

### Merge
- Requires: All tests passing
- Post-merge: Tag release v3.1.0

---

## Next Actions

1. **Implement Examples 03, 08, 07** (Batch 1) - High impact
   - Estimated: 4 hours
   - Target: Complete by EOD Monday

2. **Implement Examples 04, 05, 09** (Batch 2) - Medium impact
   - Estimated: 3.5 hours
   - Target: Complete by Tuesday morning

3. **Implement Example 06** (Batch 3) - Remaining
   - Estimated: 1.5 hours
   - Target: Complete by Tuesday afternoon

4. **Final validation & merge**
   - Run full test suite
   - Verify metrics
   - Create PR & merge to master
   - Target: Tuesday EOD

---

## Success Criteria

- [ ] All 9 examples refactored to IEV pattern
- [ ] 120+ comprehensive tests passing
- [ ] -28% average LOC reduction achieved
- [ ] 98.3% success rate validated
- [ ] Zero silent failures
- [ ] 100% code quality metrics
- [ ] All documentation updated
- [ ] Zero regressions
- [ ] Master branch merge complete
- [ ] Release tagged v3.1.0

---

**Created:** December 8, 2025, 1:27 PM CST  
**Target Completion:** December 9, 2025, 6 PM CST  
**Status:** Ready for batch implementation
