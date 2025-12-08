"""Run the self-modifying agent using NexusRuntime - Reduced from 121 to 45 lines."""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from _lib.runtime import NexusRuntime, ClassificationExtractor


async def main():
    # Create runtime with classification extractor for binary routing
    runtime = NexusRuntime(
        manifest_path=Path(__file__).parent / "manifest.yaml",
        graph_name="main",
        service_name="self-modifying-agent",
        extractor=ClassificationExtractor(
            categories=["search_docs", "calculate_risk"]
        ),
    )
    
    await runtime.setup()
    
    # Test queries for different routes
    test_queries = [
        "Search documents for risk analysis",
        "Calculate risk for my portfolio",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"📝 Query: {query}")
        print(f"{'='*60}")
        
        # Execute
        result = await runtime.execute(
            f"self-mod-{query[:10].replace(' ', '_')}",
            runtime.create_input(query)
        )
        
        # Display results
        print(f"📍 Execution Path: {' → '.join(result['execution_path'])}")
        
        routing_decision = result.get("decision")
        if routing_decision:
            print(f"🎯 Routed to: {routing_decision.replace('_', ' ').upper()}")
        
        # Find formatted response
        messages = result.get("messages", [])
        final_response = None
        for msg in reversed(messages):
            if hasattr(msg, "content"):
                content = str(msg.content).strip()
                if len(content) > 50 and content.lower() != routing_decision:
                    final_response = content
                    break
        
        if final_response:
            print(f"\n💬 Formatted Response:")
            response_lines = final_response.split('\n')[:10]
            for line in response_lines:
                if line.strip():
                    print(f"   {line}")
            if len(final_response.split('\n')) > 10:
                remaining = len(final_response.split('\n')) - 10
                print(f"   ... ({remaining} more lines)")
        elif result.get("last_content"):
            print(f"📊 Output: {result['last_content'][:300]}...")


if __name__ == "__main__":
    asyncio.run(main())
