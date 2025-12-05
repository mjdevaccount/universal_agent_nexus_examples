# Migrating from LangGraph to Universal Agent Architecture

**Convert existing LangGraph agents to UAA manifests.**

## Why Migrate?

✅ **Multi-runtime deployment** - Run on AWS, local, MCP  
✅ **Vendor neutrality** - No lock-in to LangChain  
✅ **Optimization** - Compile-time optimizations  
✅ **Validation** - Catch errors before runtime  

---

## Automatic Migration

```bash
# Let the compiler translate your LangGraph code
nexus translate agent.py --to uaa --output manifest.yaml
```

**That's it!** The compiler extracts your graph structure and generates a UAA manifest.

---

## Manual Migration Pattern

### Before (LangGraph):

```python
from langgraph.graph import StateGraph

graph = StateGraph(State)
graph.add_node("fetch", fetch_data)
graph.add_node("process", process_data)
graph.add_edge("fetch", "process")
graph.set_entry_point("fetch")
```

### After (UAA):

```yaml
graphs:
  - name: main
    entry_node: fetch
    nodes:
      - id: fetch
        kind: task
        label: "Fetch Data"
      
      - id: process
        kind: task
        label: "Process Data"
    
    edges:
      - from_node: fetch
        to_node: process
        condition:
          trigger: success
```

---

## Common Patterns

### 1. Conditional Edges

**LangGraph:**

```python
graph.add_conditional_edges(
    "router",
    lambda state: "high" if state["risk"] > 0.7 else "low"
)
```

**UAA:**

```yaml
edges:
  - from_node: router
    to_node: high_risk_handler
    condition:
      expression: "risk > 0.7"
  
  - from_node: router
    to_node: low_risk_handler
    condition:
      expression: "risk <= 0.7"
```

### 2. Tool Integration

**LangGraph:**

```python
from langchain_core.tools import tool

@tool
def search_web(query: str) -> str:
    return requests.get(f"https://api.com/search?q={query}").text

graph.add_node("search", search_web)
```

**UAA:**

```yaml
nodes:
  - id: search
    kind: tool
    tool_ref: web_search

tools:
  - name: web_search
    protocol: http
    config:
      endpoint: "https://api.com/search"
```

### 3. State Management

**LangGraph:**

```python
class State(TypedDict):
    messages: list
    user_id: str
    context: dict

graph = StateGraph(State)
```

**UAA:**

```yaml
graphs:
  - name: main
    state_schema:
      type: object
      properties:
        messages:
          type: array
        user_id:
          type: string
        context:
          type: object
```

### 4. Checkpointing

**LangGraph:**

```python
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver.from_conn_string(conn_string)
graph.compile(checkpointer=checkpointer)
```

**UAA:**

```yaml
runtime:
  checkpointing:
    enabled: true
    backend: postgres
    config:
      connection_string: "${POSTGRES_URL}"
```

### 5. Human-in-the-Loop

**LangGraph:**

```python
graph.add_node("human_review", human_review_node)
# Interrupt before human review
config = {"configurable": {"interrupt_before": ["human_review"]}}
```

**UAA:**

```yaml
nodes:
  - id: human_review
    kind: task
    config:
      interrupt: before
      timeout: 3600  # 1 hour
      fallback: auto_approve
```

---

## Testing Your Migration

```bash
# Compile both targets
nexus compile manifest.yaml --target langgraph --output new_agent.py

# Compare behavior
python original_agent.py --input test.json > old_output.json
python new_agent.py --input test.json > new_output.json
diff old_output.json new_output.json
```

---

## Migration Checklist

- [ ] Export existing graph structure
- [ ] Map nodes to UAA node types (task, tool, router)
- [ ] Convert conditional edges to expressions
- [ ] Extract tool definitions
- [ ] Configure state schema
- [ ] Set up checkpointing
- [ ] Test with existing inputs
- [ ] Validate output parity

---

## Troubleshooting

**Q: My custom nodes don't translate**  
A: Wrap them as tools in UAA with protocol: python

**Q: State persistence differs**  
A: Configure checkpointing in runtime section

**Q: Performance degraded**  
A: Enable optimization passes: `nexus compile --opt-level aggressive`

**Q: Missing LangChain-specific features**  
A: Most features have UAA equivalents; check the docs for mapping

---

## Next Steps

- [AWS Migration Guide](aws-to-uaa.md)
- [Custom Optimization Passes](custom-optimization-passes.md)
- [Examples Repository](../)

