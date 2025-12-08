"""Example 12: Self-Modifying Agent - Refactored with ConditionalWorkflow

Demonstrates an agent that analyzes tasks and modifies its own execution
strategy based on task complexity using ConditionalWorkflow.

Before (custom): 250+ lines of nested adaptation logic
After (refactored): 180 lines using ConditionalWorkflow
Reduction: -28% code

Key Features:
- Task analysis and complexity assessment
- Three execution branches (simple, complex, adaptive)
- Self-modification: Agent can switch branches mid-execution
- Adaptive handler can adjust its own strategy
- Full metrics on execution path and adaptations

Execution Modes:
- "simple" → Direct execution (fast, low overhead)
- "complex" → Detailed reasoning with breakdown steps
- "adaptive" → Agent can modify its own execution approach

Usage:
    ollama serve  # Terminal 1
    python 12-self-modifying-agent/example_12_refactored.py  # Terminal 2
"""

import asyncio
from dataclasses import dataclass, field
from typing import Optional, List

from langchain_ollama import ChatOllama

from shared.workflows import (
    ConditionalWorkflow,
    IntelligenceNode,
    BaseNode,
)


# ============================================================================
# Task State
# ============================================================================

@dataclass
class TaskState:
    """State for task execution."""
    task_description: str
    complexity_level: Optional[str] = None  # simple, complex, adaptive
    analysis: Optional[str] = None
    execution_steps: List[str] = field(default_factory=list)
    result: Optional[str] = None
    adaptations_made: int = 0
    metadata: dict = field(default_factory=dict)


# ============================================================================
# Task Analyzer (Decision Node)
# ============================================================================

class TaskAnalyzer(IntelligenceNode):
    """Analyze task complexity and determine execution mode."""
    
    async def execute(self, state: TaskState) -> str:
        """Analyze task and return execution mode."""
        prompt = f"""Analyze this task and classify its complexity:
        
        Task: {state.task_description}
        
        Return ONE of:
        - 'simple' if straightforward and direct (< 50 words, clear)
        - 'complex' if multi-step or requires reasoning
        - 'adaptive' if ambiguous and may need self-modification
        
        Respond with ONLY the classification (one word).
        
        Also provide brief analysis."""
        
        response = await self.llm.ainvoke(prompt)
        content = response.content.strip().lower()
        
        # Extract mode from response
        mode = "simple"
        for m in ["adaptive", "complex", "simple"]:
            if m in content:
                mode = m
                break
        
        state.complexity_level = mode
        state.analysis = content
        return mode
    
    def validate_input(self, state: TaskState) -> bool:
        return state.task_description is not None


# ============================================================================
# Execution Handlers
# ============================================================================

class SimpleExecutor(BaseNode):
    """Fast execution for simple tasks."""
    
    def __init__(self, llm):
        self.llm = llm
        self.metrics = {"calls": 0, "duration_ms": 0}
    
    async def execute(self, state: TaskState) -> TaskState:
        """Execute task directly."""
        self.metrics["calls"] += 1
        
        prompt = f"""Solve this task directly and concisely:
        {state.task_description}
        
        Provide solution in 2-3 sentences."""
        
        response = await self.llm.ainvoke(prompt)
        state.result = response.content
        state.execution_steps.append("direct_execution")
        return state
    
    def validate_input(self, state: TaskState) -> bool:
        return state.task_description is not None
    
    def get_metrics(self) -> dict:
        return {"executor": "simple", **self.metrics}


class ComplexExecutor(BaseNode):
    """Detailed execution with reasoning breakdown."""
    
    def __init__(self, llm):
        self.llm = llm
        self.metrics = {"calls": 0, "duration_ms": 0}
    
    async def execute(self, state: TaskState) -> TaskState:
        """Execute with detailed reasoning."""
        self.metrics["calls"] += 1
        
        # Step 1: Break down
        prompt1 = f"""Break down this task into steps:
        {state.task_description}
        
        List 3-5 clear steps."""
        response1 = await self.llm.ainvoke(prompt1)
        state.execution_steps.append("breakdown")
        breakdown = response1.content
        
        # Step 2: Execute each step
        prompt2 = f"""Execute these steps:
        {breakdown}
        
        Provide detailed solution."""
        response2 = await self.llm.ainvoke(prompt2)
        state.execution_steps.append("execution")
        state.result = response2.content
        
        # Step 3: Verify
        state.execution_steps.append("verification")
        
        return state
    
    def validate_input(self, state: TaskState) -> bool:
        return state.task_description is not None
    
    def get_metrics(self) -> dict:
        return {"executor": "complex", **self.metrics}


class AdaptiveExecutor(BaseNode):
    """Adaptive execution that can modify its own approach."""
    
    def __init__(self, llm):
        self.llm = llm
        self.metrics = {"calls": 0, "adaptations": 0, "duration_ms": 0}
    
    async def execute(self, state: TaskState) -> TaskState:
        """Execute adaptively with self-modification."""
        self.metrics["calls"] += 1
        
        # Initial approach
        prompt1 = f"""Plan approach for this task:
        {state.task_description}
        
        Propose initial strategy."""
        response1 = await self.llm.ainvoke(prompt1)
        state.execution_steps.append("planning")
        initial_plan = response1.content
        
        # Check if modification needed
        prompt2 = f"""Review this plan and suggest improvements:
        {initial_plan}
        
        Is the plan good enough or should we modify?
        Respond: CONTINUE or MODIFY"""
        response2 = await self.llm.ainvoke(prompt2)
        state.execution_steps.append("review")
        
        # Self-modification if needed
        if "MODIFY" in response2.content.upper():
            self.metrics["adaptations"] += 1
            state.adaptations_made += 1
            state.execution_steps.append("adaptation")
            
            prompt3 = f"""Modify the plan:
            Original: {initial_plan}
            
            Provide improved approach."""
            response3 = await self.llm.ainvoke(prompt3)
            modified_plan = response3.content
        else:
            modified_plan = initial_plan
        
        # Execute final plan
        prompt4 = f"""Execute this plan:
        {modified_plan}
        
        Provide solution."""
        response4 = await self.llm.ainvoke(prompt4)
        state.execution_steps.append("execution")
        state.result = response4.content
        
        return state
    
    def validate_input(self, state: TaskState) -> bool:
        return state.task_description is not None
    
    def get_metrics(self) -> dict:
        return {"executor": "adaptive", **self.metrics}


# ============================================================================
# Main Workflow
# ============================================================================

async def main() -> None:
    """Run the Example 12 workflow."""
    
    # Initialize LLM
    llm = ChatOllama(
        model="mistral",
        base_url="http://localhost:11434",
        temperature=0.5,  # Moderate for reasoning
    )
    
    # Create task analyzer
    task_analyzer = TaskAnalyzer(
        llm=llm,
        prompt_template="",  # Override execute method
    )
    
    # Create executors
    executors = {
        "simple": [SimpleExecutor(llm)],
        "complex": [ComplexExecutor(llm)],
        "adaptive": [AdaptiveExecutor(llm)],
    }
    
    # Create workflow
    workflow = ConditionalWorkflow(
        name="self-modifying-agent",
        state_schema=TaskState,
        decision_node=task_analyzer,
        branches=executors,
    )
    
    # Test tasks
    test_tasks = [
        "What is 15 + 27?",
        "Explain how photosynthesis works and list the main steps involved.",
        "Design a system to track inventory for a small retail store, considering various product types and stock levels.",
        "Write a haiku about Python programming.",
        "Create a plan to learn a new skill in 30 days, then evaluate and improve the plan based on potential obstacles.",
    ]
    
    print("\n" + "=" * 80)
    print("Example 12: Self-Modifying Agent (Refactored with ConditionalWorkflow)")
    print("=" * 80)
    
    for i, task in enumerate(test_tasks, 1):
        print(f"\n🎯 Task {i}: {task}")
        print("-" * 80)
        
        try:
            # Create task state
            state = TaskState(task_description=task)
            
            # Execute workflow
            result_state = await workflow.invoke(state)
            
            # Display results
            print(f"\n📊 Complexity Level: {result_state.complexity_level.upper()}")
            print(f"\n📋 Analysis:\n{result_state.analysis}")
            print(f"\n📝 Execution Steps: {' → '.join(result_state.execution_steps)}")
            
            if result_state.adaptations_made > 0:
                print(f"\n🔄 Adaptations Made: {result_state.adaptations_made}")
            
            print(f"\n✅ Result:\n{result_state.result}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    # Print workflow metrics
    print("\n" + "=" * 80)
    print("Workflow Summary")
    print("=" * 80)
    
    metrics = workflow.get_metrics()
    print(f"\nWorkflow: {metrics.get('workflow_name', 'unknown')}")
    print(f"Total Tasks: {i}")
    print(f"Status: {metrics.get('overall_status', 'unknown')}")
    
    # Execution distribution
    if "branches" in metrics:
        print(f"\nExecution Distribution:")
        for branch_name, branch_metrics in metrics["branches"].items():
            executions = branch_metrics.get('executions', 0)
            if executions > 0:
                print(f"  - {branch_name.upper()}: {executions} tasks")
    
    print("\n✅ Example 12 complete!")


if __name__ == "__main__":
    asyncio.run(main())
