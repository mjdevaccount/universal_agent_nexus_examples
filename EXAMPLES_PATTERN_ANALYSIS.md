# Examples Pattern Analysis

**Date:** December 7, 2025  
**Analysis:** Standard pattern compliance across all examples

## Executive Summary

**Status:** ⚠️ **PARTIAL COMPLIANCE** - Examples 01-05, 11-13, 15 follow a standard pattern, but examples 06-10 use different architectures.

**Standard Pattern Compliance:** 9/14 examples (64%)

---

## Standard Pattern (Examples 01-05, 11-13, 15)

### ✅ Consistent Elements

#### 1. **File Structure**
```
<example-number>-<name>/
├── manifest.yaml          # ✅ All have this
├── run_agent.py           # ✅ All have this (except 15 uses run_fabric_demo.py)
├── README.md              # ✅ All have this
└── requirements.txt       # ⚠️ Only 11-13, 15 have this
```

#### 2. **Import Pattern**
```python
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_core.messages import HumanMessage
from universal_agent_nexus.compiler import parse
from universal_agent_nexus.ir.pass_manager import create_default_pass_manager, OptimizationLevel
from universal_agent_nexus.adapters.langgraph import LangGraphRuntime
from universal_agent_tools.observability_helper import setup_observability, trace_runtime_execution
```

**Compliance:**
- ✅ Examples 02-05, 11-13: Full compliance
- ⚠️ Example 01: Uses `load_manifest()` instead of `parse()` + `PassManager`
- ✅ Example 15: Adds Cache Fabric imports

#### 3. **Main Function Pattern**
```python
async def main():
    # Setup observability
    obs_enabled = setup_observability("<service-name>")
    
    # Use proper Nexus compiler pipeline: parse → optimize → execute
    print("📦 Parsing manifest.yaml...")
    ir = parse("manifest.yaml")
    
    print("⚡ Running optimization passes...")
    manager = create_default_pass_manager(OptimizationLevel.DEFAULT)
    ir_optimized = manager.run(ir)
    
    # Log optimization stats
    stats = manager.get_statistics()
    if stats:
        total_time = sum(s.elapsed_ms for s in stats.values())
        print(f"✅ Applied {len(stats)} passes in {total_time:.2f}ms")
    
    runtime = LangGraphRuntime(
        postgres_url=None,
        enable_checkpointing=False,
    )
    await runtime.initialize(ir_optimized, graph_name="<graph_name>")
    
    # Prepare input data (MessagesState format)
    input_data = {
        "messages": [
            HumanMessage(content="<input>")
        ]
    }
    
    # Execute with tracing
    if obs_enabled:
        async with trace_runtime_execution("<execution_id>", graph_name="<graph_name>"):
            result = await runtime.execute(
                execution_id="<execution_id>",
                input_data=input_data,
            )
    else:
        result = await runtime.execute(
            execution_id="<execution_id>",
            input_data=input_data,
        )
    
    # Extract and display results
    messages = result.get("messages", [])
    executed_nodes = [k for k in result.keys() if k != "messages"]
    # ... result processing ...
```

**Compliance:**
- ✅ Examples 02-05, 11-13: Full compliance
- ⚠️ Example 01: Uses `load_manifest()` (older pattern)
- ✅ Example 15: Adds Cache Fabric integration

#### 4. **Input Format (v3.0.0+ MessagesState)**
```python
from langchain_core.messages import HumanMessage

input_data = {
    "messages": [
        HumanMessage(content="<user_input>")
    ]
}
```

**Compliance:**
- ✅ Examples 02-05, 11-13, 15: All use MessagesState
- ⚠️ Example 01: Uses old format `{"name": "World"}`

#### 5. **Observability Integration**
```python
obs_enabled = setup_observability("<service-name>")

if obs_enabled:
    async with trace_runtime_execution("<execution_id>", graph_name="<graph_name>"):
        result = await runtime.execute(...)
else:
    result = await runtime.execute(...)
```

**Compliance:**
- ✅ Examples 01-05, 11-13, 15: All use observability helper

#### 6. **Result Extraction Pattern**
```python
messages = result.get("messages", [])
executed_nodes = [k for k in result.keys() if k != "messages"]

# Extract specific data from messages
for msg in messages:
    if hasattr(msg, 'content'):
        content = str(msg.content).strip()
        # ... process content ...
```

**Compliance:**
- ✅ Examples 02-05, 11-13: All follow this pattern
- ⚠️ Example 01: Uses old result format

---

## Non-Standard Examples (06-10)

### Example 06: Playground Simulation
- **Architecture:** Frontend + Backend (FastAPI/WebSocket)
- **No manifest.yaml:** Uses Python backend directly
- **No run_agent.py:** Uses `uvicorn backend/main:app`
- **Pattern:** Runtime-first, not manifest-first

### Example 07: Innovation Waves
- **Architecture:** Frontend + Backend (Python simulation)
- **No manifest.yaml:** Uses Python backend directly
- **No run_agent.py:** Uses `python backend/main.py`
- **Pattern:** Runtime-first, not manifest-first

### Example 08: Local Agent Runtime
- **Architecture:** MCP servers + LangGraph runtime
- **Has manifest:** `local_agent.yaml` (not `manifest.yaml`)
- **No run_agent.py:** Uses `python runtime/agent_runtime.py`
- **Pattern:** MCP-first, runtime-oriented

### Example 09: Autonomous Flow
- **Architecture:** Dynamic tool discovery
- **Has manifest:** `autonomous_flow.yaml` (not `manifest.yaml`)
- **No run_agent.py:** Uses `python runtime/autonomous_runtime.py`
- **Pattern:** Dynamic manifest generation

### Example 10: Local LLM Tool Servers
- **Architecture:** Nested scaffolding + enrichment
- **No manifest.yaml:** Uses Python scaffolding directly
- **No run_agent.py:** Uses `python organization_agent.py` or `python research_agent/run_local.py`
- **Pattern:** Tool-service scaffolding

---

## Pattern Compliance Matrix

| Example | manifest.yaml | run_agent.py | Full Compiler Pipeline | MessagesState | Observability | Cache Fabric | Compliance |
|---------|---------------|--------------|------------------------|---------------|---------------|--------------|------------|
| 01 | ✅ | ✅ | ⚠️ (uses load_manifest) | ❌ (old format) | ✅ | ❌ | ⚠️ **Partial** |
| 02 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ **Full** |
| 03 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ **Full** |
| 04 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ **Full** |
| 05 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ **Full** |
| 06 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ **Different** |
| 07 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ **Different** |
| 08 | ⚠️ (local_agent.yaml) | ❌ | ⚠️ | ⚠️ | ⚠️ | ❌ | ⚠️ **Partial** |
| 09 | ⚠️ (autonomous_flow.yaml) | ❌ | ⚠️ | ⚠️ | ⚠️ | ❌ | ⚠️ **Partial** |
| 10 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ **Different** |
| 11 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ **Full** |
| 12 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ **Full** |
| 13 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ **Full** |
| 15 | ✅ | ⚠️ (run_fabric_demo.py) | ✅ | ✅ | ✅ | ✅ | ✅ **Full** |

---

## Issues Found

### 1. **Example 01: Outdated Pattern**
- Uses `load_manifest()` instead of full compiler pipeline
- Uses old input format instead of MessagesState
- **Fix:** Update to match examples 02-05

### 2. **Examples 06-10: Different Architecture**
- These examples serve different purposes (simulations, MCP servers, scaffolding)
- They intentionally don't follow the standard manifest-first pattern
- **Recommendation:** Document these as "Advanced Examples" with different patterns

### 3. **Missing requirements.txt**
- Examples 01-05 don't have `requirements.txt`
- Examples 11-13, 15 have `requirements.txt`
- **Fix:** Add `requirements.txt` to examples 01-05

### 4. **Cache Fabric Integration**
- Only example 15 uses Cache Fabric
- Examples 02-05, 11-13 could benefit from Cache Fabric
- **Recommendation:** Gradually add Cache Fabric to standard examples

---

## Recommendations

### High Priority

1. **Update Example 01 to Standard Pattern**
   - Replace `load_manifest()` with `parse()` + `PassManager`
   - Update input format to MessagesState
   - Add `requirements.txt`

2. **Add requirements.txt to Examples 01-05**
   - Document dependencies explicitly
   - Make examples self-contained

3. **Document Examples 06-10 as "Advanced Patterns"**
   - Create separate documentation section
   - Explain why they differ from standard pattern
   - Keep them as-is (they serve different purposes)

### Medium Priority

4. **Standardize Cache Fabric Integration**
   - Add `resolve_fabric_from_env()` to examples 02-05, 11-13
   - Make Cache Fabric opt-in via environment variable
   - Document in README

5. **Create Standard Template**
   - Extract common pattern into `tools/standard_template.py`
   - Use as starting point for new examples
   - Include all standard elements (observability, compiler pipeline, MessagesState)

### Low Priority

6. **Standardize Result Extraction**
   - Create helper function for extracting messages/execution path
   - Reduce code duplication across examples
   - Add to `universal_agent_tools`

---

## Standard Pattern Template

```python
"""Run the <example-name> agent using LangGraphRuntime with v3.0.1 patterns."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_core.messages import HumanMessage
from universal_agent_nexus.compiler import parse
from universal_agent_nexus.ir.pass_manager import create_default_pass_manager, OptimizationLevel
from universal_agent_nexus.adapters.langgraph import LangGraphRuntime
from universal_agent_tools.observability_helper import setup_observability, trace_runtime_execution
# Optional: from shared.cache_fabric import resolve_fabric_from_env


async def main():
    # Setup observability
    obs_enabled = setup_observability("<service-name>")
    
    # Optional: Setup Cache Fabric
    # fabric, fabric_meta = resolve_fabric_from_env()
    
    # Use proper Nexus compiler pipeline: parse → optimize → execute
    print("📦 Parsing manifest.yaml...")
    ir = parse("manifest.yaml")
    
    print("⚡ Running optimization passes...")
    manager = create_default_pass_manager(OptimizationLevel.DEFAULT)
    ir_optimized = manager.run(ir)
    
    # Log optimization stats
    stats = manager.get_statistics()
    if stats:
        total_time = sum(s.elapsed_ms for s in stats.values())
        print(f"✅ Applied {len(stats)} passes in {total_time:.2f}ms")
    
    runtime = LangGraphRuntime(
        postgres_url=None,
        enable_checkpointing=False,
    )
    await runtime.initialize(ir_optimized, graph_name="<graph_name>")
    
    # Prepare input data (MessagesState format)
    input_data = {
        "messages": [
            HumanMessage(content="<user_input>")
        ]
    }
    
    # Execute with tracing
    if obs_enabled:
        async with trace_runtime_execution("<execution_id>", graph_name="<graph_name>"):
            result = await runtime.execute(
                execution_id="<execution_id>",
                input_data=input_data,
            )
    else:
        result = await runtime.execute(
            execution_id="<execution_id>",
            input_data=input_data,
        )
    
    # Extract and display results
    messages = result.get("messages", [])
    executed_nodes = [k for k in result.keys() if k != "messages"]
    
    print(f"\n✅ <Example> Complete")
    print(f"📝 Execution Path: {' → '.join(executed_nodes)}")
    
    # Process messages and display results
    # ... example-specific result processing ...


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Conclusion

**Overall Assessment:** Examples 02-05, 11-13, 15 follow a **strong standard pattern**. Example 01 needs updating, and examples 06-10 intentionally use different architectures.

**Next Steps:**
1. Update Example 01 to standard pattern
2. Add `requirements.txt` to examples 01-05
3. Create standard template for new examples
4. Document examples 06-10 as "Advanced Patterns"

