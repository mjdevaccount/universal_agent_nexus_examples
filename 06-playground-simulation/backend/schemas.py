"""
Schemas for Universal Agent Fabric integration.

These wrap and extend the upstream universal_agent_fabric schemas
for playground-specific validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Re-export upstream schemas for convenience
from universal_agent_fabric import (
    Role,
    Capability,
    Domain,
    GovernanceRule,
    FabricSpec,
)


class PlaygroundArchetype(BaseModel):
    """
    Extended archetype with playground-specific metadata.
    
    Wraps universal_agent_fabric.Role with UI metadata.
    """
    # Core role fields (maps to universal_agent_fabric.Role)
    name: str = Field(..., description="Display name for the archetype")
    base_template: str = Field(..., description="Graph template (react_loop, planning_loop, simple_response)")
    system_prompt_template: str = Field(..., description="System prompt for LLM")
    default_capabilities: List[str] = Field(default_factory=list, description="Required capability names")
    
    # Playground-specific extensions
    personality: Optional[Dict[str, int]] = Field(
        default_factory=dict,
        description="Personality traits for UI visualization (0-10 scale)"
    )
    ui_role: Optional[str] = Field(None, description="Short role description for UI")
    
    def to_fabric_role(self) -> Role:
        """Convert to upstream Role schema."""
        return Role(
            name=self.name,
            base_template=self.base_template,
            system_prompt_template=self.system_prompt_template,
            default_capabilities=self.default_capabilities,
        )


class PlaygroundCapability(BaseModel):
    """
    Extended capability with playground-specific config.
    
    Wraps universal_agent_fabric.Capability.
    """
    name: str
    description: str
    protocol: str = "local"  # local, mcp, http, subprocess
    config_template: Optional[Dict[str, Any]] = None
    
    def to_fabric_capability(self) -> Capability:
        """Convert to upstream Capability schema."""
        return Capability(
            name=self.name,
            description=self.description,
            protocol=self.protocol,
            config_template=self.config_template,
        )


class PlaygroundGovernance(BaseModel):
    """
    Collection of governance rules for the playground.
    """
    rules: List[GovernanceRule] = Field(default_factory=list)


class CompiledAgent(BaseModel):
    """
    Result of compiling an archetype through FabricBuilder.
    """
    name: str
    archetype: str
    system_prompt: str
    base_template: str
    capabilities: List[str]
    domains: List[str] = Field(default_factory=list)
    governance_rules: List[str] = Field(default_factory=list)
    compiled: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

