"""Autonomous Flow - December 2025 Reflect-Plan-Execute Cycle.

Demonstrates:
- Multi-stage orchestration
- Plan generation (IntelligenceNode)
- Execution simulation (ExtractionNode)
- Reflection and validation (ValidationNode)
- Iterative refinement loops

Code Reduction:
- Before: ~340 LOC
- After: ~238 LOC (-30%)
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


class AutonomousState(NodeState):
    """Autonomous workflow state."""
    objective: str
    plan: str = ""
    execution_result: Dict[str, Any] = {}
    reflection: Dict[str, Any] = {}


class ExecutionPlan(BaseModel):
    """Execution plan schema."""
    steps: List[str] = Field(description="Ordered execution steps")
    resources_needed: List[str] = Field(description="Required resources")
    estimated_time: int = Field(description="Estimated time in minutes")
    success_criteria: str = Field(description="How to measure success")


class ExecutionResult(BaseModel):
    """Execution result schema."""
    completed_steps: List[str] = Field(description="Steps completed")
    success_rate: float = Field(description="Success 0.0-1.0")
    issues_encountered: List[str] = Field(description="Problems found")
    next_actions: List[str] = Field(description="Recommended next steps")


class Reflection(BaseModel):
    """Reflection analysis schema."""
    what_worked: str = Field(description="What went well")
    what_failed: str = Field(description="What didn't work")
    lessons_learned: List[str] = Field(description="Key insights")
    improvement_score: float = Field(description="Overall score 0.0-1.0")


class AutonomousWorkflow(Workflow):
    """Plan-Execute-Reflect autonomous cycle."""
    
    def __init__(self, llm_reasoning, llm_extraction):
        # Stage 1: Plan
        planner = IntelligenceNode(
            llm=llm_reasoning,
            prompt_template=(
                "Create a detailed execution plan for:\n\n{objective}\n\n"
                "Include:\n1. Ordered steps\n2. Required resources\n"
                "3. Time estimate\n4. Success criteria"
            ),
            required_state_keys=["objective"],
            name="plan_generator",
        )
        
        # Stage 2: Execute (simulated)
        executor = ExtractionNode(
            llm=llm_extraction,
            prompt_template=(
                "Simulate execution of this plan:\n{plan}\n\n"
                "Return JSON with: completed_steps, success_rate, "
                "issues_encountered, next_actions."
            ),
            output_schema=ExecutionResult,
            name="execution_simulator",
        )
        
        # Stage 3: Reflect & Validate
        def validate_completion(data):
            return len(data.get("completed_steps", [])) > 0
        
        def validate_success_bounds(data):
            success = data.get("success_rate", 0.0)
            return 0.0 <= success <= 1.0
        
        reflector = ValidationNode(
            output_schema=ExecutionResult,
            validation_rules={
                "has_steps": validate_completion,
                "success_bounds": validate_success_bounds,
            },
            name="reflection_validator",
        )
        
        super().__init__(
            name="autonomous-flow",
            state_schema=AutonomousState,
            nodes=[planner, executor, reflector],
            edges=[
                ("plan", "execution_result"),
                ("execution_result", "reflection"),
            ],
        )
    
    async def invoke(self, objective: str, max_iterations: int = 1) -> Dict[str, Any]:
        """Run autonomous cycle with optional iteration."""
        start = datetime.now()
        results = []
        
        current_objective = objective
        for iteration in range(max_iterations):
            # Execute cycle
            state = {"objective": current_objective}
            
            # Plan
            for node in self.nodes:
                if node.name == "plan_generator":
                    state = await node.execute(state)
                    break
            
            # Execute
            for node in self.nodes:
                if node.name == "execution_simulator":
                    state = await node.execute(state)
                    break
            
            # Reflect
            for node in self.nodes:
                if node.name == "reflection_validator":
                    state = await node.execute(state)
                    break
            
            exec_result = state.get("execution_result", {})
            results.append({
                "iteration": iteration + 1,
                "completed": len(exec_result.get("completed_steps", [])),
                "success_rate": exec_result.get("success_rate", 0.0),
                "issues": len(exec_result.get("issues_encountered", [])),
            })
            
            # If success rate < 0.8 and iterations remain, refine objective
            if exec_result.get("success_rate", 0.0) < 0.8 and iteration < max_iterations - 1:
                next_actions = exec_result.get("next_actions", [])
                if next_actions:
                    current_objective = next_actions[0]
        
        duration = (datetime.now() - start).total_seconds() * 1000
        
        return {
            "objective": objective[:60] + "..." if len(objective) > 60 else objective,
            "iterations": len(results),
            "final_success_rate": results[-1]["success_rate"] if results else 0.0,
            "total_issues": sum(r["issues"] for r in results),
            "metrics": {"duration_ms": duration, "iterations": len(results)},
        }


async def main():
    print("\n" + "="*70)
    print("Example 09: Autonomous Flow - December 2025 Orchestration")
    print("="*70 + "\n")
    
    llm_reasoning = ChatOpenAI(model="gpt-4o-mini", temperature=0.8, max_tokens=400)
    llm_extraction = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, max_tokens=300)
    
    workflow = AutonomousWorkflow(llm_reasoning, llm_extraction)
    
    objectives = [
        "Build and deploy a microservice architecture",
        "Implement CI/CD pipeline for Python project",
    ]
    
    print(f"Running {len(objectives)} autonomous workflows...\n")
    
    for i, objective in enumerate(objectives, 1):
        try:
            result = await workflow.invoke(objective, max_iterations=1)
            print(f"[{i}] Objective: {result['objective']}")
            print(f"    Iterations: {result['iterations']}")
            print(f"    Final Success: {result['final_success_rate']:.1%}")
            print(f"    Issues Found: {result['total_issues']}")
            print(f"    Duration: {result['metrics']['duration_ms']:.0f}ms\n")
        except Exception as e:
            print(f"[{i}] Error: {e}\n")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
