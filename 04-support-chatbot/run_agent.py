"""Run the support chatbot agent using NexusRuntime - Reduced from 100+ to 50 lines."""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared import NexusRuntime, ClassificationExtractor


async def main():
    # Create runtime with classification extractor for intents
    runtime = NexusRuntime(
        manifest_path=Path(__file__).parent / "manifest.yaml",
        graph_name="support_conversation",
        service_name="support-chatbot",
        extractor=ClassificationExtractor(
            categories=["faq", "technical", "billing", "complaint", "other"]
        ),
    )
    
    await runtime.setup()
    
    # Test with different intents
    test_queries = [
        "I can't log into my account",  # technical
        "How do I reset my password?",  # faq
        "I want to cancel my subscription",  # billing
        "This service is terrible and I'm very frustrated!",  # complaint
    ]
    
    # Use first query for demo
    user_query = test_queries[0]
    
    # Execute
    input_data = runtime.create_input(user_query)
    result = await runtime.execute("support-001", input_data)
    
    # Display results
    messages = result.get("messages", [])
    
    # Find intent (should be in early messages)
    intent = result.get("decision")
    if intent and intent.lower() in ["faq", "technical", "billing", "complaint", "other"]:
        print(f"\n🎯 Classified Intent: {intent.upper()}")
    
    # Find final response (longer message, not intent keywords)
    final_response = None
    for msg in reversed(messages):
        if hasattr(msg, "content"):
            content = str(msg.content).strip()
            if content.lower() not in ["faq", "technical", "billing", "complaint", "other", "escalate", "handle"]:
                if len(content) > 20:
                    final_response = content
                    break
    
    if final_response:
        print(f"\n💬 Bot Response:")
        print(f"   {final_response}")
    elif result.get("last_content"):
        print(f"\n💬 Bot Response:")
        print(f"   {result['last_content']}")
    
    print(f"\n📝 Execution Path: {' → '.join(result['execution_path'])}")


if __name__ == "__main__":
    asyncio.run(main())
