# v3.0.0 Migration Guide

**Quick reference for migrating from v2.x to v3.0.0+**

---

## Breaking Changes

### 1. MessagesState (Required)

**v2.x (Custom AgentState):**
```python
class AgentState(TypedDict):
    context: Dict[str, Any]
    history: Annotated[list[BaseMessage], operator.add]
    current_node: str

input_data = {
    "context": {"query": "..."},
    "history": []
}
```

**v3.0.0 (MessagesState):**
```python
from langchain_core.messages import HumanMessage

input_data = {
    "messages": [
        HumanMessage(content="Your input here")
    ]
}
```

### 2. Route Keys (Replaces Expressions)

**v2.x (Expression Evaluation):**
```yaml
edges:
  - from_node: router
    to_node: action_a
    condition:
      expression: "last_response.strip().lower() == 'safe'"
```

**v3.0.0 (Route Keys):**
```yaml
edges:
  - from_node: router
    to_node: action_a
    condition:
      route: "safe"  # Simple substring matching
```

**How It Works:**
- Router LLM returns response (e.g., "safe")
- Compiler does: `route_key.lower() in response.lower()`
- First match wins

### 3. Synchronous Compiler

**v2.x:**
```python
state_graph = await compiler.compile_async(manifest, graph_name)
```

**v3.0.0:**
```python
state_graph = compiler.compile(manifest, graph_name)  # No await
```

### 4. Router Reference Format

**Both formats work (v2.0.5+):**
```yaml
# Nested (standard)
router:
  name: "my_router"

# Flat (also works)
router_ref: "my_router"
```

---

## Migration Checklist

- [ ] Update input format to `MessagesState`
- [ ] Replace `expression:` with `route:` in edges
- [ ] Remove `await` from `compiler.compile()` calls
- [ ] Update router system messages to return single words
- [ ] Test route key matching (case-insensitive substring)
- [ ] Update runtime initialization to use full compiler pipeline

---

## Example Migration

**Before (v2.x):**
```python
input_data = {
    "context": {
        "query": "Classify this content"
    }
}

# In manifest.yaml
edges:
  - from_node: router
    to_node: approve
    condition:
      expression: "output == 'safe'"
```

**After (v3.0.0):**
```python
from langchain_core.messages import HumanMessage

input_data = {
    "messages": [
        HumanMessage(content="Classify this content")
    ]
}

# In manifest.yaml
edges:
  - from_node: router
    to_node: approve
    condition:
      route: "safe"
```

---

## Benefits of v3.0.0

1. **57% Code Reduction** - Simpler compiler, less to maintain
2. **Standard State** - Uses LangGraph's MessagesState (battle-tested)
3. **Faster Routing** - Simple string matching vs expression evaluation
4. **Better Performance** - Removed eval() security concerns

---

**See Also:** `API_REFERENCE.md` for detailed patterns and examples.

