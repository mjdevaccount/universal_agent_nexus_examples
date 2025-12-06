"""
AutonomousFlow - Dynamic Workflow Discovery and Regeneration

This demonstrates how the Nexus compiler can be used to regenerate
workflows on the fly based on discovered tools.
"""

import sys
from pathlib import Path

# Add tools registry to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.registry.tool_registry import get_registry
import yaml


def discover_and_regenerate():
    """
    Discover tools and regenerate workflow manifest.
    
    This is the core concept: use discovery to drive compilation.
    """
    print("🔍 AutonomousFlow - Dynamic Workflow Discovery")
    print("=" * 60)
    
    # 1. Initialize tool registry
    print("\n1. Initializing tool registry...")
    registry = get_registry()
    
    # 2. Register MCP servers (from config or discovery)
    print("\n2. Registering MCP servers...")
    registry.register_server("filesystem", "http://localhost:8000/mcp")
    registry.register_server("git", "http://localhost:8001/mcp")
    registry.register_server("qdrant", "http://localhost:8002/mcp")
    registry.register_server("github", "http://localhost:8003/mcp")
    print(f"   ✅ Registered {len(registry.list_servers())} servers")
    
    # 3. Discover tools
    print("\n3. Discovering tools from MCP servers...")
    tools = registry.discover_tools()
    print(f"   ✅ Discovered {len(tools)} tools:")
    for tool in tools:
        print(f"      - {tool.name} ({tool.server_name}): {tool.description}")
    
    # 4. Load base manifest
    print("\n4. Loading base manifest...")
    manifest_path = Path(__file__).parent.parent / "autonomous_flow.yaml"
    with open(manifest_path, 'r') as f:
        manifest = yaml.safe_load(f)
    
    # 5. Regenerate manifest with discovered tools
    print("\n5. Regenerating manifest with discovered tools...")
    manifest['tools'] = []
    for tool in tools:
        tool_def = {
            "name": tool.name,
            "description": tool.description,
            "protocol": "mcp",
            "mcp_server": tool.server_name,
            "config": {
                "server_url": tool.server_url,
                "tool_name": tool.name,
                "input_schema": tool.input_schema
            }
        }
        manifest['tools'].append(tool_def)
    
    # 6. Save regenerated manifest
    regenerated_path = Path(__file__).parent.parent / "autonomous_flow_regenerated.yaml"
    with open(regenerated_path, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
    print(f"   ✅ Saved regenerated manifest to {regenerated_path.name}")
    
    # 7. Next step: Compile regenerated manifest
    print("\n6. Next: Compile regenerated manifest with Nexus")
    print("   Run: nexus compile autonomous_flow_regenerated.yaml --target langgraph --output runtime/agent.py")
    
    return manifest, tools


if __name__ == "__main__":
    try:
        manifest, tools = discover_and_regenerate()
        print("\n✅ Discovery and regeneration complete!")
        print(f"   Tools available: {len(tools)}")
        print(f"   Manifest ready for compilation")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

