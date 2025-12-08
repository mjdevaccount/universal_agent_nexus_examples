"""Detailed test of LLM response to understand empty content."""

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
    
    print("Testing with num_predict=100...")
    response1 = await llm.ainvoke([HumanMessage(content="Say hello")])
    print(f"Response 1 - Content: {repr(response1.content)}")
    print(f"Response 1 - Metadata: {response1.response_metadata}")
    print(f"Response 1 - Output tokens: {response1.response_metadata.get('eval_count', 'N/A')}")
    print()
    
    print("Testing with num_predict=200...")
    llm2 = ChatOllama(
        model="qwen3:8b",
        base_url="http://localhost:11434",
        temperature=0.7,
        num_predict=200,
    )
    response2 = await llm2.ainvoke([HumanMessage(content="Say hello")])
    print(f"Response 2 - Content: {repr(response2.content)}")
    print(f"Response 2 - Metadata: {response2.response_metadata}")
    print(f"Response 2 - Output tokens: {response2.response_metadata.get('eval_count', 'N/A')}")
    print()
    
    print("Testing with streaming=False explicitly...")
    llm3 = ChatOllama(
        model="qwen3:8b",
        base_url="http://localhost:11434",
        temperature=0.7,
        num_predict=200,
    )
    response3 = await llm3.ainvoke([HumanMessage(content="Say hello")])
    print(f"Response 3 - Content: {repr(response3.content)}")
    print(f"Response 3 - Content length: {len(response3.content)}")
    print()
    
    # Check if there's streaming happening
    print("Checking for streaming chunks...")
    chunks = []
    async for chunk in llm.astream([HumanMessage(content="Say hello")]):
        chunks.append(chunk)
        if hasattr(chunk, 'content'):
            print(f"  Chunk content: {repr(chunk.content)}")
    
    print(f"\nTotal chunks received: {len(chunks)}")
    if chunks:
        full_content = "".join([c.content for c in chunks if hasattr(c, 'content')])
        print(f"Combined content from chunks: {repr(full_content)}")

if __name__ == "__main__":
    asyncio.run(test())

