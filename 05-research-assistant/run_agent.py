"""Run the research assistant agent using NexusRuntime - Reduced from 150+ to 50 lines."""

import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from universal_agent_nexus.runtime import NexusRuntime, JSONExtractor


async def main():
    # Create runtime with JSON extractor for structured research output
    runtime = NexusRuntime(
        manifest_path=Path(__file__).parent / "manifest.yaml",
        graph_name="research_workflow",
        service_name="research-assistant",
        extractor=JSONExtractor(),
    )
    
    await runtime.setup()
    
    # Sample research query
    research_query = """
    Analyze the following research topic:
    
    Topic: The impact of AI on software development
    
    Extract:
    - Key points with evidence
    - Named entities (people, organizations, technologies)
    - Main themes
    - Executive summary
    """
    
    # Execute
    input_data = runtime.create_input(
        research_query,
        documents=["doc1.pdf", "doc2.pdf"],  # Placeholder for document paths
    )
    
    result = await runtime.execute("research-001", input_data)
    
    # Display results
    print(f"\n[OK] Research Complete")
    print(f"[PATH] Execution Path: {' -> '.join(result['execution_path'])}")
    
    # Try to find structured output
    if result.get("parsed_json"):
        summary_data = result["parsed_json"]
        print(f"\n[SUMMARY] Research Summary:")
        if isinstance(summary_data, dict):
            print(json.dumps(summary_data, indent=2))
        else:
            print(summary_data)
    else:
        # Look for summary in messages
        messages = result.get("messages", [])
        for msg in reversed(messages):
            if hasattr(msg, "content"):
                content = str(msg.content)
                if "Executive Summary" in content or "Summary" in content:
                    print(f"\n[SUMMARY] Research Summary:")
                    print(content[:500])
                    if len(content) > 500:
                        print("   ... (truncated)")
                    break
        else:
            if result.get("last_content"):
                print(f"\n[OUTPUT] Output: {result['last_content'][:500]}...")


if __name__ == "__main__":
    asyncio.run(main())
