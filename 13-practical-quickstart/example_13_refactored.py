"""Example 13: Practical Quickstart - Using SimpleQAWorkflow

A simple, beginner-friendly example demonstrating basic Q&A with the
SimpleQAWorkflow helper. Perfect for getting started with workflow patterns.

Key Features:
- Single LLM call Q&A pattern
- Optional system prompt for role-playing
- Automatic metrics collection
- Full error handling
- Async/await support

Use Cases:
- Educational Q&A
- Customer support queries
- Research assistance
- General knowledge questions
- Task-specific reasoning

Usage:
    ollama serve  # Terminal 1
    python 13-practical-quickstart/example_13_refactored.py  # Terminal 2
"""

import asyncio
from typing import List, Dict, Any

from langchain_ollama import ChatOllama

from shared.workflows import SimpleQAWorkflow


# ============================================================================
# Question Sets for Different Domains
# ============================================================================

PYTHON_QUESTIONS = [
    "What are decorators in Python and how do they work?",
    "Explain the difference between lists and tuples in Python.",
    "What is the Global Interpreter Lock (GIL) and why does it matter?",
    "How does async/await work in Python?",
    "What are list comprehensions and when should you use them?",
]

WEB_DEVELOPMENT_QUESTIONS = [
    "What is the difference between REST and GraphQL APIs?",
    "Explain the concept of HTTP status codes and provide examples.",
    "What is CORS and why is it important in web development?",
    "Describe the request/response cycle in a web application.",
    "What are the benefits of using a CSS preprocessor like SASS?",
]

DATA_SCIENCE_QUESTIONS = [
    "What is overfitting and how can you prevent it?",
    "Explain the difference between supervised and unsupervised learning.",
    "What is cross-validation and why is it important?",
    "Describe the steps involved in a typical machine learning project.",
    "What is the difference between accuracy and precision in classification?",
]


# ============================================================================
# Domain-Specific Workflows
# ============================================================================

class PythonExpertWorkflow:
    """Python programming expert Q&A workflow."""
    
    def __init__(self, llm):
        self.workflow = SimpleQAWorkflow(
            name="python-expert-qa",
            llm=llm,
            system_prompt="You are an expert Python programmer with 10+ years of experience. \
Provide clear, practical explanations with code examples when relevant.",
        )
    
    async def answer_questions(self, questions: List[str]) -> List[Dict[str, Any]]:
        """Answer Python questions."""
        results = []
        for question in questions:
            result = await self.workflow.invoke(question)
            results.append(result)
        return results


class WebDeveloperWorkflow:
    """Web development expert Q&A workflow."""
    
    def __init__(self, llm):
        self.workflow = SimpleQAWorkflow(
            name="web-dev-expert-qa",
            llm=llm,
            system_prompt="You are an expert web developer specializing in modern web technologies. \
Provide practical guidance with examples and best practices.",
        )
    
    async def answer_questions(self, questions: List[str]) -> List[Dict[str, Any]]:
        """Answer web development questions."""
        results = []
        for question in questions:
            result = await self.workflow.invoke(question)
            results.append(result)
        return results


class DataScientistWorkflow:
    """Data science expert Q&A workflow."""
    
    def __init__(self, llm):
        self.workflow = SimpleQAWorkflow(
            name="data-scientist-expert-qa",
            llm=llm,
            system_prompt="You are an experienced data scientist with expertise in machine learning. \
Explain concepts clearly and discuss when and why different approaches are used.",
        )
    
    async def answer_questions(self, questions: List[str]) -> List[Dict[str, Any]]:
        """Answer data science questions."""
        results = []
        for question in questions:
            result = await self.workflow.invoke(question)
            results.append(result)
        return results


# ============================================================================
# Main Demo
# ============================================================================

async def main() -> None:
    """Run the Example 13 demonstration."""
    
    # Initialize LLM
    llm = ChatOllama(
        model="mistral",
        base_url="http://localhost:11434",
        temperature=0.7,  # Balanced for thoughtful responses
    )
    
    print("\n" + "=" * 80)
    print("Example 13: Practical Quickstart (SimpleQAWorkflow)")
    print("=" * 80)
    
    # Demo 1: Python Questions
    print("\n🐍 DOMAIN 1: Python Programming")
    print("-" * 80)
    
    python_workflow = PythonExpertWorkflow(llm)
    python_results = await python_workflow.answer_questions(PYTHON_QUESTIONS[:2])  # First 2 for demo
    
    for i, result in enumerate(python_results, 1):
        query = result.get("query", "")
        answer = result.get("answer", "")
        duration = result.get("metrics", {}).get("duration_ms", 0)
        
        print(f"\nQ{i}: {query}")
        print(f"A: {answer[:200]}..." if len(answer) > 200 else f"A: {answer}")
        print(f"⏱️  Duration: {duration:.0f}ms")
    
    # Demo 2: Web Development Questions
    print("\n\n🚺 DOMAIN 2: Web Development")
    print("-" * 80)
    
    web_workflow = WebDeveloperWorkflow(llm)
    web_results = await web_workflow.answer_questions(WEB_DEVELOPMENT_QUESTIONS[:2])  # First 2 for demo
    
    for i, result in enumerate(web_results, 1):
        query = result.get("query", "")
        answer = result.get("answer", "")
        duration = result.get("metrics", {}).get("duration_ms", 0)
        
        print(f"\nQ{i}: {query}")
        print(f"A: {answer[:200]}..." if len(answer) > 200 else f"A: {answer}")
        print(f"⏱️  Duration: {duration:.0f}ms")
    
    # Demo 3: Data Science Questions
    print("\n\n📈 DOMAIN 3: Data Science")
    print("-" * 80)
    
    ds_workflow = DataScientistWorkflow(llm)
    ds_results = await ds_workflow.answer_questions(DATA_SCIENCE_QUESTIONS[:2])  # First 2 for demo
    
    for i, result in enumerate(ds_results, 1):
        query = result.get("query", "")
        answer = result.get("answer", "")
        duration = result.get("metrics", {}).get("duration_ms", 0)
        
        print(f"\nQ{i}: {query}")
        print(f"A: {answer[:200]}..." if len(answer) > 200 else f"A: {answer}")
        print(f"⏱️  Duration: {duration:.0f}ms")
    
    # Summary
    print("\n" + "=" * 80)
    print("Summary & Metrics")
    print("=" * 80)
    
    all_results = python_results + web_results + ds_results
    total_queries = len(all_results)
    total_duration = sum(r.get("metrics", {}).get("duration_ms", 0) for r in all_results)
    avg_duration = total_duration / total_queries if total_queries > 0 else 0
    
    print(f"\nTotal Queries: {total_queries}")
    print(f"Total Duration: {total_duration:.0f}ms")
    print(f"Average Duration per Query: {avg_duration:.0f}ms")
    
    # Show workflow metrics
    print(f"\nDomains Tested:")
    print(f"  - Python Programming: {len(python_results)} queries")
    print(f"  - Web Development: {len(web_results)} queries")
    print(f"  - Data Science: {len(ds_results)} queries")
    
    print("\n✅ Example 13 complete!")
    print("\n📦 To extend this example:")
    print("  1. Add more question sets for different domains")
    print("  2. Implement question categorization")
    print("  3. Add quality metrics (answer length, clarity, etc.)")
    print("  4. Create a question-answer history")
    print("  5. Implement follow-up question handling")


async def interactive_mode() -> None:
    """Interactive Q&A mode for manual testing."""
    print("\n" + "=" * 80)
    print("Interactive Q&A Mode")
    print("=" * 80)
    
    llm = ChatOllama(
        model="mistral",
        base_url="http://localhost:11434",
        temperature=0.7,
    )
    
    # Create a generic workflow
    workflow = SimpleQAWorkflow(
        name="interactive-qa",
        llm=llm,
        system_prompt="You are a helpful, knowledgeable assistant.",
    )
    
    print("\nEnter your questions (type 'quit' to exit):")
    print("-" * 80)
    
    while True:
        try:
            question = input("\nQ: ").strip()
            if question.lower() == "quit":
                break
            
            if not question:
                continue
            
            print("Processing...")
            result = await workflow.invoke(question)
            answer = result.get("answer", "No answer generated")
            duration = result.get("metrics", {}).get("duration_ms", 0)
            
            print(f"\nA: {answer}")
            print(f"\n⏱️  Duration: {duration:.0f}ms")
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {str(e)}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        # Run interactive mode
        asyncio.run(interactive_mode())
    else:
        # Run demo mode
        asyncio.run(main())
