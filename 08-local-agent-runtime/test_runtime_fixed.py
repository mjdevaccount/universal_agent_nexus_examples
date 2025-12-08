"""
Test script with proper MCP server management

December 2025 pattern: Uses fixtures/helpers for automatic cleanup
"""

import pytest
import sys
from pathlib import Path

# Add runtime to path
sys.path.insert(0, str(Path(__file__).parent))

from runtime.agent_runtime import MCPToolLoader, create_agent_graph, create_llm_with_tools
from langchain_core.messages import HumanMessage


def test_mcp_servers(mcp_servers):
    """Test that MCP servers are running (uses fixture)."""
    print("\n[TEST] Testing MCP servers...")
    
    # Servers are already started by fixture
    filesystem_url = mcp_servers["filesystem"]
    git_url = mcp_servers["git"]
    
    import httpx
    response = httpx.get(f"{filesystem_url.replace('/mcp', '/health')}", timeout=2)
    assert response.status_code == 200
    print(f"   [OK] Filesystem server: {response.json()}")
    
    response = httpx.get(f"{git_url.replace('/mcp', '/health')}", timeout=2)
    assert response.status_code == 200
    print(f"   [OK] Git server: {response.json()}")


def test_tool_loading(mcp_servers):
    """Test loading tools from MCP servers."""
    print("\n[TEST] Loading tools from MCP servers...")
    
    filesystem_tools = MCPToolLoader.load_from_server(mcp_servers["filesystem"])
    git_tools = MCPToolLoader.load_from_server(mcp_servers["git"])
    all_tools = filesystem_tools + git_tools
    
    assert len(all_tools) > 0, "No tools loaded"
    print(f"   [OK] Loaded {len(all_tools)} tools:")
    for tool in all_tools:
        print(f"      - {tool.name}")


def test_langgraph_agent(mcp_servers):
    """Test creating and running LangGraph agent."""
    print("\n[TEST] Creating LangGraph agent...")
    
    # Load tools
    filesystem_tools = MCPToolLoader.load_from_server(mcp_servers["filesystem"])
    git_tools = MCPToolLoader.load_from_server(mcp_servers["git"])
    all_tools = filesystem_tools + git_tools
    
    # Create LLM
    llm, _ = create_llm_with_tools(all_tools, model="qwen3:8b")
    
    if llm is None:
        print("   [SKIP] Ollama not available, skipping agent test")
        pytest.skip("Ollama not available")
    
    # Create agent
    agent = create_agent_graph(all_tools, llm)
    print("   [OK] LangGraph agent created")
    
    # Test invocation
    print("\n[TEST] Testing agent with query...")
    result = agent.invoke({
        "messages": [
            HumanMessage(content="What is git status?")
        ]
    })
    
    assert "messages" in result
    assert len(result["messages"]) > 0
    print(f"   [OK] Agent executed successfully")
    print(f"   Messages: {len(result['messages'])}")


if __name__ == "__main__":
    # Run with pytest for proper fixture management
    pytest.main([__file__, "-v", "-s"])

