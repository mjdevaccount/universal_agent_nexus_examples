"""Run the hello-world agent using LangGraphRuntime with v3.0.1 patterns."""

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


async def main():
    # Setup observability
    obs_enabled = setup_observability("hello-world")
    
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
    
    runtime = LangGraphRuntime(
        postgres_url=None,
        enable_checkpointing=False,
    )
    await runtime.initialize(ir_optimized, graph_name="main")

    # v3.0.0 uses MessagesState - provide input as messages
    # The task node prompt uses {name}, so we'll provide it in the message content
    # and also in the state for template variable access
    input_data = {
        "messages": [
            HumanMessage(content="Generate a greeting for World")
        ],
        "name": "World",  # Provide as state variable for prompt template {name}
    }

    # Execute with tracing
    if obs_enabled:
        async with trace_runtime_execution("hello-001", graph_name="main"):
            result = await runtime.execute(
                execution_id="hello-001",
                input_data=input_data,
            )
    else:
        result = await runtime.execute(
            execution_id="hello-001",
            input_data=input_data,
        )
    
    # Extract results from messages (v3.0.0 MessagesState format)
    # Result structure: {'node_id': {'messages': [...]}} or {'messages': [...]}
    messages = result.get("messages", [])
    executed_nodes = [k for k in result.keys() if k != "messages"]
    
    # If no messages at top level, check node results
    if not messages and executed_nodes:
        last_node = executed_nodes[-1]
        node_result = result.get(last_node, {})
        messages = node_result.get("messages", [])
    
    print(f"\n✅ Hello World Complete")
    print(f"📝 Execution Path: {' → '.join(executed_nodes)}")
    
    if messages:
        # Get the greeting from the last message
        last_message = messages[-1]
        greeting = getattr(last_message, "content", "unknown")
        print(f"💬 Greeting: {greeting}")
    else:
        # Fallback: check for greeting in result
        greeting = result.get("greeting", result)
        print(f"💬 Greeting: {greeting}")


if __name__ == "__main__":
    asyncio.run(main())

