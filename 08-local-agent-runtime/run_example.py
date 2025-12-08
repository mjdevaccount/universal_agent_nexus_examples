"""
Single-entry command for 08-local-agent-runtime example

December 2025 pattern: Mode B - Demo/example run
Starts MCP servers, runs example, tears down automatically.

Usage:
    python run_example.py
"""

import sys
import signal
from pathlib import Path

# Add tests/helpers to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tests" / "helpers"))

from mcp_server_runner import run_mcp_servers_for_example
from runtime.agent_runtime import MCPToolLoader, create_agent_graph, create_llm_with_tools
from langchain_core.messages import HumanMessage


def main():
    """Run the example with automatic server management."""
    print("=" * 60)
    print("08-local-agent-runtime Example")
    print("=" * 60)
    print("\n[MODE B] Demo mode: Starting servers, running example, cleaning up...")
    
    # Use demo ports (different from test ports)
    with run_mcp_servers_for_example("08", [
        {
            "module": "mcp_servers.filesystem.server:app",
            "port_name": "demo-filesystem",
            "name": "filesystem"
        },
        {
            "module": "mcp_servers.git.server:app",
            "port_name": "demo-git",
            "name": "git"
        }
    ]) as server_urls:
        
        print(f"\n[OK] Servers running:")
        for name, url in server_urls.items():
            print(f"   {name}: {url}")
        
        # Load tools
        print("\n[1] Loading tools from MCP servers...")
        filesystem_tools = MCPToolLoader.load_from_server(server_urls["filesystem"])
        git_tools = MCPToolLoader.load_from_server(server_urls["git"])
        all_tools = filesystem_tools + git_tools
        
        print(f"   [OK] Loaded {len(all_tools)} tools:")
        for tool in all_tools:
            print(f"      - {tool.name}")
        
        # Create LLM
        print("\n[2] Initializing Ollama LLM...")
        llm, _ = create_llm_with_tools(all_tools, model="qwen3:8b")
        if llm is None:
            print("   [WARN] Ollama not available, using mock mode")
        else:
            print("   [OK] LLM ready")
        
        # Create agent
        print("\n[3] Building LangGraph agent...")
        agent = create_agent_graph(all_tools, llm)
        print("   [OK] Agent graph compiled")
        
        # Run example
        print("\n[4] Running example query...")
        print("   Query: 'Check git status'")
        
        result = agent.invoke({
            "messages": [
                HumanMessage(content="Check git status")
            ]
        })
        
        print(f"\n[OK] Agent execution complete!")
        print(f"   Messages: {len(result['messages'])}")
        
        # Show last message
        if result['messages']:
            last_msg = result['messages'][-1]
            if hasattr(last_msg, 'content'):
                print(f"\n   Response: {last_msg.content[:200]}...")
    
    print("\n[OK] All servers stopped (automatic cleanup)")
    print("=" * 60)


if __name__ == "__main__":
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\n\n[INTERRUPT] Cleaning up servers...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPT] Cleaning up servers...")
        sys.exit(0)

