"""Standard template for Universal Agent Nexus examples.

This template follows the v3.0.1 standard pattern used across examples 01-05, 11-13, 15.
Copy this file to your example directory and customize as needed.

Usage:
1. Copy this file to <example-number>-<name>/run_agent.py
2. Update the service name in setup_observability()
3. Update the graph_name in runtime.initialize()
4. Customize input_data for your use case
5. Customize result extraction for your output format
6. Add manifest.yaml with your graph definition
7. Add requirements.txt with dependencies
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_core.messages import HumanMessage
from universal_agent_nexus.compiler import parse
from universal_agent_nexus.ir.pass_manager import create_default_pass_manager, OptimizationLevel
from universal_agent_nexus.adapters.langgraph import LangGraphRuntime
from _lib.tools.universal_agent_tools.observability_helper import setup_observability, trace_runtime_execution

# Optional: Cache Fabric integration
# from _lib.cache_fabric.defaults import resolve_fabric_from_env
# from _lib.cache_fabric.nexus_integration import store_manifest_contexts
# from _lib.cache_fabric.runtime_integration import track_execution_with_fabric


async def main():
    # Setup observability
    obs_enabled = setup_observability("<service-name>")
    
    # Optional: Setup Cache Fabric
    # fabric, fabric_meta = resolve_fabric_from_env()
    # backend = fabric_meta["backend"]
    # print(f"Using {backend} backend for Cache Fabric")
    
    # Use proper Nexus compiler pipeline: parse → optimize → execute
    manifest_path = Path(__file__).parent / "manifest.yaml"
    print("📦 Parsing manifest.yaml...")
    ir = parse(str(manifest_path))
    
    print("⚡ Running optimization passes...")
    manager = create_default_pass_manager(OptimizationLevel.DEFAULT)
    ir_optimized = manager.run(ir)
    
    # Log optimization stats
    stats = manager.get_statistics()
    if stats:
        total_time = sum(s.elapsed_ms for s in stats.values())
        print(f"✅ Applied {len(stats)} passes in {total_time:.2f}ms")
    
    # Optional: Store manifest contexts in Cache Fabric
    # await store_manifest_contexts(ir_optimized, fabric, manifest_id="<manifest-id>")
    
    runtime = LangGraphRuntime(
        postgres_url=None,
        enable_checkpointing=False,
    )
    await runtime.initialize(ir_optimized, graph_name="<graph_name>")
    
    # Prepare input data (MessagesState format for v3.0.0+)
    input_data = {
        "messages": [
            HumanMessage(content="<your input here>")
        ],
        # Add any additional state variables your graph needs
        # "variable_name": "value",
    }
    
    # Execute with tracing
    execution_id = "<execution-id>"
    if obs_enabled:
        async with trace_runtime_execution(execution_id, graph_name="<graph_name>"):
            result = await runtime.execute(
                execution_id=execution_id,
                input_data=input_data,
            )
    else:
        result = await runtime.execute(
            execution_id=execution_id,
            input_data=input_data,
        )
    
    # Optional: Track execution in Cache Fabric
    # await track_execution_with_fabric(
    #     execution_id=execution_id,
    #     graph_name="<graph_name>",
    #     result=result,
    #     fabric=fabric,
    # )
    
    # Extract results from messages (v3.0.0 MessagesState format)
    # Result structure: {'node_id': {'messages': [...]}} or {'messages': [...]}
    messages = result.get("messages", [])
    executed_nodes = [k for k in result.keys() if k != "messages"]
    
    # If no messages at top level, check node results
    if not messages and executed_nodes:
        last_node = executed_nodes[-1]
        node_result = result.get(last_node, {})
        messages = node_result.get("messages", [])
    
    print(f"\n✅ <Example Name> Complete")
    print(f"📝 Execution Path: {' → '.join(executed_nodes)}")
    
    # Extract and display results
    if messages:
        # Get the result from the last message
        last_message = messages[-1]
        content = getattr(last_message, "content", "unknown")
        print(f"💬 Result: {content}")
    else:
        # Fallback: show raw result
        print(f"✅ Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())

