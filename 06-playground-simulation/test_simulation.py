"""
Direct test of the playground simulation - no web server needed!
Tests agents interacting with each other.

NOTE: DO NOT USE EMOJIS IN THIS FILE - Windows console (cp1252) cannot encode them
and will cause UnicodeEncodeError. Use plain text markers like [OK], [ERR], etc.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from main import Simulation, AgentConfig, ARCHETYPES


async def test_simulation():
    """Test a simple simulation with multiple agents."""
    
    print("Testing Playground Simulation\n")
    print("=" * 60)
    
    # Create a simple scenario
    scenario = "A group of kids are deciding who gets to use the swing first."
    
    # Create agents
    agents = [
        AgentConfig(archetype="bully", name="Alex"),
        AgentConfig(archetype="shy_kid", name="Sam"),
        AgentConfig(archetype="mediator", name="Jordan"),
    ]
    
    print(f"\nScenario: {scenario}\n")
    print(f"Agents:")
    for agent in agents:
        arch_info = ARCHETYPES[agent.archetype]
        print(f"  - {agent.name} ({arch_info['name']}): {arch_info['role']}")
    
    print("\n" + "=" * 60)
    print("Conversation:\n")
    
    # Create simulation
    sim = Simulation(agents, scenario)
    
    # Run a few turns
    for turn_num in range(3):
        print(f"\n--- Turn {turn_num + 1} ---")
        for agent in agents:
            try:
                turn = await sim.run_turn(agent)
                print(f"{turn['agent']}: {turn['message']}")
            except Exception as e:
                print(f"{agent.name}: [Error: {str(e)[:100]}]")
    
    print("\n" + "=" * 60)
    print("[OK] Simulation test complete!\n")


async def test_providers():
    """Test that providers can be created for all archetypes."""
    
    print("Testing LLM Providers\n")
    print("=" * 60)
    
    from llm_provider import create_provider
    
    for archetype_name in ARCHETYPES.keys():
        try:
            provider = create_provider(archetype_name)
            info = provider.get_info()
            
            status = "[OK]" if info.get("ollama_available") or info.get("fabric_available") else "[WARN]"
            print(f"{status} {archetype_name:12} -> {info['provider']:30} (Ollama: {info.get('ollama_available', False)})")
        except Exception as e:
            print(f"[ERR] {archetype_name:12} -> ERROR: {str(e)[:50]}")
    
    print("\n" + "=" * 60)


async def test_archetype_compilation():
    """Test that all archetypes can be compiled."""
    
    print("Testing Archetype Compilation\n")
    print("=" * 60)
    
    from fabric_compiler import compile_archetype
    
    for archetype_name in ARCHETYPES.keys():
        try:
            compiled = compile_archetype(archetype_name)
            print(f"[OK] {archetype_name:12} -> {compiled.name}")
            print(f"     Capabilities: {', '.join(compiled.capabilities)}")
            if compiled.domains:
                print(f"     Domains: {', '.join(compiled.domains)}")
        except Exception as e:
            print(f"[ERR] {archetype_name:12} -> ERROR: {str(e)[:50]}")
    
    print("\n" + "=" * 60)


async def main():
    """Run all tests."""
    
    print("\n" + "=" * 60)
    print("PLAYGROUND SIMULATION TEST SUITE")
    print("=" * 60 + "\n")
    
    # Test 1: Archetype compilation
    await test_archetype_compilation()
    print()
    
    # Test 2: Provider creation
    await test_providers()
    print()
    
    # Test 3: Actual simulation
    await test_simulation()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

