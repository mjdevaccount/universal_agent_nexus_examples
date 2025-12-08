"""Test without num_predict to use model default."""

import asyncio
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

async def test():
    # No num_predict - use model default
    llm = ChatOllama(
        model="qwen3:8b",
        base_url="http://localhost:11434",
        temperature=0.7,
        # num_predict not set - use default
    )
    
    names = ["World", "Alice", "Bob", "Developer"]
    
    for i, name in enumerate(names, 1):
        print(f"\n[{i}] Testing with name: {name}")
        prompt = f"Generate a warm, friendly greeting for {name}."
        
        messages = [HumanMessage(content=prompt)]
        response = await llm.ainvoke(messages)
        
        print(f"  Content length: {len(response.content)}")
        print(f"  Eval count: {response.response_metadata.get('eval_count', 'N/A')}")
        print(f"  Done reason: {response.response_metadata.get('done_reason', 'N/A')}")
        
        if len(response.content) > 0:
            print(f"  ✅ SUCCESS")
            print(f"  Content preview: {response.content[:80]}...")
        else:
            print(f"  ❌ EMPTY")

if __name__ == "__main__":
    asyncio.run(test())

