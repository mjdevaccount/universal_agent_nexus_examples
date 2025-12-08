"""Run content moderation using NexusRuntime - Reduced from 86 to 30 lines."""

import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared import NexusRuntime, ClassificationExtractor


async def main():
    # Create runtime with classification extractor
    runtime = NexusRuntime(
        manifest_path=Path(__file__).parent / "manifest.yaml",
        graph_name="moderate_content",
        service_name="content-moderation",
        extractor=ClassificationExtractor(
            categories=["safe", "low", "medium", "high", "critical"]
        ),
    )
    
    await runtime.setup()
    
    # Load test content
    test_content_path = Path(__file__).parent / "test_content.json"
    if test_content_path.exists():
        with open(test_content_path) as f:
            content = json.load(f).get("content", "This is a test post")
    else:
        content = "This is a test post"
    
    # Execute
    input_data = runtime.create_input(
        f"Content to classify: {content}\n\nRespond with ONE word: safe, low, medium, high, or critical."
    )
    
    result = await runtime.execute("moderation-001", input_data)
    
    # Display results
    print(f"\n✅ Moderation Complete")
    print(f"📊 Final Decision: {result.get('decision', 'unknown')}")
    print(f"📝 Execution Path: {' → '.join(result['execution_path'])}")


if __name__ == "__main__":
    asyncio.run(main())

