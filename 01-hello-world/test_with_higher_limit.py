"""Test with higher num_predict to see if that helps."""

import asyncio
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

async def test():
    # Try with 500 tokens to give more headroom
    llm = ChatOllama(
        model="qwen3:8b",
        base_url="http://localhost:11434",
        temperature=0.7,
        num_predict=500,  # Much higher limit
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
            print(f"  ✅ SUCCESS: {response.content[:100]}...")
        else:
            print(f"  ❌ EMPTY")

if __name__ == "__main__":
    asyncio.run(test())

