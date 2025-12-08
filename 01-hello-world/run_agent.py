"""Hello World Agent - December 2025 IEV Pattern.

Simple greeting agent demonstrating:
- IntelligenceNode only (no extraction/validation needed)
- Minimal workflow
- Learning example for December 2025 standards

Code Reduction:
- Before: ~60 LOC (old Nexus IR pattern)
- After: ~57 LOC (-5% - already minimal)
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from langchain_ollama import ChatOllama

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.workflows.nodes import NodeState
from shared.workflows.common_nodes import IntelligenceNode
from shared.workflows.workflow import Workflow


# ============================================================================
# STATE
# ============================================================================

class HelloState(NodeState):
    """Workflow state for hello world."""
    name: str
    greeting: str = ""
    analysis: str = ""


# ============================================================================
# WORKFLOW
# ============================================================================

class HelloWorldWorkflow(Workflow):
    """Simple greeting workflow.
    
    Single IntelligenceNode that generates a personalized greeting.
    """
    
    def __init__(self, llm):
        """Initialize workflow.
        
        Args:
            llm: Language model for greeting generation
        """
        # Create intelligence node
        intelligence = IntelligenceNode(
            llm=llm,
            prompt_template="Generate a warm, friendly greeting for {name}.",
            required_state_keys=["name"],
            name="greeting_generator",
            description="Generate personalized greeting",
        )
        
        # Initialize parent Workflow
        super().__init__(
            name="hello-world",
            state_schema=HelloState,
            nodes=[intelligence],
            edges=[],
        )
    
    async def invoke(self, name: str) -> Dict[str, Any]:
        """Run greeting workflow.
        
        Args:
            name: Person to greet
        
        Returns:
            {"greeting": str, "duration_ms": float}
        """
        start = datetime.now()
        
        # Execute workflow
        result = await super().invoke({"name": name})
        
        duration = (datetime.now() - start).total_seconds() * 1000
        
        return {
            "name": name,
            "greeting": result.get("analysis", "Hello!"),
            "duration_ms": duration,
            "success": "analysis" in result,
        }


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Run hello world example."""
    print("\n" + "="*60)
    print("Example 01: Hello World - December 2025 IEV Pattern")
    print("="*60 + "\n")
    
    # Initialize LLM (local qwen3 via Ollama)
    # Note: num_predict removed - using model default prevents empty responses
    # when hitting token limits (done_reason: 'length' vs 'stop')
    llm = ChatOllama(
        model="qwen3:8b",
        base_url="http://localhost:11434",
        temperature=0.7,
    )
    
    # Create workflow
    workflow = HelloWorldWorkflow(llm)
    
    # Test cases
    names = ["World", "Alice", "Bob", "Developer"]
    
    print(f"Running {len(names)} greeting tests:\n")
    
    for i, name in enumerate(names, 1):
        try:
            result = await workflow.invoke(name)
            print(f"[{i}] {name}:")
            print(f"    {result['greeting']}")
            print(f"    Duration: {result['duration_ms']:.0f}ms\n")
        except Exception as e:
            print(f"[{i}] {name}: Error - {e}\n")
    
    print("="*60)
    print("✅ All greetings generated successfully")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
