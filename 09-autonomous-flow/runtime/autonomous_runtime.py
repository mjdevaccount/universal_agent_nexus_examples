"""
AutonomousFlow Runtime
Executes the regenerated workflow using discovered tools.

This runtime loads the regenerated manifest and executes it using
LangGraph with MCP tools and Ollama.
"""

import sys
import io
from pathlib import Path
import yaml

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "08-local-agent-runtime" / "runtime"))

from universal_agent_nexus.runtime import get_registry
from agent_runtime import MCPToolLoader, create_agent_graph, create_llm_with_tools
from langchain_core.messages import HumanMessage

# Try to import observability helper
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from universal_agent_tools.observability import setup_observability
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False


def load_regenerated_manifest():
    """Load the regenerated manifest."""
    manifest_path = Path(__file__).parent.parent / "autonomous_flow_regenerated.yaml"
    with open(manifest_path, 'r') as f:
        return yaml.safe_load(f)


def create_runtime_from_manifest(manifest):
    """
    Create LangGraph runtime from regenerated manifest.
    
    This demonstrates how the compiler would generate the runtime.
    The agent can use tools autonomously to accomplish tasks.
    """
    print("[BUILD] Creating runtime from regenerated manifest...")
    
    # Extract tool configurations from manifest
    tool_configs = manifest.get('tools', [])
    
    # Load tools from MCP servers (deduplicate by server)
    all_tools = []
    seen_servers = set()
    seen_tools = set()
    
    for tool_config in tool_configs:
        server_url = tool_config['config']['server_url']
        tool_name = tool_config['name']
        
        # Only load from each server once
        if server_url not in seen_servers:
            tools = MCPToolLoader.load_from_server(server_url)
            seen_servers.add(server_url)
            
            # Deduplicate tools by name
            for tool in tools:
                if tool.name not in seen_tools:
                    all_tools.append(tool)
                    seen_tools.add(tool.name)
    
    print(f"   [OK] Loaded {len(all_tools)} unique tools from manifest")
    print(f"   [TOOLS] Available tools: {', '.join([t.name for t in all_tools[:10]])}...")
    
    # Get LLM model from manifest
    router_config = manifest.get('routers', [{}])[0]
    model = router_config.get('model', 'qwen3')
    
    # Create LLM with tools - this enables autonomous tool calling
    print(f"   [OK] Initializing Ollama LLM: {model}")
    llm, _ = create_llm_with_tools(all_tools, model=model)
    
    # Create agent graph - this supports autonomous tool selection and execution
    print("   [OK] Building LangGraph agent with tool support...")
    agent = create_agent_graph(all_tools, llm)
    
    return agent, all_tools


def main():
    """Main runtime execution."""
    # Setup observability
    if OBSERVABILITY_AVAILABLE:
        setup_observability("autonomous-flow")
    
    print("[START] AutonomousFlow Runtime")
    print("=" * 60)
    
    # 1. Load regenerated manifest
    print("\n1. Loading regenerated manifest...")
    manifest = load_regenerated_manifest()
    print(f"   [OK] Loaded manifest: {manifest['name']} v{manifest['version']}")
    print(f"   [OK] Tools in manifest: {len(manifest.get('tools', []))}")
    
    # 2. Create runtime
    print("\n2. Creating runtime from manifest...")
    agent, tools = create_runtime_from_manifest(manifest)
    print("   [OK] Runtime ready")
    
    # 3. Execute with repository discovery task
    print("\n3. Executing agent with repository discovery task...")
    print("   [WARN] Note: Tool calling may require model support for function calling")
    print("   [TIP] If tools aren't called, the model may need manual prompting")
    
    task_prompt = """You are an autonomous agent with access to GitHub and Qdrant tools.

TASK: Find mjdevaccount's GitHub repositories with "universal_agent" prefix, chunk their Python files, and store in Qdrant.

STEP 1: Search GitHub for repositories
- Call github_search_repos with query="universal_agent user:mjdevaccount"

STEP 2: List Python files in universal_agent_nexus
- Call github_list_files with repo="mjdevaccount/universal_agent_nexus" and path="src" or path="nexus"
- Look for .py files

STEP 3: Get a Python file and chunk it
- Call github_get_file to get a .py file (NOT pyproject.toml or README)
- Call chunk_and_store_python_content with the file content, file_name, and repo_name

STEP 4: Report what you chunked.

IMPORTANT: Only chunk actual .py Python files, not config files.

Start now with Step 1."""
    
    print(f"\n[SEND] Sending task to agent...")
    
    # Stream to see progress in real-time
    messages = []
    step_count = 0
    max_steps = 20  # Limit steps for full task
    
    for event in agent.stream(
        {"messages": [HumanMessage(content=task_prompt)]},
        {"recursion_limit": 100},
        stream_mode="values"
    ):
        step_count += 1
        messages = event.get("messages", [])
        
        # Print latest message
        if messages:
            last = messages[-1]
            msg_type = type(last).__name__
            print(f"\n[STEP] Step {step_count} ({msg_type}):")
            
            if hasattr(last, 'tool_calls') and last.tool_calls:
                for tc in last.tool_calls:
                    print(f"   [TOOL] Tool call: {tc.get('name')} - {tc.get('args', {})}")
            elif hasattr(last, 'content') and last.content:
                content = str(last.content)[:300]
                print(f"   [MSG] {content}")
        
        # Stop after max steps for testing
        if step_count >= max_steps:
            print(f"\n[STOP] Stopping after {max_steps} steps...")
            break
        
        # Also stop if we got a successful chunk result
        if hasattr(last, 'content') and 'chunks_created' in str(last.content):
            print(f"\n[OK] Chunking complete! Stopping.")
            break
    
    result = {"messages": messages}
    
    # Debug: Check final state
    print(f"\n[DEBUG] Final state after {step_count} steps...")
    for i, msg in enumerate(result['messages'], 1):
        msg_type = type(msg).__name__
        print(f"\n   Message {i} ({msg_type}):")
        print(f"      Has tool_calls attr: {hasattr(msg, 'tool_calls')}")
        if hasattr(msg, 'tool_calls'):
            print(f"      tool_calls value: {msg.tool_calls}")
            print(f"      tool_calls type: {type(msg.tool_calls)}")
            print(f"      tool_calls is None: {msg.tool_calls is None}")
            if msg.tool_calls:
                print(f"      [OK] {len(msg.tool_calls)} tool calls found!")
                for tc in msg.tool_calls:
                    print(f"         - {tc.get('name', 'unknown')}: {tc.get('args', {})}")
            else:
                print(f"      [EMPTY] tool_calls is empty/None")
        if hasattr(msg, 'invalid_tool_calls'):
            print(f"      invalid_tool_calls: {msg.invalid_tool_calls}")
        if hasattr(msg, 'content'):
            content_preview = str(msg.content)[:200]
            print(f"      Content: {content_preview}...")
    
    # 4. Display results
    print("\n4. Results:")
    print("=" * 60)
    for i, message in enumerate(result['messages'], 1):
        msg_type = type(message).__name__
        content = message.content[:200] if len(message.content) > 200 else message.content
        print(f"\nMessage {i} ({msg_type}):")
        print(f"  {content}")
        if hasattr(message, 'tool_calls') and message.tool_calls:
            print(f"  Tool calls: {len(message.tool_calls)}")
    
    print("\n[OK] Execution complete!")
    return agent


if __name__ == "__main__":
    try:
        agent = main()
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

