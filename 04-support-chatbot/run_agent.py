"""Run the support chatbot agent using LangGraphRuntime with v3.0.1 patterns."""

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
    obs_enabled = setup_observability("support-chatbot")
    
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
    await runtime.initialize(ir_optimized, graph_name="support_conversation")

    # Test with different intents
    test_queries = [
        "I can't log into my account",  # technical
        "How do I reset my password?",  # faq
        "I want to cancel my subscription",  # billing
        "This service is terrible and I'm very frustrated!",  # complaint
    ]
    
    # Use first query for demo
    user_query = test_queries[0]
    
    # v3.0.0 uses MessagesState - provide input as messages
    input_data = {
        "messages": [
            HumanMessage(content=user_query)
        ]
    }

    # Execute with tracing
    if obs_enabled:
        async with trace_runtime_execution("support-001", graph_name="support_conversation"):
            result = await runtime.execute(
                execution_id="support-001",
                input_data=input_data,
            )
    else:
        result = await runtime.execute(
            execution_id="support-001",
            input_data=input_data,
        )
    
    # Extract results from messages (result structure: {'node_id': {'messages': [...]}})
    executed_nodes = [k for k in result.keys() if k != "messages"]
    messages = None
    
    # Get messages from the last executed node
    if executed_nodes:
        last_node = executed_nodes[-1]
        node_result = result.get(last_node, {})
        messages = node_result.get("messages", [])
    
    print(f"\n✅ Support Chatbot Complete")
    print(f"📝 Execution Path: {' → '.join(executed_nodes)}")
    
    if messages:
        # Find intent classification (first router response)
        intent = None
        for msg in messages:
            if hasattr(msg, 'content'):
                content = str(msg.content).strip().lower()
                if content in ['faq', 'technical', 'billing', 'complaint', 'other']:
                    intent = content
                    break
        
        # Find the final response (last AIMessage that's not an intent)
        final_response = None
        for msg in reversed(messages):
            if hasattr(msg, 'content'):
                content = str(msg.content).strip()
                # Skip intent classifications and routing decisions
                if content.lower() not in ['faq', 'technical', 'billing', 'complaint', 'other', 'escalate', 'handle']:
                    if len(content) > 20:  # Likely a real response
                        final_response = content
                        break
        
        if intent:
            print(f"\n🎯 Classified Intent: {intent.upper()}")
        
        if final_response:
            print(f"\n💬 Bot Response:")
            # Format response nicely (wrap long lines)
            lines = final_response.split('\n')
            for line in lines[:10]:  # Show first 10 lines
                print(f"   {line}")
            if len(lines) > 10:
                print(f"   ... ({len(lines) - 10} more lines)")
        else:
            # Fallback: show last message
            if messages:
                last_message = messages[-1]
                content = getattr(last_message, "content", "")
                print(f"\n💬 Response: {content[:400]}...")
    else:
        print(f"⚠️  No messages found in result")
        print(f"📍 Executed Nodes: {' → '.join(executed_nodes)}")


if __name__ == "__main__":
    asyncio.run(main())

