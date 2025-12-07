"""Run the minimal customer-support agent using LangGraphRuntime with v3.0.1 patterns."""

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
    obs_enabled = setup_observability("practical-quickstart")
    
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
    await runtime.initialize(ir_optimized, graph_name="main")

    # Test queries for different routes
    test_queries = [
        "I can't log into my account",
        "My subscription payment failed",
        "The app keeps crashing on startup",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"📝 Query: {query}")
        print(f"{'='*60}")
        
        # v3.0.0 uses MessagesState - provide input as messages
        input_data = {
            "messages": [
                HumanMessage(content=query)
            ]
        }

        # Execute with tracing
        if obs_enabled:
            async with trace_runtime_execution(f"support-{query[:10]}", graph_name="main"):
                result = await runtime.execute(
                    execution_id=f"support-{query[:10]}",
                    input_data=input_data,
                )
        else:
            result = await runtime.execute(
                execution_id=f"support-{query[:10]}",
                input_data=input_data,
            )
        
        # Extract results from messages
        messages = result.get("messages", [])
        executed_nodes = [k for k in result.keys() if k != "messages"]
        
        print(f"📍 Execution Path: {' → '.join(executed_nodes)}")
        
        if messages:
            # Find routing decision and final response
            routing_decision = None
            final_response = None
            
            for msg in messages:
                if hasattr(msg, 'content'):
                    content = str(msg.content).strip()
                    content_lower = content.lower()
                    # Check for routing decision
                    if content_lower in ['billing', 'technical', 'account']:
                        routing_decision = content_lower
                    # Find final formatted response
                    elif len(content) > 50 and content_lower not in ['billing', 'technical', 'account']:
                        if not final_response or len(content) > len(final_response):
                            final_response = content
            
            if routing_decision:
                print(f"🎯 Routed to: {routing_decision.upper()}")
            
            if final_response:
                print(f"\n💬 Customer Response:")
                response_lines = final_response.split('\n')[:10]
                for line in response_lines:
                    if line.strip():
                        print(f"   {line}")
                total_lines = len(final_response.split('\n'))
                if total_lines > 10:
                    remaining = total_lines - 10
                    print(f"   ... ({remaining} more lines)")
            else:
                # Fallback: show last message
                if messages:
                    last_message = messages[-1]
                    content = getattr(last_message, "content", "")
                    print(f"📊 Output: {content[:300]}...")
        else:
            print(f"✅ Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
