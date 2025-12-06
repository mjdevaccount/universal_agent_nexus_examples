"""
Compiler Bridge: Fabric → LangGraph with MCP Tools

This module demonstrates how Universal Agent Nexus would compile
Fabric YAML to LangGraph runtime with MCP tool integration.

December 2025: Aligned with compiler architecture.
"""

from pathlib import Path
import yaml
from typing import Dict, List, Any
from runtime.agent_runtime import MCPToolLoader, create_agent_graph, create_llm_with_tools


class FabricToLangGraphCompiler:
    """
    Compiles Fabric YAML to LangGraph runtime.
    
    This is what Universal Agent Nexus would generate.
    """
    
    def __init__(self, fabric_yaml_path: str):
        self.fabric_yaml_path = Path(fabric_yaml_path)
        self.spec = self._load_fabric_spec()
    
    def _load_fabric_spec(self) -> Dict:
        """Load Fabric YAML specification."""
        with open(self.fabric_yaml_path) as f:
            return yaml.safe_load(f)
    
    def compile(self) -> Any:
        """
        Compile Fabric spec to LangGraph runtime.
        
        Returns:
            Compiled LangGraph agent
        """
        # 1. Extract tools from Fabric spec
        tools = self._extract_tools()
        
        # 2. Load tools from MCP servers
        mcp_tools = self._load_mcp_tools(tools)
        
        # 3. Create LLM with tools
        role = self.spec["roles"][0]  # Use first role
        system_prompt = role["system_prompt_template"]
        llm, _ = create_llm_with_tools(mcp_tools, model="llama3.2:11b")
        
        # 4. Build LangGraph agent
        agent = create_agent_graph(mcp_tools, llm)
        
        return agent
    
    def _extract_tools(self) -> List[Dict]:
        """Extract tool definitions from Fabric spec."""
        return self.spec.get("tools", [])
    
    def _load_mcp_tools(self, tool_defs: List[Dict]) -> List:
        """Load tools from MCP servers based on Fabric tool definitions."""
        all_tools = []
        
        for tool_def in tool_defs:
            if tool_def.get("protocol") == "mcp":
                server_url = tool_def["config"]["server_url"]
                tools = MCPToolLoader.load_from_server(server_url)
                all_tools.extend(tools)
        
        return all_tools
    
    def generate_code(self, output_path: str):
        """
        Generate Python code for LangGraph runtime.
        
        This is what `nexus compile --target langgraph` would produce.
        """
        code = f'''"""
Generated LangGraph Runtime
Compiled from: {self.fabric_yaml_path}

Run: python {Path(output_path).name}
"""

from runtime.agent_runtime import (
    MCPToolLoader, 
    create_agent_graph, 
    create_llm_with_tools
)

def main():
    # Load tools from MCP servers
    tools = []
'''
        
        # Add tool loading for each MCP server
        mcp_servers = set()
        for tool_def in self.spec.get("tools", []):
            if tool_def.get("protocol") == "mcp":
                server_url = tool_def["config"]["server_url"]
                if server_url not in mcp_servers:
                    mcp_servers.add(server_url)
                    code += f'''    tools.extend(MCPToolLoader.load_from_server("{server_url}"))
'''
        
        code += '''
    # Create LLM with tools
    llm, _ = create_llm_with_tools(tools, model="llama3.2:11b")
    
    # Build agent
    agent = create_agent_graph(tools, llm)
    
    return agent

if __name__ == "__main__":
    agent = main()
    print("✅ Agent compiled and ready!")
'''
        
        with open(output_path, 'w') as f:
            f.write(code)
        
        print(f"✅ Generated: {output_path}")


if __name__ == "__main__":
    # Example: Compile Fabric YAML to LangGraph
    compiler = FabricToLangGraphCompiler("local_agent.yaml")
    agent = compiler.compile()
    
    # Generate code
    compiler.generate_code("runtime/generated_agent.py")
    
    print("\n✅ Compilation complete!")
    print("   Run: python runtime/generated_agent.py")

