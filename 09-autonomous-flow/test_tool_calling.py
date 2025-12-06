"""
Test script to diagnose tool calling issues.
Run this to identify exactly where tool calling fails.
"""

import sys
import io
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "08-local-agent-runtime" / "runtime"))

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import BaseTool, tool
from agent_runtime import MCPToolLoader, create_llm_with_tools

print("=" * 60)
print("TOOL CALLING DIAGNOSTIC TEST")
print("=" * 60)

# Test 1: Check if bind_tools works
print("\n[TEST 1] Testing bind_tools() with qwen3:8b")
print("-" * 60)
try:
    @tool
    def test_tool(query: str) -> str:
        """Test tool for function calling."""
        return f"Test result: {query}"
    
    llm = ChatOllama(model="qwen3:8b", temperature=0.7)
    print(f"✅ LLM created: {type(llm)}")
    
    try:
        llm_bound = llm.bind_tools([test_tool])
        print(f"✅ bind_tools() succeeded: {type(llm_bound)}")
        print(f"   Bound LLM type: {type(llm_bound)}")
    except Exception as e:
        print(f"❌ bind_tools() FAILED: {type(e).__name__}: {e}")
        llm_bound = None
except Exception as e:
    print(f"❌ Setup FAILED: {type(e).__name__}: {e}")
    sys.exit(1)

# Test 2: Check response format
print("\n[TEST 2] Testing LLM response with tools bound")
print("-" * 60)
if llm_bound:
    try:
        response = llm_bound.invoke([
            HumanMessage(content="Use the test_tool with query 'hello'")
        ])
        print(f"✅ Response received: {type(response)}")
        print(f"   Has tool_calls attribute: {hasattr(response, 'tool_calls')}")
        if hasattr(response, 'tool_calls'):
            print(f"   tool_calls value: {response.tool_calls}")
            print(f"   tool_calls is truthy: {bool(response.tool_calls)}")
        else:
            print(f"   ❌ Response does NOT have tool_calls attribute")
            print(f"   Available attributes: {[a for a in dir(response) if not a.startswith('_')][:15]}")
            print(f"   Response content: {response.content[:200]}")
    except Exception as e:
        print(f"❌ LLM invoke FAILED: {type(e).__name__}: {e}")

# Test 3: Test with MCP tools
print("\n[TEST 3] Testing with actual MCP tools")
print("-" * 60)
try:
    tools = MCPToolLoader.load_from_server("http://localhost:8003/mcp")
    print(f"✅ Loaded {len(tools)} MCP tools")
    if tools:
        print(f"   First tool: {tools[0].name} - {type(tools[0])}")
        
        llm, _ = create_llm_with_tools(tools, model="qwen3:8b")
        print(f"✅ LLM with tools created: {type(llm)}")
        
        response = llm.invoke([
            HumanMessage(content="Call github_search_repos with query 'universal_agent'")
        ])
        print(f"✅ Response received: {type(response)}")
        print(f"   Has tool_calls: {hasattr(response, 'tool_calls')}")
        if hasattr(response, 'tool_calls'):
            print(f"   tool_calls: {response.tool_calls}")
        else:
            print(f"   ❌ No tool_calls in response")
            print(f"   Content: {response.content[:300]}")
except Exception as e:
    print(f"❌ MCP tool test FAILED: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Check tool schema format
print("\n[TEST 4] Checking tool schema format")
print("-" * 60)
try:
    tools = MCPToolLoader.load_from_server("http://localhost:8003/mcp")
    if tools:
        tool = tools[0]
        print(f"Tool: {tool.name}")
        print(f"Type: {type(tool)}")
        print(f"Has args_schema: {hasattr(tool, 'args_schema')}")
        if hasattr(tool, 'args_schema'):
            print(f"args_schema: {tool.args_schema}")
        print(f"Has args: {hasattr(tool, 'args')}")
        if hasattr(tool, 'args'):
            print(f"args: {tool.args}")
except Exception as e:
    print(f"❌ Schema check FAILED: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)

