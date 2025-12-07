# Example 11 - N-Decision Router Updates

## v3.0.1 Migration Complete ✅

### Changes Applied

1. **Full Compiler Pipeline**
   - ✅ Changed from `load_manifest()` to `parse()` → `PassManager` → `runtime.initialize()`
   - ✅ Uses optimization passes for better performance

2. **MessagesState Format**
   - ✅ Updated input to use `MessagesState` format
   - ✅ Input now: `{"messages": [HumanMessage(content="...")]}`

3. **Router-Based Architecture**
   - ✅ Changed `analyze_query` to use `router_ref: decision_router`
   - ✅ Changed `format_response` from task to router with `router_ref: formatter_router`
   - ✅ Added router definitions with specialized system messages

4. **Route Keys (v3.0.0)**
   - ✅ Updated edges to use `route:` conditions instead of `expression:`
   - ✅ Routes: `data_quality`, `growth_experiment`, `customer_support`, `reporting`
   - ✅ Simplified routing logic (substring matching)

5. **Observability Integration**
   - ✅ Uses `setup_observability()` helper
   - ✅ Uses `trace_runtime_execution()` context manager
   - ✅ Full OpenTelemetry tracing enabled

6. **Enhanced Testing**
   - ✅ Tests all 4 routing paths
   - ✅ Improved output formatting
   - ✅ Shows routing decision and formatted response

### Execution Flow

```
User Query
    ↓
analyze_query (router)
    ↓
[Route Decision]
    ↓
┌───────────┬───────────┬───────────┬───────────┐
│           │           │           │           │
data_quality  growth_    customer_   reporting
_exec        experiment  support_    _exec
             _exec       _exec
│           │           │           │
└───────────┴───────────┴───────────┴───────────┘
                    ↓
            format_response (router)
                    ↓
            Final Response
```

### Router Configuration

**Decision Router:**
- Classifies queries into 4 categories
- Returns single word: `data_quality`, `growth_experiment`, `customer_support`, or `reporting`
- Uses `ollama://qwen3:8b`

**Formatter Router:**
- Summarizes tool output
- Makes responses concise and actionable
- Uses `ollama://qwen3:8b`

### Key Learnings Applied

- ✅ Standard runtime pattern (parse → optimize → execute)
- ✅ MessagesState input format
- ✅ Route keys for simplified routing (v3.0.0)
- ✅ Router for both classification and formatting
- ✅ Convergent pattern (all paths → formatter)
- ✅ N-way routing (4 decision paths)

### Testing

Run with:
```bash
python run_agent.py
```

Tests all 4 routes:
1. **Data Quality**: "Check data quality for user reports"
2. **Growth Experiment**: "Run an A/B test for the new feature"
3. **Customer Support**: "Help a customer with their billing issue"
4. **Reporting**: "Generate weekly metrics report"

**Note:** MCP tools may not be available locally, but routing and formatting work correctly.

---

**Status:** ✅ Fully working with v3.0.1

