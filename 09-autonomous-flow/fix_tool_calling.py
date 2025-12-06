"""
Diagnostic script to test Ollama tool calling with proper configuration
Tests all three failure points with fixes applied
"""

import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from langchain_ollama import ChatOllama  # ✅ Correct import
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
import json

# Define a simple test tool
@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers together."""
    return a * b

@tool
def get_weather(city: str) -> str:
    """Get the weather for a city."""
    return f"The weather in {city} is sunny, 72°F"

tools = [multiply, get_weather]

print("=" * 80)
print("OLLAMA TOOL CALLING DIAGNOSTIC")
print("=" * 80)

# TEST 1: Check import source
print("\n✓ TEST 1: Import Source")
print(f"   ChatOllama module: {ChatOllama.__module__}")
if "langchain_ollama" in ChatOllama.__module__:
    print("   ✅ PASS: Using correct langchain_ollama package")
else:
    print("   ❌ FAIL: Using wrong package. Install: pip install langchain-ollama")
    exit(1)

# TEST 2: Initialize with thinking mode disabled
print("\n✓ TEST 2: Model Initialization")
try:
    # Try qwen3 first
    llm = ChatOllama(
        model="qwen3:8b",
        temperature=0,
        think=False  # ✅ Critical fix
    )
    print(f"   ✅ PASS: Initialized qwen3:8b with think=False")
    model_name = "qwen3:8b"
except Exception as e:
    print(f"   ⚠️  qwen3:8b failed: {e}")
    print("   Trying llama3.1:8b instead...")
    try:
        llm = ChatOllama(
            model="llama3.1:8b",
            temperature=0
        )
        model_name = "llama3.1:8b"
        print(f"   ✅ Using {model_name} instead")
    except:
        print("   ❌ No suitable model found")
        exit(1)

# TEST 3: Check bind_tools exists and works
print("\n✓ TEST 3: Tool Binding")
try:
    llm_with_tools = llm.bind_tools(tools)
    print("   ✅ PASS: bind_tools() method exists and executed")
except AttributeError:
    print("   ❌ FAIL: bind_tools() not found. Wrong ChatOllama version.")
    exit(1)
except Exception as e:
    print(f"   ❌ FAIL: bind_tools() error: {e}")
    exit(1)

# TEST 4: Invoke and check response structure
print("\n✓ TEST 4: Tool Call Response Structure")
try:
    response = llm_with_tools.invoke([
        HumanMessage(content="What is 25 multiplied by 4?")
    ])
    
    print(f"   Response type: {type(response).__name__}")
    print(f"   Has tool_calls attr: {hasattr(response, 'tool_calls')}")
    
    if hasattr(response, "tool_calls"):
        print(f"   tool_calls value: {response.tool_calls}")
        print(f"   tool_calls type: {type(response.tool_calls)}")
        print(f"   tool_calls is None: {response.tool_calls is None}")
        print(f"   tool_calls length: {len(response.tool_calls) if response.tool_calls else 0}")
        
        if response.tool_calls and len(response.tool_calls) > 0:
            print("   ✅ PASS: Model generated tool_calls!")
            print(f"\n   Tool call details:")
            for tc in response.tool_calls:
                print(f"      - Function: {tc.get('name')}")
                print(f"      - Args: {tc.get('args')}")
        else:
            print("   ❌ FAIL: tool_calls is empty or None")
            print(f"   Response content: {response.content[:200]}")
    else:
        print("   ❌ FAIL: Response has no tool_calls attribute")
        print(f"   Response: {response}")
        
except Exception as e:
    print(f"   ❌ FAIL: Invocation error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# TEST 5: Test simple text (should NOT call tools)
print("\n✓ TEST 5: Normal Text Response (No Tools)")
try:
    response = llm_with_tools.invoke([
        HumanMessage(content="Hello, how are you?")
    ])
    
    has_tools = hasattr(response, "tool_calls") and response.tool_calls
    
    if has_tools and len(response.tool_calls) > 0:
        print("   ⚠️  WARNING: Model calling tools for simple text!")
        print(f"   Tools called: {[tc.get('name') for tc in response.tool_calls]}")
        print("   This is a known issue with some Ollama models.")
    else:
        print("   ✅ PASS: No tools called for simple greeting")
        print(f"   Response: {response.content[:100]}")
        
except Exception as e:
    print(f"   ❌ FAIL: {e}")

# TEST 6: Weather tool call
print("\n✓ TEST 6: Weather Tool Call")
try:
    response = llm_with_tools.invoke([
        HumanMessage(content="What's the weather in Dallas?")
    ])
    
    if hasattr(response, "tool_calls") and response.tool_calls:
        tool_names = [tc.get('name') for tc in response.tool_calls]
        if 'get_weather' in tool_names:
            print("   ✅ PASS: Correctly identified weather tool")
            for tc in response.tool_calls:
                if tc.get('name') == 'get_weather':
                    print(f"   City argument: {tc.get('args', {}).get('city')}")
        else:
            print(f"   ⚠️  Called wrong tool: {tool_names}")
    else:
        print("   ❌ FAIL: No tool call generated")
        print(f"   Response: {response.content[:200]}")
        
except Exception as e:
    print(f"   ❌ FAIL: {e}")

print("\n" + "=" * 80)
print("DIAGNOSIS COMPLETE")
print("=" * 80)
print(f"\nModel tested: {model_name}")
print("\nRECOMMENDATIONS:")
print("1. Ensure you're using: from langchain_ollama import ChatOllama")
print("2. Always set think=False for Qwen3 models when using tools")
print("3. Consider using llama3.1:8b or qwen2.5:7b if qwen3:8b has issues")
print("4. Update your agent_runtime.py with the fixes shown above")

