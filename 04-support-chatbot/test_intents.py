"""Test all intent classifications in the support chatbot."""

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


# Test cases for different intents
TEST_CASES = [
    {
        "name": "FAQ Intent",
        "query": "How do I reset my password?",
        "expected_intent": "faq",
    },
    {
        "name": "Technical Intent",
        "query": "I can't log into my account",
        "expected_intent": "technical",
    },
    {
        "name": "Billing Intent",
        "query": "I want to cancel my subscription",
        "expected_intent": "billing",
    },
    {
        "name": "Complaint Intent",
        "query": "This service is terrible and I'm very frustrated!",
        "expected_intent": "complaint",
    },
    {
        "name": "Other Intent",
        "query": "What's the weather like?",
        "expected_intent": "other",
    },
]


async def test_intent(test_case: dict, runtime: LangGraphRuntime):
    """Test a single intent classification."""
    print(f"\n{'='*60}")
    print(f"🧪 Testing: {test_case['name']}")
    print(f"💬 Query: {test_case['query']}")
    print(f"{'='*60}")
    
    input_data = {
        "messages": [
            HumanMessage(content=test_case['query'])
        ]
    }
    
    execution_id = f"test-{test_case['name'].lower().replace(' ', '-')}"
    
    try:
        result = await runtime.execute(
            execution_id=execution_id,
            input_data=input_data,
        )
        
        # Extract intent and response
        messages = result.get("messages", [])
        executed_nodes = [k for k in result.keys() if k != "messages"]
        
        intent = None
        final_response = None
        
        for msg in messages:
            if hasattr(msg, 'content'):
                content = str(msg.content).strip().lower()
                if content in ['faq', 'technical', 'billing', 'complaint', 'other']:
                    intent = content
                elif len(content) > 20 and content.lower() not in ['escalate', 'handle']:
                    final_response = content
        
        print(f"✅ Intent: {intent.upper() if intent else 'UNKNOWN'}")
        print(f"📍 Execution Path: {' → '.join(executed_nodes)}")
        
        if final_response:
            print(f"\n💬 Response: {final_response[:200]}...")
        
        # Verify routing
        if intent == test_case['expected_intent']:
            print(f"✅ Intent matched expected: {test_case['expected_intent']}")
        else:
            print(f"⚠️  Intent mismatch: expected '{test_case['expected_intent']}', got '{intent}'")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all test cases."""
    print("🚀 Support Chatbot - Intent Classification Testing")
    print("=" * 60)
    
    # Setup observability
    obs_enabled = setup_observability("support-chatbot-test")
    
    # Parse and optimize manifest
    print("\n📦 Parsing manifest.yaml...")
    ir = parse("manifest.yaml")
    
    print("⚡ Running optimization passes...")
    manager = create_default_pass_manager(OptimizationLevel.DEFAULT)
    ir_optimized = manager.run(ir)
    
    stats = manager.get_statistics()
    if stats:
        total_time = sum(s.elapsed_ms for s in stats.values())
        print(f"✅ Applied {len(stats)} passes in {total_time:.2f}ms")
    
    # Initialize runtime
    runtime = LangGraphRuntime(
        postgres_url=None,
        enable_checkpointing=False,
    )
    await runtime.initialize(ir_optimized, graph_name="support_conversation")
    
    # Run all test cases
    for test_case in TEST_CASES:
        if obs_enabled:
            async with trace_runtime_execution(f"test-{test_case['name']}", graph_name="support_conversation"):
                await test_intent(test_case, runtime)
        else:
            await test_intent(test_case, runtime)
    
    print(f"\n{'='*60}")
    print("✅ All tests complete!")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())

