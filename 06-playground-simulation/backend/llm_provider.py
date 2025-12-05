"""
LLM Provider with ultra-lightweight function calling.

Supports:
1. Gemma 2B Function Calling (2GB) - RECOMMENDED
2. danielmiessler Fabric CLI
3. Direct OpenAI (fallback)

Architecture:
- Role definitions from Universal Agent Fabric
- Capabilities from ontology/capabilities/
- Policy enforcement from Universal Agent Architecture
"""

import json
import re
import subprocess
import asyncio
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path
import yaml

from capabilities_impl import CAPABILITY_REGISTRY


def get_project_root() -> Path:
    """Get the project root directory."""
    current = Path(__file__).resolve().parent
    if current.name == "backend":
        return current.parent
    return current


class GemmaToolCallingProvider:
    """
    Ultra-lightweight function calling using Gemma 2B (2GB).
    
    Features:
    - Native function calling support
    - 80 tokens/sec on M1 Mac
    - Works with Ollama (free)
    - 2GB model size
    
    Setup:
        ollama pull gemma:2b-instruct
    """
    
    def __init__(self, archetype: str, project_root: Optional[Path] = None):
        self.archetype = archetype
        
        if project_root is None:
            project_root = get_project_root()
        self.project_root = project_root
        
        # Load role definition
        self.role_def = self._load_role()
        
        # Get capabilities for this archetype
        self.capabilities = self._get_archetype_capabilities()
        
        # Build tool schema
        self.tools = self._build_tool_schema()
        
        # Check if Ollama is available
        self.ollama_available = self._check_ollama()
    
    def _load_role(self) -> Dict:
        """Load role definition from fabric archetypes."""
        role_path = self.project_root / "fabric_archetypes" / f"{self.archetype}.yaml"
        if not role_path.exists():
            raise ValueError(f"Archetype not found: {self.archetype}")
        with open(role_path) as f:
            return yaml.safe_load(f)
    
    def _get_archetype_capabilities(self) -> Dict[str, Callable]:
        """Get capability functions for this archetype."""
        cap_names = self.role_def.get("default_capabilities", ["speak"])
        return {
            name: CAPABILITY_REGISTRY[name]
            for name in cap_names
            if name in CAPABILITY_REGISTRY
        }
    
    def _build_tool_schema(self) -> List[Dict]:
        """Convert capabilities to tool schema for Gemma."""
        tools = []
        cap_dir = self.project_root / "ontology" / "capabilities"
        
        for cap_name in self.capabilities.keys():
            cap_file = cap_dir / f"{cap_name}.yaml"
            if cap_file.exists():
                with open(cap_file) as f:
                    cap_def = yaml.safe_load(f)
                    tools.append({
                        "name": cap_def["name"],
                        "description": cap_def["description"],
                        "parameters": cap_def.get("config_template", {}).get("inputs", []),
                    })
        
        return tools
    
    def _check_ollama(self) -> bool:
        """Check if Ollama is available."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def complete(self, context: str, scenario: str, temperature: float = 0.7) -> str:
        """
        Generate response with optional tool calling.
        
        Flow:
        1. Build prompt with role + tools
        2. Generate response via Ollama
        3. If tool call detected, execute and get final answer
        4. Return response
        """
        if not self.ollama_available:
            return await self._fallback_complete(context, scenario, temperature)
        
        # Build system prompt with tools
        tools_json = json.dumps(self.tools, indent=2) if self.tools else "No tools available."
        
        system_prompt = f"""{self.role_def.get('system_prompt_template', '')}

You have access to these functions:
{tools_json}

To use a function, respond with:
<functioncall> {{"name": "function_name", "arguments": {{"arg": "value"}}}} </functioncall>

If no function is needed, respond naturally as your character.
Keep responses VERY SHORT (1-2 sentences max)."""

        # Build full prompt
        prompt = f"""{system_prompt}

Scenario: {scenario}

Recent conversation:
{context}

Your response:"""

        try:
            # Call Ollama
            response = await self._call_ollama(prompt, temperature)
            
            # Check for function call
            if "<functioncall>" in response:
                tool_call = self._parse_tool_call(response)
                
                if tool_call:
                    # Execute tool
                    tool_result = await self._execute_tool(tool_call)
                    
                    # Get final response
                    final_prompt = f"""{prompt}

{response}

Tool result: {json.dumps(tool_result)}

Based on this result, provide your final brief response (1-2 sentences):"""
                    
                    response = await self._call_ollama(final_prompt, temperature)
            
            # Clean up response
            return self._clean_response(response)
            
        except Exception as e:
            return f"[{self.role_def.get('name', 'Agent')}]: {str(e)[:50]}"
    
    async def _call_ollama(self, prompt: str, temperature: float) -> str:
        """Call Ollama API."""
        result = await asyncio.to_thread(
            lambda: subprocess.run(
                [
                    "ollama", "run", "gemma:2b-instruct",
                    "--nowordwrap",
                ],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=30
            )
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Ollama error: {result.stderr}")
        
        return result.stdout.strip()
    
    def _parse_tool_call(self, response: str) -> Optional[Dict]:
        """Extract function call from response."""
        match = re.search(
            r'<functioncall>\s*({.*?})\s*</functioncall>',
            response,
            re.DOTALL
        )
        
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                return None
        return None
    
    async def _execute_tool(self, tool_call: Dict) -> Dict:
        """Execute capability function."""
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("arguments", {})
        
        capability_func = self.capabilities.get(tool_name)
        
        if not capability_func:
            return {"error": f"Tool '{tool_name}' not found"}
        
        try:
            if asyncio.iscoroutinefunction(capability_func):
                result = await capability_func(**tool_args)
            else:
                result = capability_func(**tool_args)
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _clean_response(self, response: str) -> str:
        """Clean up response text."""
        # Remove any remaining function call tags
        response = re.sub(r'<functioncall>.*?</functioncall>', '', response, flags=re.DOTALL)
        # Remove extra whitespace
        response = ' '.join(response.split())
        return response.strip()
    
    async def _fallback_complete(self, context: str, scenario: str, temperature: float) -> str:
        """Fallback to OpenAI if Ollama not available."""
        try:
            from openai import OpenAI
            client = OpenAI()
            
            response = await asyncio.to_thread(
                lambda: client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": self.role_def.get("system_prompt_template", "")},
                        {"role": "user", "content": f"Scenario: {scenario}\n\nConversation:\n{context}\n\nYou say:"}
                    ],
                    max_tokens=60,
                    temperature=temperature
                )
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"[{self.role_def.get('name', 'Agent')} thinking...] {str(e)[:50]}"
    
    def get_info(self) -> Dict:
        """Get provider info."""
        return {
            "provider": "gemma-2b-function-calling" if self.ollama_available else "openai-fallback",
            "archetype": self.archetype,
            "model_size": "2GB" if self.ollama_available else "cloud",
            "tools": [t["name"] for t in self.tools],
            "role": self.role_def.get("name"),
            "ollama_available": self.ollama_available,
        }


class FabricCLIProvider:
    """
    LLM provider using danielmiessler Fabric CLI.
    
    Setup:
        pip install fabric
        fabric --setup  # Select Ollama or other provider
    """
    
    def __init__(self, archetype: str, project_root: Optional[Path] = None):
        self.archetype = archetype
        
        if project_root is None:
            project_root = get_project_root()
        self.project_root = project_root
        self.role_def = self._load_role()
        self.fabric_available = self._check_fabric()
    
    def _load_role(self) -> Dict:
        """Load role definition."""
        role_path = self.project_root / "fabric_archetypes" / f"{self.archetype}.yaml"
        if not role_path.exists():
            raise ValueError(f"Archetype not found: {self.archetype}")
        with open(role_path) as f:
            return yaml.safe_load(f)
    
    def _check_fabric(self) -> bool:
        """Check if Fabric CLI is available."""
        try:
            subprocess.run(["fabric", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    async def complete(self, context: str, scenario: str, temperature: float = 0.9) -> str:
        """Generate completion via Fabric CLI."""
        system_prompt = self.role_def.get("system_prompt_template", "")
        full_prompt = f"{system_prompt}\n\nScenario: {scenario}\n\nConversation:\n{context}\n\nYou say:"
        
        if self.fabric_available:
            try:
                result = await asyncio.to_thread(
                    lambda: subprocess.run(
                        ["fabric", "--temperature", str(temperature)],
                        input=full_prompt,
                        capture_output=True,
                        text=True,
                        check=True,
                        timeout=30
                    )
                )
                return result.stdout.strip()
            except Exception as e:
                return f"[Error: {str(e)[:50]}]"
        
        return "[Fabric CLI not available]"
    
    def get_info(self) -> Dict:
        """Get provider info."""
        return {
            "provider": "fabric-cli",
            "archetype": self.archetype,
            "role": self.role_def.get("name"),
            "fabric_available": self.fabric_available,
        }


# Default provider factory
def create_provider(archetype: str, provider_type: str = "gemma") -> Any:
    """
    Create LLM provider for archetype.
    
    Args:
        archetype: Name of archetype (bully, shy_kid, mediator, etc.)
        provider_type: "gemma" (recommended), "fabric", or "auto"
    
    Returns:
        Provider instance
    """
    if provider_type == "gemma":
        return GemmaToolCallingProvider(archetype)
    elif provider_type == "fabric":
        return FabricCLIProvider(archetype)
    else:
        # Auto-detect best available
        provider = GemmaToolCallingProvider(archetype)
        if provider.ollama_available:
            return provider
        
        fabric_provider = FabricCLIProvider(archetype)
        if fabric_provider.fabric_available:
            return fabric_provider
        
        # Return Gemma provider anyway (will fallback to OpenAI)
        return provider
