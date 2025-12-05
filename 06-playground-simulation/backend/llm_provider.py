"""
LLM Provider using Universal Agent Fabric + danielmiessler Fabric.

Architecture:
1. Universal Agent Fabric - Compiles role definitions via FabricBuilder
2. danielmiessler Fabric - Handles LLM provider abstraction

This module bridges the compiled Fabric specs to actual LLM calls.
"""

import subprocess
import asyncio
from typing import Dict, Optional
from pathlib import Path
import yaml

from schemas import CompiledAgent


def get_project_root() -> Path:
    """Get the project root directory (06-playground-simulation)."""
    current = Path(__file__).resolve().parent
    
    if current.name == "backend":
        return current.parent
    
    while current != current.parent:
        if (current / "fabric_archetypes").exists():
            return current
        current = current.parent
    
    cwd = Path.cwd()
    if (cwd / "fabric_archetypes").exists():
        return cwd
    if (cwd / "06-playground-simulation" / "fabric_archetypes").exists():
        return cwd / "06-playground-simulation"
    
    return Path(__file__).resolve().parent.parent


class AgentFabricProvider:
    """
    LLM provider using YOUR Universal Agent Fabric for roles
    + danielmiessler Fabric for LLM calls.
    
    Usage:
        provider = AgentFabricProvider(archetype="bully")
        response = await provider.complete(context, scenario)
    """
    
    def __init__(
        self,
        archetype: str,
        project_root: Optional[Path] = None,
        use_compiler: bool = True,
    ):
        self.archetype = archetype
        
        if project_root is None:
            project_root = get_project_root()
        
        self.project_root = Path(project_root)
        self.fabric_dir = self.project_root / "fabric_archetypes"
        self.use_compiler = use_compiler
        self.compiled_agent: Optional[CompiledAgent] = None
        
        # Try to use the full compiler, fall back to simple loading
        if use_compiler:
            try:
                from fabric_compiler import get_compiler
                compiler = get_compiler()
                self.compiled_agent = compiler.compile_agent(archetype)
                self.role_def = {
                    "name": self.compiled_agent.name,
                    "system_prompt_template": self.compiled_agent.system_prompt,
                    "base_template": self.compiled_agent.base_template,
                    "default_capabilities": self.compiled_agent.capabilities,
                }
            except Exception as e:
                # Fall back to simple loading
                print(f"Compiler fallback: {e}")
                self.compiled_agent = None
                self.role_def = self._load_role_simple()
        else:
            self.role_def = self._load_role_simple()
        
        self.fabric_available = self._check_fabric_cli()
    
    def _load_role_simple(self) -> Dict:
        """Load role definition directly from YAML (fallback)."""
        role_path = self.fabric_dir / f"{self.archetype}.yaml"
        
        if not role_path.exists():
            raise ValueError(f"Archetype not found: {self.archetype} (looked in {role_path})")
        
        with open(role_path) as f:
            return yaml.safe_load(f)
    
    def _check_fabric_cli(self) -> bool:
        """Verify danielmiessler Fabric CLI is installed."""
        try:
            subprocess.run(
                ["fabric", "--version"],
                capture_output=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    async def complete(
        self,
        context: str,
        scenario: str,
        temperature: float = 0.9,
    ) -> str:
        """
        Generate completion using:
        1. System prompt from YOUR Fabric (role definition)
        2. LLM call via danielmiessler Fabric (provider abstraction)
        
        Args:
            context: Conversation history
            scenario: Current scenario
            temperature: Sampling temperature
        
        Returns:
            Generated text
        """
        # Build prompt from YOUR Fabric role definition
        system_prompt = self.role_def.get("system_prompt_template", "")
        
        # Combine with context
        full_prompt = f"{system_prompt}\n\nScenario: {scenario}\n\nConversation:\n{context}\n\nYou say:"
        
        if self.fabric_available:
            return await self._complete_with_fabric(full_prompt, temperature)
        else:
            return await self._complete_with_openai(full_prompt, system_prompt, context, scenario, temperature)
    
    async def _complete_with_fabric(self, full_prompt: str, temperature: float) -> str:
        """Call danielmiessler Fabric for LLM execution."""
        try:
            result = await asyncio.to_thread(
                lambda: subprocess.run(
                    [
                        "fabric",
                        "--temperature", str(temperature),
                    ],
                    input=full_prompt,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=30
                )
            )
            
            return result.stdout.strip()
        
        except subprocess.TimeoutExpired:
            return "[Error: Request timed out]"
        except subprocess.CalledProcessError as e:
            return f"[Error: {e.stderr[:100]}]"
        except Exception as e:
            return f"[Error: {str(e)[:100]}]"
    
    async def _complete_with_openai(
        self, 
        full_prompt: str, 
        system_prompt: str, 
        context: str, 
        scenario: str,
        temperature: float
    ) -> str:
        """Fallback to direct OpenAI call if Fabric CLI not available."""
        try:
            from openai import OpenAI
            client = OpenAI()
            
            response = await asyncio.to_thread(
                lambda: client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
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
            "provider": "universal-agent-fabric + fabric-cli" if self.fabric_available else "universal-agent-fabric + openai",
            "archetype": self.archetype,
            "role_name": self.role_def.get("name"),
            "base_template": self.role_def.get("base_template"),
            "capabilities": self.role_def.get("default_capabilities", []),
            "fabric_cli_available": self.fabric_available,
            "compiled": self.compiled_agent is not None,
            "domains": self.compiled_agent.domains if self.compiled_agent else [],
            "governance_rules": self.compiled_agent.governance_rules if self.compiled_agent else [],
        }


def create_provider(archetype: str, use_compiler: bool = True) -> AgentFabricProvider:
    """Factory function to create providers."""
    return AgentFabricProvider(archetype=archetype, use_compiler=use_compiler)
