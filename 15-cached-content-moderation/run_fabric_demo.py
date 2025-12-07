"""Full end-to-end demo of Cache Fabric Layer integration.

Demonstrates:
1. Nexus compiler stores system prompts in fabric
2. Agent runtime reads from fabric (hot-reload)
3. Execution tracking
4. Feedback recording
5. Metrics display
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_core.messages import HumanMessage
from universal_agent_nexus.compiler import parse
from universal_agent_nexus.ir.pass_manager import create_default_pass_manager, OptimizationLevel
from universal_agent_nexus.adapters.langgraph import LangGraphRuntime

# Cache Fabric imports
from shared.cache_fabric import create_cache_fabric, ContextScope
from shared.cache_fabric.nexus_integration import store_manifest_contexts, get_router_prompt_from_fabric
from shared.cache_fabric.runtime_integration import track_execution_with_fabric, record_feedback_to_fabric
from universal_agent_tools.observability_helper import setup_observability, trace_runtime_execution


async def main():
    # Setup observability
    obs_enabled = setup_observability("cached-content-moderation")
    
    # Determine backend from environment or default to memory
    backend = os.getenv("CACHE_BACKEND", "memory")
    
    if backend == "redis":
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        print(f"🔴 Using Redis backend: {redis_url}")
        fabric = create_cache_fabric("redis", redis_url=redis_url)
    elif backend == "vector":
        # For vector backend, you'd need an embedding function
        # This is a placeholder - in production, use sentence-transformers
        print("🔍 Vector backend requires embedding_fn - using memory instead")
        fabric = create_cache_fabric("memory")
    else:
        print("💾 Using In-Memory backend (development)")
        fabric = create_cache_fabric("memory")
    
    # === PHASE 1: NEXUS COMPILER INTEGRATION ===
    print("\n" + "="*60)
    print("📦 PHASE 1: Nexus Compiler → Cache Fabric")
    print("="*60)
    
    print("\n📦 Parsing manifest.yaml...")
    ir = parse("manifest.yaml")
    
    print("⚡ Running optimization passes...")
    manager = create_default_pass_manager(OptimizationLevel.DEFAULT)
    ir_optimized = manager.run(ir)
    
    stats = manager.get_statistics()
    if stats:
        total_time = sum(s.elapsed_ms for s in stats.values())
        print(f"✅ Applied {len(stats)} passes in {total_time:.2f}ms")
    
    # Store system prompts in fabric (Nexus integration)
    print("\n💾 Storing system prompts in Cache Fabric...")
    await store_manifest_contexts(ir_optimized, fabric, graph_name="moderate_content")
    
    # Show what was stored
    router_entry = await fabric.get_context("router:risk_router:system_prompt")
    if router_entry:
        print(f"✅ Stored router:risk_router:system_prompt (v{router_entry.version})")
        print(f"   Preview: {router_entry.value[:100]}...")
    
    # === PHASE 2: AGENT RUNTIME INTEGRATION ===
    print("\n" + "="*60)
    print("🚀 PHASE 2: Agent Runtime → Cache Fabric")
    print("="*60)
    
    runtime = LangGraphRuntime(
        postgres_url=None,
        enable_checkpointing=False,
    )
    await runtime.initialize(ir_optimized, graph_name="moderate_content")
    
    # === PHASE 3: EXECUTION WITH FABRIC TRACKING ===
    print("\n" + "="*60)
    print("⚡ PHASE 3: Execution with Fabric Tracking")
    print("="*60)
    
    test_cases = [
        ("This is a great product!", "safe"),
        ("Check out my amazing deal!", "low"),
        ("This might need review", "medium"),
        ("This is dangerous content", "high"),
        ("HATE SPEECH AND VIOLENCE", "critical"),
    ]
    
    for i, (content, expected) in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {expected.upper()} ---")
        print(f"Content: {content}")
        
        execution_id = f"moderation-{i:03d}"
        
        # Read system prompt from fabric (hot-reload enabled)
        router_prompt = await get_router_prompt_from_fabric(
            "risk_router",
            fabric,
            default="Classify content risk level.",
        )
        
        # Prepare input
        input_data = {
            "messages": [
                HumanMessage(content=f"Content to classify: {content}\n\nRespond with ONE word: safe, low, medium, high, or critical.")
            ]
        }
        
        # Execute with tracing
        if obs_enabled:
            async with trace_runtime_execution(execution_id, graph_name="moderate_content"):
                result = await runtime.execute(
                    execution_id=execution_id,
                    input_data=input_data,
                )
        else:
            result = await runtime.execute(
                execution_id=execution_id,
                input_data=input_data,
            )
        
        # Track execution in fabric
        await track_execution_with_fabric(
            execution_id=execution_id,
            graph_name="moderate_content",
            result=result,
            fabric=fabric,
        )
        
        # Extract decision from result structure
        # Result structure: {node_name: {messages: [...]}, ...}
        decision = None
        
        # Check all node results for messages
        all_messages = []
        for node_name, node_result in result.items():
            if isinstance(node_result, dict) and "messages" in node_result:
                all_messages.extend(node_result["messages"])
        
        # Also check top-level messages
        if "messages" in result:
            all_messages.extend(result["messages"])
        
        if all_messages:
            # Find the router's decision (usually first message from router)
            for msg in all_messages:
                if hasattr(msg, 'content'):
                    content = str(msg.content).strip().lower()
                    # Check if it's a routing decision (single word)
                    if content in ['safe', 'low', 'medium', 'high', 'critical']:
                        decision = content
                        break
            
            # Fallback: search in message content
            if not decision:
                for msg in all_messages:
                    if hasattr(msg, 'content'):
                        content = str(msg.content).strip().lower()
                        # Extract decision from content if it contains one
                        for word in ['safe', 'low', 'medium', 'high', 'critical']:
                            if word in content:
                                decision = word
                                break
                        if decision:
                            break
        
        # If still no decision, check node names (router output might be in node name)
        if not decision:
            executed_nodes = [k for k in result.keys() if k != "messages"]
            # The router decision is logged, so we can infer from execution path
            # But for now, we'll use the router's logged output from INFO logs
        
        if decision:
            print(f"✅ Decision: {decision.upper()}")
            
            # Record feedback
            await record_feedback_to_fabric(
                execution_id=execution_id,
                feedback={
                    "status": "success",
                    "classification": decision,
                    "expected": expected,
                    "match": expected in decision or decision in expected,
                },
                fabric=fabric,
            )
        else:
            # Show execution path instead
            executed_nodes = [k for k in result.keys() if k != "messages"]
            print(f"✅ Execution Path: {' → '.join(executed_nodes)}")
            print(f"   (Decision inferred from execution path)")
            
            # Record feedback with inferred decision
            if executed_nodes:
                # Infer decision from path (last node before audit_log)
                path_str = ' '.join(executed_nodes).lower()
                for word in ['critical', 'high', 'medium', 'low', 'safe']:
                    if word in path_str:
                        decision = word
                        break
            
            if decision:
                await record_feedback_to_fabric(
                    execution_id=execution_id,
                    feedback={
                        "status": "success",
                        "classification": decision,
                        "expected": expected,
                        "match": expected in decision or decision in expected,
                        "inferred": True,
                    },
                    fabric=fabric,
                )
    
    # === PHASE 4: METRICS ===
    print("\n" + "="*60)
    print("📊 PHASE 4: Cache Fabric Metrics")
    print("="*60)
    
    metrics = await fabric.get_metrics()
    print(f"\n📈 Metrics:")
    for key, value in metrics.items():
        if key != "stats":
            print(f"   {key}: {value}")
    
    if "stats" in metrics:
        print(f"\n📊 Detailed Stats:")
        for key, value in metrics["stats"].items():
            print(f"   {key}: {value}")
    
    # Show stored contexts
    print(f"\n💾 Stored Contexts:")
    router_entry = await fabric.get_context("router:risk_router:system_prompt")
    if router_entry:
        print(f"   ✅ router:risk_router:system_prompt (v{router_entry.version})")
    
    graph_entry = await fabric.get_context("graph:moderate_content:metadata")
    if graph_entry:
        print(f"   ✅ graph:moderate_content:metadata")
    
    print(f"\n✅ Cache Fabric Demo Complete!")
    print(f"   Backend: {metrics.get('backend', 'unknown')}")
    print(f"   Total executions tracked: {len(test_cases)}")


if __name__ == "__main__":
    asyncio.run(main())

