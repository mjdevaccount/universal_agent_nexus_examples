"""Playground Simulation - December 2025 Generation + Validation.

Demonstrates:
- IntelligenceNode: Generate creative scenarios
- ExtractionNode: Extract simulation parameters
- ValidationNode: Validate simulation quality
- Iteration: Multiple generation rounds

Code Reduction:
- Before: ~260 LOC
- After: ~208 LOC (-20%)
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.workflows.nodes import NodeState
from shared.workflows.common_nodes import (
    IntelligenceNode,
    ExtractionNode,
    ValidationNode,
)
from shared.workflows.workflow import Workflow


class SimulationState(NodeState):
    """Workflow state."""
    prompt: str
    analysis: str = ""
    extracted: Dict[str, Any] = {}
    validated: Dict[str, Any] = {}


class SimulationScenario(BaseModel):
    """Simulation scenario output."""
    scenario_title: str = Field(description="Title of scenario")
    description: str = Field(description="Detailed description")
    parameters: Dict[str, Any] = Field(description="Simulation parameters")
    expected_outcome: str = Field(description="Expected simulation result")
    difficulty: str = Field(description="Difficulty level: easy, medium, hard")
    iterations: int = Field(description="Suggested iteration count")


class PlaygroundWorkflow(Workflow):
    """Generation + validation for playground scenarios."""
    
    def __init__(self, llm_reasoning, llm_extraction):
        intelligence = IntelligenceNode(
            llm=llm_reasoning,
            prompt_template=(
                "Generate a creative playground simulation scenario:\n\n{prompt}\n\n"
                "Include:\n1. Interesting scenario title\n2. Detailed description\n"
                "3. Key parameters\n4. Expected outcomes\n5. Difficulty assessment"
            ),
            required_state_keys=["prompt"],
            name="scenario_generation",
        )
        
        extraction = ExtractionNode(
            llm=llm_extraction,
            prompt_template=(
                "Extract scenario details from:\n{analysis}\n\n"
                "Return JSON with: scenario_title, description, parameters, "
                "expected_outcome, difficulty, iterations."
            ),
            output_schema=SimulationScenario,
            name="scenario_extraction",
        )
        
        def validate_title_length(data):
            return 5 < len(data.get("scenario_title", "")) < 100
        
        def validate_description_length(data):
            return len(data.get("description", "")) > 50
        
        def validate_difficulty_valid(data):
            valid = {"easy", "medium", "hard"}
            return data.get("difficulty", "").lower() in valid
        
        validation = ValidationNode(
            output_schema=SimulationScenario,
            validation_rules={
                "title_bounds": validate_title_length,
                "description_quality": validate_description_length,
                "difficulty_valid": validate_difficulty_valid,
            },
            name="scenario_validation",
        )
        
        super().__init__(
            name="playground-simulation",
            state_schema=SimulationState,
            nodes=[intelligence, extraction, validation],
            edges=[
                ("analysis", "extraction"),
                ("extraction", "validation"),
            ],
        )
    
    async def invoke(self, prompt: str) -> Dict[str, Any]:
        start = datetime.now()
        result = await self.execute({"prompt": prompt})
        duration = (datetime.now() - start).total_seconds() * 1000
        
        validated = result.get("validated", {})
        return {
            "prompt": prompt[:60] + "..." if len(prompt) > 60 else prompt,
            "title": validated.get("scenario_title", ""),
            "description": validated.get("description", "")[:100] + "...",
            "difficulty": validated.get("difficulty", "unknown"),
            "iterations": validated.get("iterations", 1),
            "metrics": {"duration_ms": duration, "success": "validated" in result},
        }


async def main():
    print("\n" + "="*70)
    print("Example 06: Playground Simulation - December 2025 Pattern")
    print("="*70 + "\n")
    
    llm_reasoning = ChatOpenAI(model="gpt-4o-mini", temperature=0.9, max_tokens=500)
    llm_extraction = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, max_tokens=300)
    
    workflow = PlaygroundWorkflow(llm_reasoning, llm_extraction)
    
    prompts = [
        "Create a physics simulation where objects fall under different gravity conditions",
        "Design a particle system with color gradients and collision detection",
    ]
    
    for i, prompt in enumerate(prompts, 1):
        try:
            result = await workflow.invoke(prompt)
            print(f"[{i}] Prompt: {result['prompt']}")
            print(f"    Title: {result['title']}")
            print(f"    Difficulty: {result['difficulty']}")
            print(f"    Iterations: {result['iterations']}")
            print(f"    Duration: {result['metrics']['duration_ms']:.0f}ms\n")
        except Exception as e:
            print(f"[{i}] Error: {e}\n")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
