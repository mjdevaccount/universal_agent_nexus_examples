"""Run the research agent locally with MCP tool servers."""

import asyncio
import os
import subprocess
import sys
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from universal_agent_nexus.adapters.langgraph import LangGraphRuntime, load_manifest
from universal_agent_tools.observability import setup_observability, trace_runtime_execution


async def start_mcp_servers() -> list[subprocess.Popen[bytes]]:
    """Start MCP tool servers in the background."""
    servers: list[subprocess.Popen[bytes]] = []

    # Start embeddings server
    embeddings = subprocess.Popen(
        ["python", "-m", "research_agent.tools.embeddings_server"],
        env={**os.environ, "PORT": "8001"},
    )
    servers.append(embeddings)
    await asyncio.sleep(2)

    return servers


async def main() -> None:
    # Setup observability
    obs_enabled = setup_observability("research-agent")
    
    servers = await start_mcp_servers()

    try:
        manifest = load_manifest("manifest.yaml")

        runtime = LangGraphRuntime(
            postgres_url=None,
            enable_checkpointing=False,
        )
        await runtime.initialize(manifest)

        # Execute with tracing
        if obs_enabled:
            async with trace_runtime_execution("research-001", graph_name="main"):
                result = await runtime.execute(
                    execution_id="research-001",
                    input_data={
                        "context": {
                            "query": "Find papers on prompt caching in language models from 2024",
                        },
                    },
                )
        else:
            result = await runtime.execute(
                execution_id="research-001",
                input_data={
                    "context": {
                        "query": "Find papers on prompt caching in language models from 2024",
                    },
                },
            )

        print("\n[OK] Research Complete")
        print(f"Output: {result['context']['last_response']}")
    finally:
        for process in servers:
            process.terminate()
            process.wait()


if __name__ == "__main__":
    asyncio.run(main())
