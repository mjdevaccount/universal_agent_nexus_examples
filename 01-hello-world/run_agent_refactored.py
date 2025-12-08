"""Run the hello-world agent using NexusRuntime base class - Reduced from 92 to 25 lines."""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared import NexusRuntime


async def main():
    # Create runtime (handles all boilerplate)
    runtime = NexusRuntime(
        manifest_path=Path(__file__).parent / "manifest.yaml",
        graph_name="main",
        service_name="hello-world",
    )
    
    # Setup (parse, optimize, initialize)
    await runtime.setup()
    
    # Execute
    input_data = runtime.create_input(
        "Generate a greeting for World",
        name="World",  # State variable for prompt template
    )
    
    result = await runtime.execute("hello-001", input_data)
    
    # Display results
    print(f"\n✅ Hello World Complete")
    print(f"📝 Execution Path: {' → '.join(result['execution_path'])}")
    
    if result.get("last_content"):
        print(f"💬 Greeting: {result['last_content']}")


if __name__ == "__main__":
    asyncio.run(main())

