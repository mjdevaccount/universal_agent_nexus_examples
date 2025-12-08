"""Test LLM response structure to diagnose empty content issue."""

import asyncio
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

async def test():
    llm = ChatOllama(
        model="qwen3:8b",
        base_url="http://localhost:11434",
        temperature=0.7,
        num_predict=100,
    )
    
    print("Testing LLM response...")
    response = await llm.ainvoke([HumanMessage(content="Say hello")])
    
    print(f"\nResponse type: {type(response)}")
    print(f"Response object: {response}")
    print(f"Has 'content' attr: {hasattr(response, 'content')}")
    
    if hasattr(response, 'content'):
        print(f"Content value: {repr(response.content)}")
        print(f"Content type: {type(response.content)}")
        print(f"Content length: {len(response.content) if response.content else 0}")
    else:
        print("Available attributes:")
        attrs = [x for x in dir(response) if not x.startswith("_")]
        print(f"  {attrs}")
        
        # Try common alternatives
        if hasattr(response, 'text'):
            print(f"  text: {repr(response.text)}")
        if hasattr(response, 'message'):
            print(f"  message: {response.message}")
        if hasattr(response, 'response'):
            print(f"  response: {response.response}")

if __name__ == "__main__":
    asyncio.run(test())

