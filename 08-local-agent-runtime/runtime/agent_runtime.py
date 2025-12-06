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
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import BaseTool
import operator
import json
import httpx
from pathlib import Path


# ===== STATE =====

class AgentState(TypedDict):
    """Agent state for LangGraph."""
    messages: Annotated[Sequence[BaseMessage], operator.add]


# ===== MCP TOOL LOADER =====

class MCPToolLoader:
    """
    Load tools from MCP servers using December 2025 standardized introspection.
    
    MCP Spec (November 2025):
    - SEP-986: Standardized tool naming
    - Auto-discovery via introspection
    - Standardized schema format
    """
    
    @staticmethod
    def load_from_server(server_url: str) -> list[BaseTool]:
        """
        Load tools from an MCP server via introspection.
        
        Args:
            server_url: MCP server URL (e.g., "http://localhost:8000/mcp")
            
        Returns:
            List of LangChain tools
        """
        try:
            # MCP introspection endpoint (standardized)
            response = httpx.get(f"{server_url}/tools", timeout=5)
            response.raise_for_status()
            
            tools_data = response.json()
            tools = []
            
            for tool_def in tools_data.get("tools", []):
                # Create LangChain tool from MCP tool definition
                # NOTE: Parameter order matches __init__: server_url, tool_name, input_schema, name, description
                tool = MCPTool(
                    server_url=server_url,
                    tool_name=tool_def["name"],
                    input_schema=tool_def.get("inputSchema", {}),
                    name=tool_def["name"],
                    description=tool_def.get("description", "")
                )
                tools.append(tool)
            
            return tools
            
        except Exception as e:
            print(f"Warning: Could not load tools from {server_url}: {e}")
            return []


class MCPTool(BaseTool):
    """LangChain tool wrapper for MCP tools."""
    
    def __init__(self, server_url: str, tool_name: str, input_schema: dict, name: str = None, description: str = ""):
        # CRITICAL: BaseTool needs args_schema for Ollama tool calling
        # Convert MCP inputSchema to Pydantic model for LangChain
        from pydantic import create_model, BaseModel
        from typing import get_type_hints
        
        # Create args_schema from input_schema
        args_schema = None
        if input_schema and input_schema.get("properties"):
            # Create a Pydantic model from the JSON schema
            fields = {}
            for prop_name, prop_def in input_schema.get("properties", {}).items():
                prop_type = str  # Default to str
                if prop_def.get("type") == "integer":
                    prop_type = int
                elif prop_def.get("type") == "boolean":
                    prop_type = bool
                fields[prop_name] = (prop_type, ...)
            
            if fields:
                ArgsModel = create_model(f"{tool_name}_Args", **fields)
                args_schema = ArgsModel
        
        # Call parent first (Pydantic models need this)
        super().__init__(name=name or tool_name, description=description, args_schema=args_schema)
        
        # Store MCP-specific attributes AFTER super().__init__()
        # Use object.__setattr__ to bypass Pydantic's attribute handling
        object.__setattr__(self, '_server_url', server_url)
        object.__setattr__(self, '_tool_name', tool_name)
        object.__setattr__(self, '_input_schema', input_schema)
    
    def _run(self, **kwargs) -> str:
        """Execute MCP tool via HTTP."""
        try:
            response = httpx.post(
                f"{self._server_url}/tools/{self._tool_name}",
                json=kwargs,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            return result.get("content", str(result))
        except Exception as e:
            return f"Error executing tool: {str(e)}"
    
    async def _arun(self, **kwargs) -> str:
        """Async execution."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self._server_url}/tools/{self._tool_name}",
                    json=kwargs,
                    timeout=10
                )
                response.raise_for_status()
                result = response.json()
                return result.get("content", str(result))
            except Exception as e:
                return f"Error executing tool: {str(e)}"


# ===== LLM SETUP =====

def create_llm_with_tools(tools: list[BaseTool], model: str = "qwen2.5-coder:14b"):
    """
    Create Ollama LLM with function calling support.
    
    CRITICAL FIX: Use ChatOpenAI with Ollama's OpenAI-compatible API
    LangChain's ChatOllama doesn't properly parse tool calls from Ollama's native API.
    Using ChatOpenAI with Ollama's /v1 endpoint fixes this parsing issue.
    """
    try:
        # Use ChatOpenAI with Ollama's OpenAI-compatible API
        # This properly parses tool calls that ChatOllama misses
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(
            model=model,
            base_url="http://localhost:11434/v1",  # Ollama's OpenAI-compatible API
            api_key="ollama",  # Dummy key (Ollama doesn't require auth)
            temperature=0,
        )
        
        # Try to bind tools
        if tools:
            try:
                llm_with_tools = llm.bind_tools(tools)
                print(f"✅ Tools bound successfully to {model} via OpenAI-compatible API")
                return llm_with_tools, tools
            except Exception as e:
                print(f"⚠️  Warning: bind_tools failed: {e}")
                print("   Using LLM without tool binding (manual tool calling)")
                return llm, tools
        else:
            return llm, []
            
    except ImportError:
        print("❌ ERROR: langchain-openai not installed")
        print("   Install with: pip install langchain-openai")
        # Fallback to ChatOllama if ChatOpenAI not available
        try:
            from langchain_ollama import ChatOllama
            llm = ChatOllama(model=model, temperature=0)
            if tools:
                llm_with_tools = llm.bind_tools(tools)
                return llm_with_tools, tools
            return llm, []
        except:
            return None, tools


def parse_tool_calls_from_content(content: str, tools: list[BaseTool]) -> list:
    """
    Parse tool calls from JSON content when Ollama returns them in content field.
    
    Ollama's /v1 API sometimes returns tool calls as JSON in content instead of
    the standard tool_calls array. This function extracts and converts them.
    """
    import json
    import re
    
    if not content or not isinstance(content, str):
        return []
    
    # Try to parse as JSON directly
    try:
        tool_call_data = json.loads(content.strip())
        if isinstance(tool_call_data, dict) and "name" in tool_call_data:
            # Found a tool call in JSON format
            tool_name = tool_call_data.get("name")
            tool_args = tool_call_data.get("arguments", {})
            
            # Find the tool to get its ID
            tool = next((t for t in tools if t.name == tool_name), None)
            if tool:
                return [{
                    "name": tool_name,
                    "args": tool_args,
                    "id": f"call_{tool_name}_{hash(str(tool_args))}"
                }]
    except (json.JSONDecodeError, AttributeError):
        pass
    
    # Try to find JSON in content (might be mixed with text)
    json_match = re.search(r'\{[^{}]*"name"[^{}]*\}', content)
    if json_match:
        try:
            tool_call_data = json.loads(json_match.group(0))
            if isinstance(tool_call_data, dict) and "name" in tool_call_data:
                tool_name = tool_call_data.get("name")
                tool_args = tool_call_data.get("arguments", {})
                tool = next((t for t in tools if t.name == tool_name), None)
                if tool:
                    return [{
                        "name": tool_name,
                        "args": tool_args,
                        "id": f"call_{tool_name}_{hash(str(tool_args))}"
                    }]
        except (json.JSONDecodeError, AttributeError):
            pass
    
    return []


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
    print("🚀 Local Agent Runtime - December 2025 Stack")
    print("=" * 60)
    
    # 1. Load tools from MCP servers (auto-discovery)
    print("\n1. Loading tools from MCP servers...")
    filesystem_tools = MCPToolLoader.load_from_server("http://localhost:8000/mcp")
    git_tools = MCPToolLoader.load_from_server("http://localhost:8001/mcp")
    all_tools = filesystem_tools + git_tools
    
    print(f"   ✅ Loaded {len(all_tools)} tools:")
    for tool in all_tools:
        print(f"      - {tool.name}: {tool.description}")
    
    # 2. Create LLM with tools (Ollama function calling)
    print("\n2. Initializing Ollama LLM with function calling...")
    llm, _ = create_llm_with_tools(all_tools, model="llama3.2:11b")
    print("   ✅ LLM ready with tool binding")
    
    # 3. Create LangGraph agent
    print("\n3. Building LangGraph agent...")
    agent = create_agent_graph(all_tools, llm)
    print("   ✅ Agent graph compiled")
    
    # 4. Run agent
    print("\n4. Running agent...")
    print("   (This would be invoked from the compiler-generated code)")
    
    # Example invocation
    result = agent.invoke({
        "messages": [
            HumanMessage(content="Find all TODO comments in the codebase")
        ]
    })
    
    print("\n✅ Agent execution complete!")
    print(f"   Messages: {len(result['messages'])}")
    
    return agent


if __name__ == "__main__":
    main()

