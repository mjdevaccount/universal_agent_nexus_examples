"""Run the content moderation agent using LangGraphRuntime."""

import asyncio
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from universal_agent_nexus.compiler import parse
from universal_agent_nexus.ir.pass_manager import create_default_pass_manager, OptimizationLevel
from universal_agent_nexus.adapters.langgraph import LangGraphRuntime
from _lib.tools.universal_agent_tools.observability_helper import setup_observability, trace_runtime_execution


async def main():
    # Setup observability
    obs_enabled = setup_observability("content-moderation")
    
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
    await runtime.initialize(ir_optimized, graph_name="moderate_content")

    # Load test content if available
    test_content_path = Path(__file__).parent / "test_content.json"
    if test_content_path.exists():
        with open(test_content_path) as f:
            test_data = json.load(f)
            content = test_data.get("content", "This is a test post")
    else:
        content = "This is a test post"
    
    # v3.0.0 uses MessagesState - provide input as messages
    from langchain_core.messages import HumanMessage
    input_data = {
        "messages": [
            HumanMessage(content=f"Content to classify: {content}\n\nRespond with ONE word: safe, low, medium, high, or critical.")
        ]
    }

    # Execute with tracing
    if obs_enabled:
        async with trace_runtime_execution("moderation-001", graph_name="moderate_content"):
            result = await runtime.execute(
                execution_id="moderation-001",
                input_data=input_data,
            )
    else:
        result = await runtime.execute(
            execution_id="moderation-001",
            input_data=input_data,
        )
    
    # Extract final decision from messages
    messages = result.get("messages", [])
    if messages:
        last_message = messages[-1]
        decision = getattr(last_message, "content", "unknown")
        print(f"\n✅ Moderation Complete")
        print(f"📊 Final Decision: {decision}")
        print(f"📝 Execution Path: {list(result.keys())}")
    else:
        print(f"✅ Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())

