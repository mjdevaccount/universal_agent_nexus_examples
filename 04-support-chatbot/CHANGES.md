# Example 04 - Support Chatbot Updates

## v3.0.1 Migration Complete ✅

### Changes Applied

1. **Full Compiler Pipeline**
   - ✅ Changed from `load_manifest()` to `parse()` → `PassManager` → `runtime.initialize()`
   - ✅ Uses optimization passes for better performance

2. **MessagesState Format**
   - ✅ Updated input to use `MessagesState` format
   - ✅ Input now: `{"messages": [HumanMessage(content="...")]}`

3. **Router-Based Response Generation**
   - ✅ Changed `generate_response` from `task` to `router`
   - ✅ Uses `response_generator` router for actual LLM response generation
   - ✅ Task nodes are passthrough in v3.0.0, routers generate content

4. **Sentiment Router**
   - ✅ Changed `sentiment_check` from `task` to `router`
   - ✅ Uses `sentiment_router` with route keys ("escalate" or "handle")
   - ✅ Replaced expression evaluation with simple route matching

5. **Route Keys (v3.0.0)**
   - ✅ All edges use `route:` keys instead of `expression:`
   - ✅ Intent router returns single words: faq, technical, billing, complaint, other
   - ✅ Sentiment router returns: escalate or handle

6. **Observability Integration**
   - ✅ Uses `setup_observability()` helper
   - ✅ Uses `trace_runtime_execution()` context manager
   - ✅ Full OpenTelemetry tracing enabled

7. **Enhanced Output**
   - ✅ Improved message extraction from result structure
   - ✅ Displays intent classification
   - ✅ Shows formatted bot response

### Execution Flow

```
User Query
    ↓
classify_intent (router)
    ↓
┌───┴───┬──────┬──────┬──────┬────────┐
│       │      │      │      │        │
FAQ   Technical Billing Complaint Other
│       │      │      │      │
│       ↓      │      ↓      │
│   troubleshoot │  sentiment │
│       │      │      │      │
│       └──────┴──────┴──────┘
│              │
│       generate_response (router)
│              │
└──────────────┘
```

### Key Learnings Applied

- ✅ Standard runtime pattern (parse → optimize → execute)
- ✅ MessagesState input format
- ✅ Router for content generation (not just routing decisions)
- ✅ Route keys for simple matching
- ✅ Multiple routers in one graph
- ✅ Convergent paths to response generation

### Testing

Run with:
```bash
python run_agent.py
```

Test all intents:
```bash
python test_intents.py
```

Expected output:
- Intent classification displayed
- Execution path shown
- Formatted bot response

---

**Status:** ✅ Fully working with v3.0.1

