"""Run the support chatbot agent using LangGraphRuntime."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from universal_agent_nexus.adapters.langgraph import LangGraphRuntime, load_manifest
from universal_agent_tools.observability_helper import setup_observability, trace_runtime_execution


async def main():
    # Setup observability
    obs_enabled = setup_observability("support-chatbot")
    
    manifest = load_manifest("manifest.yaml")

    runtime = LangGraphRuntime(
        postgres_url=None,
        enable_checkpointing=False,
    )
    await runtime.initialize(manifest)

    # Execute with tracing
    if obs_enabled:
        async with trace_runtime_execution("support-001", graph_name="support_conversation"):
            result = await runtime.execute(
                execution_id="support-001",
                input_data={"context": {"query": "I can't log into my account"}},
            )
    else:
        result = await runtime.execute(
            execution_id="support-001",
            input_data={"context": {"query": "I can't log into my account"}},
        )
    
    print(f"✅ Result: {result.get('context', {}).get('last_response', result)}")


if __name__ == "__main__":
    asyncio.run(main())

