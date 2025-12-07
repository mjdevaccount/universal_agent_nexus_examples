"""Run the research assistant agent using LangGraphRuntime with v3.0.1 patterns."""

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
    obs_enabled = setup_observability("research-assistant")
    
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
    await runtime.initialize(ir_optimized, graph_name="analyze_document")

    # Sample document analysis query
    query = """Analyze this research document:
    
Title: "Advances in Large Language Models"
Content: Large language models have revolutionized natural language processing. 
Recent developments in transformer architectures have enabled models like GPT-4 
and Claude to achieve remarkable performance across diverse tasks. Key innovations 
include attention mechanisms, scaling laws, and instruction tuning.

Extract key points, entities, themes, and generate a summary."""

    # v3.0.0 uses MessagesState - provide input as messages
    input_data = {
        "messages": [
            HumanMessage(content=query)
        ],
        "file_path": "sample_document.pdf",  # For document parser tool
    }

    # Execute with tracing
    if obs_enabled:
        async with trace_runtime_execution("research-001", graph_name="analyze_document"):
            result = await runtime.execute(
                execution_id="research-001",
                input_data=input_data,
            )
    else:
        result = await runtime.execute(
            execution_id="research-001",
            input_data=input_data,
        )
    
    # Extract results from messages
    messages = result.get("messages", [])
    executed_nodes = [k for k in result.keys() if k != "messages"]
    
    print(f"\n✅ Research Analysis Complete")
    print(f"📝 Execution Path: {' → '.join(executed_nodes)}")
    
    if messages:
        # Find the final summary (last substantial AIMessage)
        final_summary = None
        key_points = None
        themes = None
        
        for msg in reversed(messages):
            if hasattr(msg, 'content'):
                content = str(msg.content).strip()
                # Find summary (longest, most structured response)
                if "Executive Summary" in content or "Summary" in content:
                    if not final_summary or len(content) > len(final_summary):
                        final_summary = content
                # Find key points
                elif "Claim" in content or "key point" in content.lower():
                    if not key_points:
                        key_points = content
                # Find themes
                elif "theme" in content.lower() or "Theme" in content:
                    if not themes:
                        themes = content
        
        if final_summary:
            print(f"\n📄 Document Summary:")
            # Clean up and display
            summary_lines = final_summary.split('\n')
            for line in summary_lines[:30]:  # Show first 30 lines
                if line.strip():
                    print(f"   {line}")
            if len(summary_lines) > 30:
                print(f"   ... ({len(summary_lines) - 30} more lines)")
        else:
            # Fallback: show last substantial message
            for msg in reversed(messages):
                if hasattr(msg, 'content'):
                    content = str(msg.content).strip()
                    if len(content) > 50:
                        print(f"\n📊 Analysis Result:")
                        print(f"   {content[:500]}...")
                        break
    else:
        print(f"✅ Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())

