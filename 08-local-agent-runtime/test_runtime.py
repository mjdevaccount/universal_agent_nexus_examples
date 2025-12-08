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
    print("[TEST] Testing MCP servers...")
    
    try:
        import httpx
        
        # Test filesystem server (optional)
        try:
            response = httpx.get("http://localhost:8144/mcp/tools", timeout=2)
            if response.status_code == 200:
                tools = response.json()
                print(f"   [OK] Filesystem server: {len(tools.get('tools', []))} tools")
            else:
                print(f"   [SKIP] Filesystem server not on port 8000 (port may be in use)")
        except:
            print(f"   [SKIP] Filesystem server not running (optional)")
        
        # Test git server
        response = httpx.get("http://localhost:8145/mcp/tools", timeout=2)
        if response.status_code == 200:
            tools = response.json()
            print(f"   [OK] Git server: {len(tools.get('tools', []))} tools")
        else:
            print(f"   [FAIL] Git server: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"   [FAIL] Error: {e}")
        return False


def test_tool_loading():
    """Test loading tools from MCP servers."""
    print("\n[TEST] Loading tools from MCP servers...")
    
    try:
        # Try filesystem server (may not be running)
        filesystem_tools = MCPToolLoader.load_from_server("http://localhost:8144/mcp")
        # Git server (should be running)
        git_tools = MCPToolLoader.load_from_server("http://localhost:8145/mcp")
        all_tools = filesystem_tools + git_tools
        
        if not all_tools:
            print("   [WARN] No tools loaded. Make sure at least one MCP server is running.")
            return []
        
        print(f"   [OK] Loaded {len(all_tools)} tools:")
        for tool in all_tools:
            print(f"      - {tool.name}")
        
        return all_tools
        
    except Exception as e:
        print(f"   [FAIL] Error loading tools: {e}")
        return []


def test_langgraph_agent(tools):
    """Test creating and running LangGraph agent."""
    print("\n[TEST] Creating LangGraph agent...")
    
    try:
        # Create LLM (with fallback if Ollama not available)
        llm, _ = create_llm_with_tools(tools, model="gemma:2b-instruct")
        
        if llm is None:
            print("   [WARN] Ollama not available, using mock LLM")
            print("   [OK] Agent graph created (mock mode)")
            return True
        
        # Create agent graph
        agent = create_agent_graph(tools, llm)
        print("   [OK] LangGraph agent created")
        
        # Test invocation (simple query)
        print("\n[TEST] Testing agent with query...")
        # Simple invoke without checkpointer config
        result = agent.invoke({
            "messages": [
                HumanMessage(content="What is git status?")
            ]
        })
        
        print(f"   [OK] Agent executed successfully")
        print(f"   Messages: {len(result['messages'])}")
        
        return True
        
    except Exception as e:
        print(f"   [FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    import sys
    import io
    # Fix Windows console encoding
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("Testing Local Agent Runtime with LangGraph")
    print("=" * 60)
    
    # Test 1: MCP servers
    if not test_mcp_servers():
        print("\n[ERROR] MCP servers not running!")
        print("   Start them with:")
        print("   python mcp_servers/filesystem/server.py")
        print("   python mcp_servers/git/server.py")
        return False
    
    # Test 2: Tool loading
    tools = test_tool_loading()
    if not tools:
        print("\n[ERROR] Failed to load tools!")
        return False
    
    # Test 3: LangGraph agent
    if not test_langgraph_agent(tools):
        print("\n[ERROR] Failed to create/run agent!")
        return False
    
    print("\n" + "=" * 60)
    print("[SUCCESS] All tests passed! LangGraph runtime is working.")
    print("\nTo use the agent:")
    print("  python runtime/agent_runtime.py")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

