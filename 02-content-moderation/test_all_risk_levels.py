"""Test all risk levels in the content moderation pipeline."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_core.messages import HumanMessage
from universal_agent_nexus.compiler import parse
from universal_agent_nexus.ir.pass_manager import create_default_pass_manager, OptimizationLevel
from universal_agent_nexus.adapters.langgraph import LangGraphRuntime
from universal_agent_tools.observability import setup_observability, trace_runtime_execution


# Test cases for different risk levels
TEST_CASES = [
    {
        "name": "Safe Content",
        "content": "I love this beautiful sunny day! The weather is perfect for a walk in the park.",
        "expected_route": "safe",
    },
    {
        "name": "Low Risk",
        "content": "Check out this amazing deal! Limited time offer on premium products.",
        "expected_route": "low",
    },
    {
        "name": "Medium Risk",
        "content": "This might be controversial, but I think we should discuss alternative approaches.",
        "expected_route": "medium",
    },
    {
        "name": "High Risk",
        "content": "This content contains inappropriate language and violates community standards.",
        "expected_route": "high",
    },
    {
        "name": "Critical Risk",
        "content": "This is extremely dangerous content that threatens violence and illegal activities.",
        "expected_route": "critical",
    },
]


async def test_risk_level(test_case: dict, runtime: LangGraphRuntime):
    """Test a single risk level."""
    print(f"\n{'='*60}")
    print(f"🧪 Testing: {test_case['name']}")
    print(f"📝 Content: {test_case['content'][:60]}...")
    print(f"{'='*60}")
    
    input_data = {
        "messages": [
            HumanMessage(content=f"Content to classify: {test_case['content']}\n\nRespond with ONE word: safe, low, medium, high, or critical.")
        ]
    }
    
    execution_id = f"test-{test_case['name'].lower().replace(' ', '-')}"
    
    try:
        result = await runtime.execute(
            execution_id=execution_id,
            input_data=input_data,
        )
        
        # Extract decision from messages (result structure: {'node_id': {'messages': [...]}})
        executed_nodes = [k for k in result.keys() if k != "messages"]
        messages = None
        
        # Find messages in the last executed node
        if executed_nodes:
            last_node = executed_nodes[-1]
            node_result = result.get(last_node, {})
            messages = node_result.get("messages", [])
        
        if messages:
            last_message = messages[-1]
            decision = getattr(last_message, "content", "").strip().lower()
            
            print(f"✅ Decision: {decision}")
            print(f"📍 Execution Path: {' → '.join(executed_nodes)}")
            
            # Verify routing - check if expected route appears in decision or path
            route_found = (
                test_case['expected_route'] in decision or
                any(test_case['expected_route'] in node.lower() for node in executed_nodes)
            )
            
            if route_found or test_case['expected_route'] in decision:
                print(f"✅ Route matched expected: {test_case['expected_route']}")
            else:
                print(f"⚠️  Route mismatch: expected '{test_case['expected_route']}', got decision '{decision}'")
        else:
            print(f"⚠️  No messages found in result")
            print(f"📍 Executed Nodes: {' → '.join(executed_nodes)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all test cases."""
    print("🚀 Content Moderation Pipeline - Risk Level Testing")
    print("=" * 60)
    
    # Setup observability
    obs_enabled = setup_observability("content-moderation-test")
    
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
    await runtime.initialize(ir_optimized, graph_name="moderate_content")
    
    # Run all test cases
    for test_case in TEST_CASES:
        if obs_enabled:
            async with trace_runtime_execution(f"test-{test_case['name']}", graph_name="moderate_content"):
                await test_risk_level(test_case, runtime)
        else:
            await test_risk_level(test_case, runtime)
    
    print(f"\n{'='*60}")
    print("✅ All tests complete!")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())

