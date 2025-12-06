"""Quick test of LangGraph runtime."""
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from runtime.agent_runtime import MCPToolLoader, create_agent_graph, create_llm_with_tools
from langchain_core.messages import HumanMessage

print("Loading tools...")
tools = MCPToolLoader.load_from_server('http://localhost:8001/mcp')
print(f"[OK] Loaded {len(tools)} tools")

print("Creating LLM...")
llm, _ = create_llm_with_tools(tools)
print("[OK] LLM created")

print("Creating agent...")
agent = create_agent_graph(tools, llm)
print("[OK] Agent created!")

print("\nInvoking agent...")
result = agent.invoke({
    'messages': [HumanMessage(content='Hello, what tools do you have?')]
})

print(f"[OK] Success! Got {len(result['messages'])} messages")
for msg in result['messages']:
    content = str(msg.content)[:100] if hasattr(msg, 'content') else str(msg)[:100]
    print(f"   - {type(msg).__name__}: {content}")

