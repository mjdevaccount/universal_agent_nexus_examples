"""
AutonomousFlow Agent
Code Knowledge Management Agent with sync and Q&A capabilities.
"""

import sys
import io
from pathlib import Path
from datetime import datetime, timedelta
import json
import logging
from contextlib import nullcontext

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("autonomous_flow")

# Try to use observability if available
try:
    from universal_agent_nexus.observability import setup_tracing, trace_execution
    setup_tracing(service_name="autonomous-flow", environment="development")
    OBSERVABILITY_AVAILABLE = True
    logger.info("Observability enabled: OpenTelemetry tracing available")
except ImportError:
    OBSERVABILITY_AVAILABLE = False
    logger.warning("Observability module not available - using basic logging")

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "08-local-agent-runtime" / "runtime"))

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import BaseTool
import operator

from agent_runtime import MCPToolLoader, create_llm_with_tools

# Managed repositories
MANAGED_REPOS = [
    "mjdevaccount/universal_agent_fabric",
    "mjdevaccount/universal_agent_architecture",
    "mjdevaccount/universal_agent_nexus",
    "mjdevaccount/universal_agent_nexus_examples",
]

# Server URL
MCP_SERVER = "http://localhost:8010/mcp"


class AgentState(TypedDict):
    """Agent state."""
    messages: Annotated[Sequence[BaseMessage], operator.add]


def parse_tool_calls_from_content(content: str, tools: list) -> list:
    """Parse tool calls from JSON content."""
    import re
    
    if not content or not isinstance(content, str):
        return []
    
    try:
        tool_call = json.loads(content.strip())
        if isinstance(tool_call, dict) and "name" in tool_call:
            return [{
                "name": tool_call["name"],
                "args": tool_call.get("arguments", {}),
                "id": f"call_{tool_call['name']}_{hash(str(tool_call))}"
            }]
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON in content
    json_match = re.search(r'\{[^{}]*"name"[^{}]*\}', content)
    if json_match:
        try:
            tool_call = json.loads(json_match.group(0))
            if "name" in tool_call:
                return [{
                    "name": tool_call["name"],
                    "args": tool_call.get("arguments", {}),
                    "id": f"call_{tool_call['name']}_{hash(str(tool_call))}"
                }]
        except json.JSONDecodeError:
            pass
    
    return []


def create_agent(task_type: str = "sync"):
    """
    Create the agent for a specific task type.
    
    task_type: "sync", "query", or "maintain"
    """
    logger.info(f"Creating {task_type} agent", extra={"task_type": task_type})
    
    # Load tools from our MCP server
    tools = MCPToolLoader.load_from_server(MCP_SERVER)
    logger.info(f"Loaded {len(tools)} tools", extra={"tool_count": len(tools), "server": MCP_SERVER})
    
    # Create LLM
    llm, _ = create_llm_with_tools(tools, model="qwen2.5-coder:14b")
    logger.info("LLM ready", extra={"model": "qwen2.5-coder:14b"})
    
    # Build graph
    def agent_node(state: AgentState):
        """Agent decides what to do."""
        messages = state["messages"]
        response = llm.invoke(messages)
        
        # Parse tool calls from content if needed
        if hasattr(response, "tool_calls") and response.tool_calls:
            logger.info("Agent generated tool calls", extra={
                "tool_count": len(response.tool_calls),
                "tool_names": [tc.get("name") for tc in response.tool_calls]
            })
            return {"messages": [response]}
        
        if hasattr(response, "content") and response.content:
            parsed = parse_tool_calls_from_content(response.content, tools)
            if parsed:
                logger.info("Parsed tool calls from content", extra={
                    "tool_count": len(parsed),
                    "tool_names": [tc.get("name") for tc in parsed]
                })
                response = AIMessage(content=response.content, tool_calls=parsed)
            else:
                logger.info("Agent generated text response (no tool calls)", extra={
                    "content_length": len(str(response.content))
                })
        
        return {"messages": [response]}
    
    def tool_node(state: AgentState):
        """Execute tool calls."""
        last_message = state["messages"][-1]
        tool_messages = []
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            for tc in last_message.tool_calls:
                tool_name = tc["name"]
                tool_args = tc.get("args", {})
                tool_id = tc.get("id", tool_name)
                
                logger.info("Executing tool", extra={
                    "tool_name": tool_name,
                    "tool_id": tool_id,
                    "args_keys": list(tool_args.keys()) if tool_args else []
                })
                
                tool = next((t for t in tools if t.name == tool_name), None)
                if tool:
                    try:
                        result = tool._run(**tool_args)
                        logger.info("Tool executed successfully", extra={
                            "tool_name": tool_name,
                            "result_length": len(str(result))
                        })
                    except Exception as e:
                        logger.error("Tool execution failed", extra={
                            "tool_name": tool_name,
                            "error": str(e)
                        }, exc_info=True)
                        result = f"Error: {str(e)}"
                    
                    tool_messages.append(ToolMessage(content=str(result), tool_call_id=tool_id))
                else:
                    logger.warning("Tool not found", extra={"tool_name": tool_name})
                    tool_messages.append(ToolMessage(content=f"Tool {tool_name} not found", tool_call_id=tool_id))
        
        return {"messages": tool_messages}
    
    def should_continue(state: AgentState):
        """Decide if we should continue."""
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return "end"
    
    # Build graph
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
    graph.add_edge("tools", "agent")
    
    return graph.compile(), tools


def run_sync_agent():
    """Run the sync agent to update chunks."""
    print("\n" + "=" * 60)
    print("🔄 CODE SYNC AGENT")
    print("=" * 60)
    
    agent, tools = create_agent("sync")
    
    repos_list = "\n".join([f"  - {r}" for r in MANAGED_REPOS])
    
    prompt = f"""You are a Code Sync Agent. Keep our code knowledge base up to date.

MANAGED REPOSITORIES:
{repos_list}

YOUR TASK:
1. Call get_sync_status to see current state
2. Call bulk_sync_all to sync ALL repos in one fast operation
3. Report the results

Use bulk_sync_all - it handles everything efficiently in one call.
Start now."""

    print(f"\n📤 Starting sync task...")
    
    step = 0
    max_steps = 10  # Should complete in ~3-4 steps now
    
    for event in agent.stream(
        {"messages": [HumanMessage(content=prompt)]},
        {"recursion_limit": 50},
        stream_mode="values"
    ):
        step += 1
        messages = event.get("messages", [])
        
        if messages:
            last = messages[-1]
            
            if hasattr(last, 'tool_calls') and last.tool_calls:
                for tc in last.tool_calls:
                    print(f"\n🔧 [{step}] Tool: {tc.get('name')}")
                    args = tc.get('args', {})
                    if args and str(args) != "{}":
                        print(f"     Args: {json.dumps(args, default=str)[:100]}")
            elif hasattr(last, 'content') and last.content:
                content = str(last.content)
                if not content.startswith('{'):
                    print(f"\n💬 [{step}] Agent: {content[:300]}...")
        
        if step >= max_steps:
            print(f"\n⏹️  Max steps reached ({max_steps})")
            break
    
    print("\n✅ Sync complete!")


def run_qa_agent(question: str):
    """Run the Q&A agent to answer questions about the code."""
    print("\n" + "=" * 60)
    print("❓ CODE Q&A AGENT")
    print("=" * 60)
    
    agent, tools = create_agent("query")
    
    prompt = f"""You are a Code Research Agent. You must analyze codebases and write comprehensive answers.

TASK: {question}

INSTRUCTIONS:
1. Call analyze_full_stack to get complete info about ALL repositories
2. After receiving the data, WRITE your answer based on what you learned
3. Do NOT call more tools after analyze_full_stack - just write your answer

Call analyze_full_stack now."""

    print(f"\n📤 Task: {question}")
    print("\n" + "-" * 40)
    
    step = 0
    max_steps = 25  # Allow more steps for research
    final_answer = None
    
    for event in agent.stream(
        {"messages": [HumanMessage(content=prompt)]},
        {"recursion_limit": 60},
        stream_mode="values"
    ):
        step += 1
        messages = event.get("messages", [])
        
        if messages:
            last = messages[-1]
            msg_type = type(last).__name__
            
            if hasattr(last, 'tool_calls') and last.tool_calls:
                for tc in last.tool_calls:
                    print(f"🔧 [{step}] {tc.get('name')}: {str(tc.get('args', {}))[:60]}...")
            elif msg_type == "ToolMessage":
                content = str(last.content)[:200]
                print(f"📥 [{step}] Tool result: {content}...")
            elif hasattr(last, 'content') and last.content:
                content = str(last.content)
                if not content.startswith('{') and len(content) > 100:
                    final_answer = content
                    print(f"\n💬 [{step}] Response received ({len(content)} chars)")
        
        if step >= max_steps:
            print(f"\n⏹️  Max steps reached")
            break
    
    # Print final answer
    if final_answer:
        print("\n" + "=" * 60)
        print("📋 FINAL ANSWER:")
        print("=" * 60)
        print(final_answer)
    
    print("\n✅ Research complete!")


def run_document_agent(topic: str, output_file: str = None):
    """
    Run the document generation agent with Plan-Execute pattern.
    
    Pattern: Research → Plan → Execute Sections → Compile
    Each phase has clear completion criteria - no churning.
    """
    print("\n" + "=" * 60)
    print("📝 DOCUMENT GENERATION AGENT")
    print("=" * 60)
    print(f"   Topic: {topic}")
    print(f"   Output: {output_file or 'auto-generated'}")
    
    agent, tools = create_agent("document")
    
    # Generate output filename if not provided
    if not output_file:
        safe_topic = topic.lower().replace(" ", "_")[:30]
        output_file = f"{safe_topic}_{datetime.now().strftime('%Y%m%d')}"
    
    # Enhanced Multi-Pass prompt (simplified - use analyze_full_stack which works)
    prompt = f"""You are a Technical Documentation Agent using enhanced multi-pass generation.

TOPIC: {topic}

FOLLOW THIS EXACT SEQUENCE:

PHASE 1 - RESEARCH:
Call analyze_full_stack to get comprehensive data about all repositories.

PHASE 2 - CREATE PLAN:
After reviewing the data, call create_multi_pass_plan with:
- title: A clear document title for "{topic}"
- topic: "{topic}"

PHASE 3 - GENERATE ARCHITECTURE:
Call write_section with section_id="architecture" and write a comprehensive architecture overview based on analyze_full_stack data.

PHASE 4 - GENERATE MODULE DOCS:
For each section (core_modules, adapters, tools):
- Call write_section with detailed API documentation based on the analyze_full_stack data
- Include classes, methods, parameters, examples

PHASE 5 - GENERATE EXAMPLES:
Call write_section with section_id="examples" and practical code examples

PHASE 6 - COMPILE:
After ALL sections are written, call compile_document with filename: "{output_file}"

RULES:
- Complete each phase before moving to next
- Use analyze_full_stack data to inform your writing
- Be comprehensive but structured
- When compile_document succeeds, you are DONE

Start with PHASE 1: call analyze_full_stack now."""

    print("\n🚀 Starting document generation...")
    print("-" * 40)
    
    step = 0
    max_steps = 15  # Quick test: 1 research + 1 plan + 3 sections + 1 compile = ~6 steps, allow 2x for safety
    current_phase = "PREPROCESSING"
    
    for event in agent.stream(
        {"messages": [HumanMessage(content=prompt)]},
        {"recursion_limit": 80},
        stream_mode="values"
    ):
        step += 1
        messages = event.get("messages", [])
        
        if messages:
            last = messages[-1]
            
            if hasattr(last, 'tool_calls') and last.tool_calls:
                for tc in last.tool_calls:
                    tool_name = tc.get('name')
                    
                    # Track phase
                    if tool_name == "analyze_codebase_structure":
                        current_phase = "PREPROCESSING"
                    elif tool_name == "create_semantic_clusters":
                        current_phase = "PREPROCESSING"
                    elif tool_name == "build_dependency_graph":
                        current_phase = "PREPROCESSING"
                    elif tool_name == "calculate_pagerank_scores":
                        current_phase = "PREPROCESSING"
                    elif tool_name == "create_multi_pass_plan" or tool_name == "create_document_plan":
                        current_phase = "PLANNING"
                    elif tool_name == "set_preprocessing_data":
                        current_phase = "STORING_DATA"
                    elif tool_name == "write_section":
                        current_phase = "WRITING"
                    elif tool_name == "compile_document":
                        current_phase = "COMPILING"
                    
                    args = tc.get('args', {})
                    arg_preview = ""
                    if 'section_id' in args:
                        arg_preview = f"({args['section_id']})"
                    elif 'title' in args:
                        arg_preview = f"({args['title'][:40]}...)"
                    elif 'filename' in args:
                        arg_preview = f"({args['filename']})"
                    
                    print(f"📌 [{current_phase}] {tool_name} {arg_preview}")
            
            elif isinstance(last, ToolMessage):
                content = str(last.content)
                # Show tool response (truncated)
                print(f"📥 [{step}] Tool response: {content[:200]}...")
                # Check for document saved message
                if "document_saved" in content:
                    try:
                        result = json.loads(content)
                        if result.get("status") == "document_saved":
                            print(f"\n✅ Document saved: {result.get('path')}")
                            print(f"   Sections: {result.get('sections_compiled')}")
                            print(f"   Size: {result.get('total_chars')} chars")
                            break
                    except:
                        pass
                # Check for plan created
                elif "plan_created" in content:
                    print(f"   📋 Plan created successfully")
                # Check for section written
                elif "section_written" in content or "all_sections_complete" in content:
                    try:
                        result = json.loads(content)
                        completed = result.get("completed", 0)
                        total = result.get("total", 0)
                        print(f"   ✏️ Progress: {completed}/{total} sections")
                    except:
                        pass
            
            elif hasattr(last, 'content') and last.content and not hasattr(last, 'tool_calls'):
                # Agent generated text response without tool calls - might be stopping
                content = str(last.content)
                if len(content) > 50:
                    print(f"💬 [{step}] Agent text (no tools): {content[:200]}...")
        
        if step >= max_steps:
            logger.warning(f"Max steps reached ({max_steps}) - stopping to prevent infinite loop", extra={
                "max_steps": max_steps,
                "current_phase": current_phase
            })
            print(f"\n⚠️ Max steps reached ({max_steps}) - stopping")
            break
    
    print("\n" + "=" * 60)
    print("📝 Document generation complete!")


def run_status_check():
    """Quick status check without full agent."""
    print("\n" + "=" * 60)
    print("📊 STATUS CHECK")
    print("=" * 60)
    
    import httpx
    
    try:
        # Get sync status
        r = httpx.post(f"{MCP_SERVER}/tools/get_sync_status", json={}, timeout=10)
        status = json.loads(r.json().get("content", "{}"))
        
        print("\n📦 Sync Status:")
        if "repos" in status:
            for repo in status["repos"]:
                print(f"   • {repo['repo']}: {repo.get('files_synced', 0)} files, {repo.get('total_chunks', 0)} chunks")
        else:
            print(f"   {status}")
        
        # Get storage stats
        r = httpx.post(f"{MCP_SERVER}/tools/get_storage_stats", json={}, timeout=10)
        stats = json.loads(r.json().get("content", "{}"))
        
        print(f"\n💾 Storage Stats:")
        print(f"   Repos tracked: {stats.get('repos_tracked', 0)}")
        print(f"   Total files: {stats.get('total_files', 0)}")
        print(f"   Total chunks: {stats.get('total_chunks', 0)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Make sure the MCP server is running: python tools/server.py")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AutonomousFlow Agent")
    parser.add_argument("command", choices=["sync", "query", "status", "document"], 
                       help="Command to run")
    parser.add_argument("--question", "-q", type=str,
                       help="Question for query command")
    parser.add_argument("--topic", "-t", type=str,
                       help="Topic for document command")
    parser.add_argument("--output", "-o", type=str,
                       help="Output filename for document command")
    
    args = parser.parse_args()
    
    if args.command == "sync":
        run_sync_agent()
    elif args.command == "query":
        if not args.question:
            print("Error: --question is required for query command")
            return
        run_qa_agent(args.question)
    elif args.command == "status":
        run_status_check()
    elif args.command == "document":
        if not args.topic:
            print("Error: --topic is required for document command")
            return
        run_document_agent(args.topic, args.output)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Default to status check
        run_status_check()
    else:
        main()

