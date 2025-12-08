"""
Local Agent Runtime
Demonstrates: Fabric → Nexus → LangGraph with MCP tools + Ollama

December 2025 Stack:
- MCP standardized (November 2025 spec)
- Tool introspection built-in
- Ollama with function calling
- LangGraph production-ready
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import BaseTool
import operator

from universal_agent_tools.ollama_tools import (
    MCPTool,
    MCPToolLoader,
    create_llm_with_tools,
    parse_tool_calls_from_content,
)

# Try to import observability helper
try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from universal_agent_tools.observability import setup_observability
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False


# ===== STATE =====

class AgentState(TypedDict):
    """Agent state for LangGraph."""
    messages: Annotated[Sequence[BaseMessage], operator.add]


# ===== LANGGRAPH NODES =====

def agent_node(state: AgentState, llm, tools: list[BaseTool]):
    """Agent node: LLM decides what to do."""
    messages = state["messages"]
    
    if llm is None:
        # Mock response for demo
        return {
            "messages": [
                AIMessage(
                    content="I'll help you with that. Let me use the available tools.",
                    tool_calls=[{
                        "name": "git_status",
                        "args": {"repo_path": "."},
                        "id": "call_1"
                    }]
                )
            ]
        }
    
    # Invoke LLM
    try:
        response = llm.invoke(messages)
        
        # Check if response has tool_calls (from bind_tools)
        if hasattr(response, "tool_calls") and response.tool_calls:
            return {"messages": [response]}
        
        # CRITICAL FIX: Parse tool calls from content if Ollama returned them as JSON
        # Ollama's /v1 API sometimes returns tool calls in content instead of tool_calls
        if hasattr(response, "content") and response.content:
            parsed_tool_calls = parse_tool_calls_from_content(response.content, tools)
            if parsed_tool_calls:
                # Create new AIMessage with tool_calls
                from langchain_core.messages import AIMessage
                response_with_tools = AIMessage(
                    content=response.content,  # Keep original content
                    tool_calls=parsed_tool_calls
                )
                return {"messages": [response_with_tools]}
        
        # If no tool calls, return the response as-is
        return {"messages": [response]}
        
    except Exception as e:
        # Fallback: return a simple response
        return {
            "messages": [
                AIMessage(
                    content=f"I understand. Available tools: {', '.join([t.name for t in tools])}",
                )
            ]
        }


def tool_node(state: AgentState, tools: list[BaseTool]):
    """Tool node: Execute tool calls."""
    last_message = state["messages"][-1]
    
    tool_messages = []
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call.get("args", {})
            tool_id = tool_call.get("id", tool_name)
            
            # Find the tool
            tool = next((t for t in tools if t.name == tool_name), None)
            
            if tool:
                # Verify tool has required attributes
                if not hasattr(tool, '_server_url'):
                    tool_messages.append(
                        ToolMessage(
                            content=f"Error: Tool {tool_name} missing _server_url attribute. Tool type: {type(tool).__name__}",
                            tool_call_id=tool_id
                        )
                    )
                    continue
                
                # Execute tool
                try:
                    result = tool._run(**tool_args)
                except Exception as e:
                    result = f"Error executing tool: {str(e)}"
                
                tool_messages.append(
                    ToolMessage(
                        content=str(result),
                        tool_call_id=tool_id
                    )
                )
            else:
                tool_messages.append(
                    ToolMessage(
                        content=f"Tool {tool_name} not found",
                        tool_call_id=tool_id
                    )
                )
    
    return {"messages": tool_messages}


def should_continue(state: AgentState):
    """Conditional edge: Continue to tools or end."""
    last_message = state["messages"][-1]
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    else:
        return "end"


# ===== GRAPH BUILDING =====

def create_agent_graph(tools: list[BaseTool], llm):
    """
    Create LangGraph agent with MCP tools.
    
    This is what the compiler would generate from Fabric YAML.
    """
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("agent", lambda state: agent_node(state, llm, tools))
    graph.add_node("tools", lambda state: tool_node(state, tools))
    
    # Add edges
    graph.set_entry_point("agent")
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    graph.add_edge("tools", "agent")
    
    # Compile without checkpointer for simple execution
    # (Checkpointer requires thread_id config, use MemorySaver only when needed)
    return graph.compile()


# ===== MAIN RUNTIME =====

def main():
    """Main runtime - demonstrates the full stack."""
    # Setup observability
    if OBSERVABILITY_AVAILABLE:
        setup_observability("local-agent-runtime")
    
    print("[START] Local Agent Runtime - December 2025 Stack")
    print("=" * 60)
    
    # 1. Load tools from MCP servers (auto-discovery)
    print("\n1. Loading tools from MCP servers...")
    filesystem_tools = MCPToolLoader.load_from_server("http://localhost:8144/mcp")
    git_tools = MCPToolLoader.load_from_server("http://localhost:8145/mcp")
    all_tools = filesystem_tools + git_tools
    
    print(f"   [OK] Loaded {len(all_tools)} tools:")
    for tool in all_tools:
        print(f"      - {tool.name}: {tool.description}")
    
    # 2. Create LLM with tools (Ollama function calling)
    print("\n2. Initializing Ollama LLM with function calling...")
    llm, _ = create_llm_with_tools(all_tools, model="llama3.2:11b")
    print("   [OK] LLM ready with tool binding")
    
    # 3. Create LangGraph agent
    print("\n3. Building LangGraph agent...")
    agent = create_agent_graph(all_tools, llm)
    print("   [OK] Agent graph compiled")
    
    # 4. Run agent
    print("\n4. Running agent...")
    print("   (This would be invoked from the compiler-generated code)")
    
    # Example invocation
    result = agent.invoke({
        "messages": [
            HumanMessage(content="Find all TODO comments in the codebase")
        ]
    })
    
    print("\n[OK] Agent execution complete!")
    print(f"   Messages: {len(result['messages'])}")
    
    return agent


if __name__ == "__main__":
    main()

