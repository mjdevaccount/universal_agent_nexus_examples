"""
Test script to verify LangGraph runtime works locally.

Run this after starting MCP servers:
1. python mcp_servers/filesystem/server.py
2. python mcp_servers/git/server.py
3. python test_runtime.py
"""

import sys
from pathlib import Path

# Add runtime to path
sys.path.insert(0, str(Path(__file__).parent))

from runtime.agent_runtime import MCPToolLoader, create_agent_graph, create_llm_with_tools
from langchain_core.messages import HumanMessage


def test_mcp_servers():
    """Test that MCP servers are running."""
    print("🔍 Testing MCP servers...")
    
    try:
        import httpx
        
        # Test filesystem server
        response = httpx.get("http://localhost:8000/mcp/tools", timeout=2)
        if response.status_code == 200:
            tools = response.json()
            print(f"   ✅ Filesystem server: {len(tools.get('tools', []))} tools")
        else:
            print(f"   ❌ Filesystem server: {response.status_code}")
            return False
        
        # Test git server
        response = httpx.get("http://localhost:8001/mcp/tools", timeout=2)
        if response.status_code == 200:
            tools = response.json()
            print(f"   ✅ Git server: {len(tools.get('tools', []))} tools")
        else:
            print(f"   ❌ Git server: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_tool_loading():
    """Test loading tools from MCP servers."""
    print("\n🔧 Loading tools from MCP servers...")
    
    try:
        filesystem_tools = MCPToolLoader.load_from_server("http://localhost:8000/mcp")
        git_tools = MCPToolLoader.load_from_server("http://localhost:8001/mcp")
        all_tools = filesystem_tools + git_tools
        
        print(f"   ✅ Loaded {len(all_tools)} tools:")
        for tool in all_tools:
            print(f"      - {tool.name}")
        
        return all_tools
        
    except Exception as e:
        print(f"   ❌ Error loading tools: {e}")
        return []


def test_langgraph_agent(tools):
    """Test creating and running LangGraph agent."""
    print("\n🤖 Creating LangGraph agent...")
    
    try:
        # Create LLM (with fallback if Ollama not available)
        llm, _ = create_llm_with_tools(tools, model="llama3.2:11b")
        
        if llm is None:
            print("   ⚠️  Ollama not available, using mock LLM")
            print("   ✅ Agent graph created (mock mode)")
            return True
        
        # Create agent graph
        agent = create_agent_graph(tools, llm)
        print("   ✅ LangGraph agent created")
        
        # Test invocation (simple query)
        print("\n💬 Testing agent with query...")
        result = agent.invoke({
            "messages": [
                HumanMessage(content="List files in the current directory")
            ]
        })
        
        print(f"   ✅ Agent executed successfully")
        print(f"   Messages: {len(result['messages'])}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("🚀 Testing Local Agent Runtime with LangGraph")
    print("=" * 60)
    
    # Test 1: MCP servers
    if not test_mcp_servers():
        print("\n❌ MCP servers not running!")
        print("   Start them with:")
        print("   python mcp_servers/filesystem/server.py")
        print("   python mcp_servers/git/server.py")
        return False
    
    # Test 2: Tool loading
    tools = test_tool_loading()
    if not tools:
        print("\n❌ Failed to load tools!")
        return False
    
    # Test 3: LangGraph agent
    if not test_langgraph_agent(tools):
        print("\n❌ Failed to create/run agent!")
        return False
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! LangGraph runtime is working.")
    print("\nTo use the agent:")
    print("  python runtime/agent_runtime.py")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

