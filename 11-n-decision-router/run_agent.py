"""Run the n-decision router agent using NexusRuntime - Reduced from 130 to 50 lines."""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from _lib.runtime import NexusRuntime, ClassificationExtractor


async def main():
    # Create runtime with classification extractor for routing decisions
    runtime = NexusRuntime(
        manifest_path=Path(__file__).parent / "manifest.yaml",
        graph_name="main",
        service_name="n-decision-router",
        extractor=ClassificationExtractor(
            categories=["data_quality", "growth_experiment", "customer_support", "reporting"]
        ),
    )
    
    await runtime.setup()
    
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
        
        # Execute
        result = await runtime.execute(
            f"router-{query[:10].replace(' ', '_')}",
            runtime.create_input(query)
        )
        
        # Display results
        print(f"📍 Execution Path: {' → '.join(result['execution_path'])}")
        
        routing_decision = result.get("decision")
        if routing_decision:
            print(f"🎯 Routed to: {routing_decision.upper().replace('_', ' ')}")
        
        # Find formatted response (longer message, not routing decision)
        messages = result.get("messages", [])
        final_response = None
        for msg in reversed(messages):
            if hasattr(msg, "content"):
                content = str(msg.content).strip()
                if len(content) > 50 and content.lower() != routing_decision:
                    final_response = content
                    break
        
        if final_response:
            # Clean up response
            cleaned = final_response.replace("</think>", "").strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:-3].strip()
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:-3].strip()
            
            # Remove lines starting with '_'
            lines = cleaned.split('\n')
            cleaned = '\n'.join([l for l in lines if not l.strip().startswith('_')])
            
            print(f"\n💬 Formatted Response:")
            response_lines = cleaned.split('\n')[:10]
            for line in response_lines:
                if line.strip():
                    print(f"   {line}")
            if len(cleaned.split('\n')) > 10:
                remaining = len(cleaned.split('\n')) - 10
                print(f"   ... ({remaining} more lines)")
        elif result.get("last_content"):
            print(f"📊 Output: {result['last_content'][:300]}...")


if __name__ == "__main__":
    asyncio.run(main())
