"""Run the research assistant agent using LangGraphRuntime."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from universal_agent_nexus.adapters.langgraph import LangGraphRuntime, load_manifest
from universal_agent_tools.observability_helper import setup_observability, trace_runtime_execution


async def main():
    # Setup observability
    obs_enabled = setup_observability("research-assistant")
    
    manifest = load_manifest("manifest.yaml")

    runtime = LangGraphRuntime(
        postgres_url=None,
        enable_checkpointing=False,
    )
    await runtime.initialize(manifest)

    # Execute with tracing
    if obs_enabled:
        async with trace_runtime_execution("research-001", graph_name="analyze_document"):
            result = await runtime.execute(
                execution_id="research-001",
                input_data={"file_path": "sample_document.pdf"},
            )
    else:
        result = await runtime.execute(
            execution_id="research-001",
            input_data={"file_path": "sample_document.pdf"},
        )
    
    print(f"✅ Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())

