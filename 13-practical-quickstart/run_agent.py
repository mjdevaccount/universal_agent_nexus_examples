"""Run the minimal customer-support agent using LangGraphRuntime."""

import asyncio

from universal_agent_nexus.adapters.langgraph import LangGraphRuntime, load_manifest


async def main():
    manifest = load_manifest("manifest.yaml")

    runtime = LangGraphRuntime(
        postgres_url=None,
        enable_checkpointing=False,
    )
    await runtime.initialize(manifest)

    result = await runtime.execute(
        execution_id="support-001",
        input_data={"context": {"query": "I can't log into my account"}},
    )
    print(f"✅ Result: {result['context'].get('last_response')}")


if __name__ == "__main__":
    asyncio.run(main())
