"""Run the content moderation agent using LangGraphRuntime."""

import asyncio
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from universal_agent_nexus.adapters.langgraph import LangGraphRuntime, load_manifest
from universal_agent_tools.observability_helper import setup_observability, trace_runtime_execution


async def main():
    # Setup observability
    obs_enabled = setup_observability("content-moderation")
    
    manifest = load_manifest("manifest.yaml")

    runtime = LangGraphRuntime(
        postgres_url=None,
        enable_checkpointing=False,
    )
    await runtime.initialize(manifest)

    # Load test content if available
    test_content_path = Path(__file__).parent / "test_content.json"
    if test_content_path.exists():
        with open(test_content_path) as f:
            test_data = json.load(f)
            input_data = {"content": test_data.get("content", "This is a test post")}
    else:
        input_data = {"content": "This is a test post"}

    # Execute with tracing
    if obs_enabled:
        async with trace_runtime_execution("moderation-001", graph_name="moderate_content"):
            result = await runtime.execute(
                execution_id="moderation-001",
                input_data=input_data,
            )
    else:
        result = await runtime.execute(
            execution_id="moderation-001",
            input_data=input_data,
        )
    
    print(f"✅ Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())

