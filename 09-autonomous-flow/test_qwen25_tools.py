"""Quick test of qwen2.5-coder tool calling."""
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

@tool
def test_tool(x: str) -> str:
    """Test tool that returns the input."""
    return f"Result: {x}"

print("Testing qwen2.5-coder:14b tool calling...")
llm = ChatOllama(model='qwen2.5-coder:14b', temperature=0)
llm_t = llm.bind_tools([test_tool])

print("\nCalling LLM with tool request...")
r = llm_t.invoke([HumanMessage(content='Call the test_tool with x="hello"')])

print(f"\nResponse type: {type(r)}")
print(f"Has tool_calls: {hasattr(r, 'tool_calls')}")
if hasattr(r, 'tool_calls'):
    print(f"tool_calls: {r.tool_calls}")
    print(f"tool_calls type: {type(r.tool_calls)}")
    print(f"tool_calls length: {len(r.tool_calls) if r.tool_calls else 0}")
else:
    print("NO tool_calls attribute")
print(f"Content: {r.content[:200]}")

