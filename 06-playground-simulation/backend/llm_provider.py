"""
LLM Provider using Universal Agent Fabric + danielmiessler Fabric.

Architecture:
1. Universal Agent Fabric - Compiles role definitions
2. danielmiessler Fabric - Handles LLM provider abstraction
"""

import subprocess
import os
from typing import List, Dict, Optional
from pathlib import Path
import yaml


class AgentFabricProvider:
    """
    LLM provider using YOUR Universal Agent Fabric for roles
    + danielmiessler Fabric for LLM calls.
    
    Setup:
        # Install danielmiessler Fabric
        fabric --setup
        
        # Your Universal Agent Fabric is already installed
        pip install universal-agent-fabric
    
    Usage:
        provider = AgentFabricProvider(archetype="bully")
        response = await provider.complete(context, scenario)
    """
    
    def __init__(
        self,
        archetype: str,
        fabric_dir: str = "../fabric_archetypes",
    ):
        self.archetype = archetype
        self.fabric_dir = Path(fabric_dir)
        self.role_def = self._load_role()
        self.fabric_available = self._check_fabric_cli()
    
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
    
    def _load_role(self) -> Dict:
        """Load role definition from Universal Agent Fabric."""
        role_path = self.fabric_dir / f"{self.archetype}.yaml"
        
        if not role_path.exists():
            raise ValueError(f"Archetype not found: {self.archetype}")
        
        with open(role_path) as f:
            return yaml.safe_load(f)
    
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
        system_prompt = self.role_def["system_prompt_template"]
        
        # Combine with context
        full_prompt = f"{system_prompt}\n\nScenario: {scenario}\n\nConversation:\n{context}\n\nYou say:"
        
        if self.fabric_available:
            return await self._complete_with_fabric(full_prompt, temperature)
        else:
            return await self._complete_with_openai(full_prompt, system_prompt, context, scenario, temperature)
    
    async def _complete_with_fabric(self, full_prompt: str, temperature: float) -> str:
        """Call danielmiessler Fabric for LLM execution."""
        import asyncio
        
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
        import asyncio
        
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
        }


def create_provider(archetype: str) -> AgentFabricProvider:
    """Factory function to create providers."""
    return AgentFabricProvider(archetype=archetype)

