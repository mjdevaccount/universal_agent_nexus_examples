"""Test sequential LLM calls to understand why first works but others don't."""

import asyncio
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

async def test():
    llm = ChatOllama(
        model="qwen3:8b",
        base_url="http://localhost:11434",
        temperature=0.7,
        num_predict=200,
    )
    
    names = ["World", "Alice", "Bob", "Developer"]
    
    for i, name in enumerate(names, 1):
        print(f"\n[{i}] Testing with name: {name}")
        prompt = f"Generate a warm, friendly greeting for {name}."
        
        # Fresh messages each time (like the workflow should)
        messages = [HumanMessage(content=prompt)]
        response = await llm.ainvoke(messages)
        
        print(f"  Content: {repr(response.content)}")
        print(f"  Content length: {len(response.content)}")
        print(f"  Eval count: {response.response_metadata.get('eval_count', 'N/A')}")
        print(f"  Done reason: {response.response_metadata.get('done_reason', 'N/A')}")
        
        if len(response.content) == 0:
            print(f"  ⚠️  EMPTY RESPONSE!")
            
            # Check if there's something in additional_kwargs
            if response.additional_kwargs:
                print(f"  Additional kwargs: {response.additional_kwargs}")

if __name__ == "__main__":
    asyncio.run(test())

