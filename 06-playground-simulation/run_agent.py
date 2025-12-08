"""
Example 06: Playground Simulation (Refactored)

Demonstrates tool-calling workflow for multi-agent simulation.

Before (Original):
  - ~150 lines of custom orchestration
  - Manual tool selection logic
  - No metrics collection
  - Tightly coupled to specific tools

After (Refactored with ToolCallingWorkflow):
  - ~80 lines of business logic
  - Automatic tool binding and execution
  - Full metrics + visualization
  - Reusable across any tool set

Pattern:
  User Query (simulation scenario)
    ↓
  LLM: Should I call a tool? Yes/No
    ├─ No  → Final response (simulation complete)
    └─ Yes → Select tool and call it
            ↓
        Tool Result (agent interaction result)
            ↓
        [Loop back to decision]
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any

from langchain_core.tools import Tool
from langchain_ollama import ChatOllama

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from shared.workflows import ToolCallingWorkflow


# ============================================================================
# SIMULATION TOOLS (Wrapped for LangChain)
# ============================================================================

def create_simulation_tools() -> list[Tool]:
    """
    Create tool definitions for the simulation.
    
    Tools allow the LLM to interact with the simulation:
    - Advance simulation turn
    - Query agent state
    - Modify agent parameters
    - Get conversation history
    """
    
    # Import simulation after path is set
    try:
        from main import Simulation, AgentConfig, ARCHETYPES
    except ImportError:
        raise ImportError(
            "Could not import simulation. Make sure 06-playground-simulation/backend is available."
        )
    
    # Global simulation state (in real app, would use managed state)
    simulation_state = {"sim": None, "turn": 0, "max_turns": 10}
    
    def initialize_simulation(scenario: str, agent_names: str) -> str:
        """
        Initialize a new simulation.
        
        Args:
            scenario: Description of the scenario
            agent_names: Comma-separated agent names (e.g., "Alex,Sam,Jordan")
        
        Returns:
            Status message with initialized agents
        """
        try:
            agents = [
                AgentConfig(archetype="bully", name=name.strip())
                for name in agent_names.split(",")
            ]
            
            simulation_state["sim"] = Simulation(agents, scenario)
            simulation_state["turn"] = 0
            
            agent_list = ", ".join([a.name for a in agents])
            return f"Simulation initialized with scenario: '{scenario}'\nAgents: {agent_list}"
        except Exception as e:
            return f"Error initializing simulation: {str(e)}"
    
    def run_simulation_turn(agent_name: str) -> str:
        """
        Run one turn of the simulation for an agent.
        
        Args:
            agent_name: Name of agent to run
        
        Returns:
            Agent's message/action
        """
        try:
            sim = simulation_state["sim"]
            if not sim:
                return "Error: Simulation not initialized. Call initialize_simulation first."
            
            # Find agent by name
            agent = next((a for a in sim.agents if a.name == agent_name), None)
            if not agent:
                return f"Error: Agent '{agent_name}' not found in simulation."
            
            # Run turn
            turn = asyncio.run(sim.run_turn(agent))
            simulation_state["turn"] += 1
            
            result = f"{turn['agent']}: {turn['message']}"
            
            if simulation_state["turn"] >= simulation_state["max_turns"]:
                result += "\n[SIMULATION COMPLETE: Max turns reached]"
            
            return result
        except Exception as e:
            return f"Error running turn: {str(e)}"
    
    def get_agent_archetypes() -> str:
        """
        Get available agent archetypes.
        
        Returns:
            List of archetype options
        """
        try:
            from main import ARCHETYPES
            
            archetypes = []
            for name, info in ARCHETYPES.items():
                archetypes.append(f"- {name}: {info['name']} ({info['role']})")
            
            return "Available archetypes:\n" + "\n".join(archetypes)
        except Exception as e:
            return f"Error listing archetypes: {str(e)}"
    
    def get_simulation_status() -> str:
        """
        Get current simulation status.
        
        Returns:
            Status report with turn count and agent states
        """
        try:
            sim = simulation_state["sim"]
            if not sim:
                return "Simulation not initialized."
            
            turn = simulation_state["turn"]
            max_turns = simulation_state["max_turns"]
            agents = ", ".join([a.name for a in sim.agents])
            
            return f"Turn: {turn}/{max_turns}\nAgents: {agents}\nScenario: {sim.scenario}"
        except Exception as e:
            return f"Error getting status: {str(e)}"
    
    # Return tools
    return [
        Tool(
            name="initialize_simulation",
            func=initialize_simulation,
            description="Initialize a new simulation with a scenario and agent names. Call this first!",
        ),
        Tool(
            name="run_simulation_turn",
            func=run_simulation_turn,
            description="Run one turn of simulation for a specific agent. Provide the agent's name.",
        ),
        Tool(
            name="get_agent_archetypes",
            func=get_agent_archetypes,
            description="Get available agent archetype options (bully, mediator, shy_kid, etc.)",
        ),
        Tool(
            name="get_simulation_status",
            func=get_simulation_status,
            description="Get current simulation status (turn count, agents, scenario)",
        ),
    ]


# ============================================================================
# MAIN EXAMPLE
# ============================================================================

async def main():
    """
    Run Example 06 using ToolCallingWorkflow.
    
    Demonstrates:
    1. Creating LLM instance
    2. Building simulation tools
    3. Creating ToolCallingWorkflow
    4. Running simulation via tool-calling loop
    5. Collecting and displaying metrics
    """
    
    print("\n" + "=" * 80)
    print("Example 06: Playground Simulation (Refactored with ToolCallingWorkflow)")
    print("=" * 80 + "\n")
    
    # 1. Create LLM
    print("[1/4] Initializing LLM...")
    llm = ChatOllama(
        model="qwen3:8b",
        base_url="http://localhost:11434",
        temperature=0.7,  # Balanced for decision-making
        num_predict=512,
    )
    print("      ✓ Ollama model loaded: qwen3:8b\n")
    
    # 2. Create tools
    print("[2/4] Creating simulation tools...")
    tools = create_simulation_tools()
    print(f"      ✓ {len(tools)} tools available:")
    for tool in tools:
        print(f"        - {tool.name}")
    print()
    
    # 3. Create workflow
    print("[3/4] Creating ToolCallingWorkflow...")
    workflow = ToolCallingWorkflow(
        name="playground-simulation",
        llm=llm,
        tools=tools,
        max_iterations=10,
        timeout_seconds=60,
    )
    print("      ✓ Workflow created\n")
    
    # 4. Run simulation
    print("[4/4] Running simulation via tool-calling loop...\n")
    print("-" * 80)
    
    query = """
    Simulate a playground scenario where three kids (Alex, Sam, and Jordan) 
    are deciding who gets to use the swing first. 
    
    Start by initializing the simulation with these agents, then run 3-4 turns 
    to show how the situation develops. Finally, provide a summary of what happened.
    
    Use the available tools to run the simulation and gather information.
    """
    
    result = await workflow.invoke(query)
    
    print("-" * 80 + "\n")
    
    # Display results
    print("SIMULATION RESULTS:")
    print("=" * 80)
    
    print("\nFinal Response:")
    print("-" * 40)
    if result["final_response"]:
        print(result["final_response"])
    else:
        print("[No final response generated]")
    
    print("\n\nTool Calls Executed:")
    print("-" * 40)
    print(f"Total tool calls: {len(result['tool_calls'])}")
    print(f"Iterations: {result['iterations']}\n")
    
    for i, call in enumerate(result["tool_calls"], 1):
        status = "✓" if call.success else "✗"
        print(f"{i}. {status} {call.tool_name}")
        if call.tool_input:
            inputs = ", ".join(f"{k}={v}" for k, v in call.tool_input.items())
            print(f"   Input: {inputs}")
        if call.success:
            result_preview = call.tool_result[:100].replace("\n", " ")
            print(f"   Result: {result_preview}..." if len(call.tool_result) > 100 else f"   Result: {call.tool_result}")
        else:
            print(f"   Error: {call.error}")
        print(f"   Duration: {call.duration_ms:.1f}ms")
    
    # Display metrics
    print("\n\nMetrics:")
    print("-" * 40)
    metrics = result["metrics"]
    print(f"Total Duration: {metrics['total_duration_ms']:.1f}ms")
    print(f"Successful Calls: {metrics['successful_calls']}/{metrics['tool_call_count']}")
    print(f"Success Rate: {metrics['success_rate']*100:.1f}%")
    
    if metrics["tool_call_count"] > 0:
        print(f"Avg Tool Duration: {metrics['average_tool_duration_ms']:.1f}ms")
    
    if metrics["errors"]:
        print(f"\nErrors:")
        for error in metrics["errors"]:
            print(f"  - {error}")
    
    print("\n" + "=" * 80)
    print("✓ Example 06 Complete!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[Interrupted by user]")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n[ERROR] {str(e)}")
        print("\nMake sure:")
        print("  1. Ollama is running: ollama serve")
        print("  2. Model is available: ollama pull qwen3:8b")
        print("  3. Backend is accessible: 06-playground-simulation/backend/")
        sys.exit(1)
