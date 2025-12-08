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
    Ultra-lightweight function calling using Gemma 2B (2GB) or Qwen3 (8B).
    
    Features:
    - Native function calling support
    - Works with Ollama (free)
    - Auto-detects best available model
    
    Setup:
        ollama pull gemma:2b-instruct  # 2GB, faster
        ollama pull qwen3:8b           # 5.2GB, better quality
    """
    
    def __init__(self, archetype: str, project_root: Optional[Path] = None, model: Optional[str] = None):
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
        
        # Auto-detect best model if not specified (defaults to qwen3:8b)
        if model:
            self.model = model
        else:
            self.model = self._detect_best_model()
    
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
                encoding='utf-8',
                errors='replace',
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _detect_best_model(self) -> str:
        """Auto-detect best available model. Prefers qwen3:8b for better quality."""
        if not self.ollama_available:
            return "qwen3:8b"  # Default preference
        
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=5
            )
            if result.returncode == 0:
                output = result.stdout.lower()
                # Prefer qwen3:8b for better quality, fallback to gemma
                if "qwen3:8b" in output:
                    return "qwen3:8b"
                elif "qwen3" in output:
                    # Find the exact qwen3 model name
                    for line in result.stdout.split('\n'):
                        if 'qwen3' in line.lower():
                            parts = line.split()
                            if parts:
                                return parts[0]  # Return the model name
                elif "gemma:2b-instruct" in output or "gemma:2b" in output:
                    return "gemma:2b-instruct"
        except Exception:
            pass
        
        return "qwen3:8b"  # Default to qwen3:8b
    
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

You can use functions if needed, but MOST OF THE TIME just speak naturally as your character.
Only use functions when you need to analyze or observe something specific.

Available functions: {', '.join([t['name'] for t in self.tools]) if self.tools else 'none'}

IMPORTANT: Speak naturally. Keep responses VERY SHORT (1-2 sentences max)."""

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
                    
                    # Get final response - use simpler prompt
                    final_prompt = f"""{self.role_def.get('system_prompt_template', '')}

Scenario: {scenario}

Recent conversation:
{context}

You analyzed the situation. Now respond naturally as your character (1-2 sentences max):"""
                    
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
                    "ollama", "run", self.model,
                    "--nowordwrap",
                ],
                input=prompt,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
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
        # Remove thinking/reasoning blocks (common in qwen3)
        response = re.sub(r'Thinking\.\.\..*?\.\.\.done thinking\.', '', response, flags=re.DOTALL | re.IGNORECASE)
        response = re.sub(r'Thinking\.\.\..*?Alright.*?done\.', '', response, flags=re.DOTALL | re.IGNORECASE)
        # Remove function call tags and content
        response = re.sub(r'<functioncall>.*?</functioncall>', '', response, flags=re.DOTALL)
        # Remove JSON-like function call syntax
        response = re.sub(r'\w+\([^)]*\)', '', response)
        # Remove artifacts like </start_of_turn>, <start_of_turn>, etc.
        response = re.sub(r'</?start_of_turn>', '', response, flags=re.IGNORECASE)
        response = re.sub(r'</?end_of_turn>', '', response, flags=re.IGNORECASE)
        # Remove standalone JSON objects that look like function calls
        response = re.sub(r'\{"name":\s*"[^"]+",\s*"arguments":\s*[^}]+\}', '', response)
        # Remove analyze_situation, speak, etc. as standalone words
        response = re.sub(r'\b(analyze_situation|observe_situation|speak)\b', '', response, flags=re.IGNORECASE)
        # Remove "Okay, the user wants me to..." style reasoning
        response = re.sub(r'Okay[^.]*\.\s*', '', response, flags=re.IGNORECASE)
        # Remove "Let me make sure..." style reasoning
        response = re.sub(r'Let me (make sure|check|think|confirm)[^.]*\.\s*', '', response, flags=re.IGNORECASE)
        # Remove "Wait, (maybe|perhaps|no)" style reasoning
        response = re.sub(r'Wait[^.]*\.\s*', '', response, flags=re.IGNORECASE)
        # Remove "Maybe I need to..." style reasoning
        response = re.sub(r'Maybe I (need to|should|can)[^.]*\.\s*', '', response, flags=re.IGNORECASE)
        # Remove "I should check..." style reasoning
        response = re.sub(r'I should (check|make sure|clarify)[^.]*\.\s*', '', response, flags=re.IGNORECASE)
        # Remove "So, I need to..." style reasoning
        response = re.sub(r'So[^.]*\.\s*', '', response, flags=re.IGNORECASE)
        # Remove "Alright, (that should work|done)" style endings
        response = re.sub(r'Alright[^.]*\.\s*', '', response, flags=re.IGNORECASE)
        # Remove extra whitespace and clean up
        response = ' '.join(response.split())
        # Remove leading/trailing punctuation artifacts
        response = response.strip('.,;:!?')
        # Take only the last sentence or two (usually the actual response)
        sentences = [s.strip() for s in response.split('.') if s.strip() and len(s.strip()) > 10]
        if len(sentences) > 2:
            # Keep last 2 sentences
            response = '. '.join(sentences[-2:])
        elif sentences:
            response = '. '.join(sentences)
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
        model_name = self.model if hasattr(self, 'model') else "gemma:2b-instruct"
        return {
            "provider": f"ollama-{model_name}" if self.ollama_available else "openai-fallback",
            "archetype": self.archetype,
            "model": model_name,
            "model_size": "5.2GB" if "qwen3" in model_name else "2GB" if self.ollama_available else "cloud",
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
            subprocess.run(
                ["fabric", "--version"],
                capture_output=True,
                check=True,
                encoding='utf-8',
                errors='replace'
            )
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
                        encoding='utf-8',
                        errors='replace',
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
def create_provider(archetype: str, provider_type: str = "auto", model: Optional[str] = None) -> Any:
    """
    Create LLM provider for archetype.
    
    Args:
        archetype: Name of archetype (bully, shy_kid, mediator, etc.)
        provider_type: "gemma", "fabric", or "auto" (default: auto-detect)
        model: Specific model to use (e.g., "qwen3:8b", "gemma:2b-instruct"). 
               If None, auto-detects best available.
    
    Returns:
        Provider instance
    """
    if provider_type == "gemma":
        return GemmaToolCallingProvider(archetype, model=model)
    elif provider_type == "fabric":
        return FabricCLIProvider(archetype)
    else:
        # Auto-detect best available
        provider = GemmaToolCallingProvider(archetype, model=model)
        if provider.ollama_available:
            return provider
        
        fabric_provider = FabricCLIProvider(archetype)
        if fabric_provider.fabric_available:
            return fabric_provider
        
        # Return provider anyway (will fallback to OpenAI)
        return provider
