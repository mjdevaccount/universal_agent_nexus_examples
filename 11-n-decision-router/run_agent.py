"""Run the n-decision router agent using LangGraphRuntime with v3.0.1 patterns."""

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
    obs_enabled = setup_observability("n-decision-router")
    
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
        "Check data quality for user reports",
        "Run an A/B test for the new feature",
        "Help a customer with their billing issue",
        "Generate weekly metrics report",
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
            async with trace_runtime_execution(f"router-{query[:10]}", graph_name="main"):
                result = await runtime.execute(
                    execution_id=f"router-{query[:10]}",
                    input_data=input_data,
                )
        else:
            result = await runtime.execute(
                execution_id=f"router-{query[:10]}",
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
                    # Check for routing decision (short, exact match)
                    if content_lower in ['data_quality', 'growth_experiment', 'customer_support', 'reporting']:
                        routing_decision = content_lower
                    # Find final formatted response (longest, most substantial)
                    elif len(content) > 50 and content_lower not in ['data_quality', 'growth_experiment', 'customer_support', 'reporting']:
                        if not final_response or len(content) > len(final_response):
                            final_response = content
            
            if routing_decision:
                print(f"🎯 Routed to: {routing_decision.upper().replace('_', ' ')}")
            
            if final_response:
                # Clean up response (remove any leading artifacts)
                cleaned = final_response
                if cleaned.startswith('_'):
                    # Remove leading underscore artifacts
                    lines = cleaned.split('\n')
                    cleaned = '\n'.join([l for l in lines if not l.strip().startswith('_')])
                print(f"\n💬 Formatted Response:")
                # Show first 10 lines or 400 chars
                response_lines = cleaned.split('\n')[:10]
                for line in response_lines:
                    if line.strip():
                        print(f"   {line}")
                total_lines = len(cleaned.split('\n'))
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

