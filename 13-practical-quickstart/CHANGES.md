# Example 13 - Practical Quickstart Updates

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
   - ✅ Routes: `billing`, `technical`, `account`
   - ✅ Simplified routing logic (substring matching)

5. **Observability Integration**
   - ✅ Uses `setup_observability()` helper
   - ✅ Uses `trace_runtime_execution()` context manager
   - ✅ Full OpenTelemetry tracing enabled

6. **Enhanced Testing**
   - ✅ Tests all 3 routing paths
   - ✅ Improved output formatting
   - ✅ Shows routing decision and customer response

### Execution Flow

```
Customer Query
    ↓
analyze_query (router)
    ↓
[Route Decision]
    ↓
┌───────────┬───────────┬───────────┐
│           │           │           │
billing_exec  technical_exec  account_exec
│           │           │           │
└───────────┴───────────┴───────────┘
            ↓
    format_response (router)
            ↓
    Customer Response
```

### Router Configuration

**Decision Router:**
- Classifies customer issues into 3 categories: `billing`, `technical`, `account`
- Returns single word for simple routing
- Uses `ollama://qwen3:8b`

**Formatter Router:**
- Formats tool results into empathetic customer responses
- Makes responses helpful, clear, and professional
- Uses `ollama://qwen3:8b`

### Key Learnings Applied

- ✅ Standard runtime pattern (parse → optimize → execute)
- ✅ MessagesState input format
- ✅ Route keys for simplified routing (v3.0.0)
- ✅ Router for both classification and formatting
- ✅ Convergent pattern (all paths → formatter)
- ✅ 3-way routing (billing, technical, account)

### Testing

Run with:
```bash
python run_agent.py
```

Tests all 3 routes:
1. **Account**: "I can't log into my account"
2. **Billing**: "My subscription payment failed"
3. **Technical**: "The app keeps crashing on startup"

**Note:** MCP tools may not be available locally, but routing and formatting work correctly.

---

**Status:** ✅ Fully working with v3.0.1

