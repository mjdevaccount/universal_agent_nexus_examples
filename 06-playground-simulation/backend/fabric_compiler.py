"""
Compile agent archetypes using Universal Agent Fabric.

This module integrates with the upstream universal_agent_fabric package
to properly compile role definitions into runtime-ready specifications.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
import os

from universal_agent_fabric import (
    FabricBuilder,
    FabricSpec,
    Role,
    Capability,
    Domain,
    GovernanceRule,
)

from schemas import PlaygroundArchetype, CompiledAgent


def get_project_root() -> Path:
    """Get the project root directory (06-playground-simulation)."""
    # Try to find project root from current file location
    current = Path(__file__).resolve().parent
    
    # If we're in backend/, go up one level
    if current.name == "backend":
        return current.parent
    
    # If running from tests, go up appropriately
    while current != current.parent:
        if (current / "fabric_archetypes").exists():
            return current
        current = current.parent
    
    # Fallback to current working directory
    cwd = Path.cwd()
    if (cwd / "fabric_archetypes").exists():
        return cwd
    if (cwd / "06-playground-simulation" / "fabric_archetypes").exists():
        return cwd / "06-playground-simulation"
    
    return Path(__file__).resolve().parent.parent


class PlaygroundCompiler:
    """
    Compiler that uses Universal Agent Fabric to build agent specs.
    
    Architecture:
        fabric_archetypes/*.yaml (Role definitions)
        ontology/capabilities/*.yaml (Capability definitions)
        ontology/domains/*.yaml (Domain definitions)
        policy/rules/*.yaml (Governance rules)
                ↓
        FabricBuilder.build()
                ↓
        CompiledAgent (runtime-ready)
    """
    
    def __init__(
        self,
        project_root: Optional[Path] = None,
    ):
        if project_root is None:
            project_root = get_project_root()
        
        self.project_root = Path(project_root)
        self.archetypes_dir = self.project_root / "fabric_archetypes"
        self.capabilities_dir = self.project_root / "ontology" / "capabilities"
        self.domains_dir = self.project_root / "ontology" / "domains"
        self.policies_dir = self.project_root / "policy" / "rules"
        
        # Cache loaded definitions
        self._capabilities: Dict[str, Capability] = {}
        self._domains: Dict[str, Domain] = {}
        self._governance_rules: List[GovernanceRule] = []
        
        # Load all definitions
        self._load_capabilities()
        self._load_domains()
        self._load_governance_rules()
    
    def _load_capabilities(self) -> None:
        """Load all capability definitions."""
        if not self.capabilities_dir.exists():
            return
            
        for yaml_file in self.capabilities_dir.glob("*.yaml"):
            try:
                with open(yaml_file) as f:
                    data = yaml.safe_load(f)
                    if data and "name" in data:
                        cap = Capability(**data)
                        self._capabilities[cap.name] = cap
            except Exception as e:
                print(f"Warning: Could not load capability {yaml_file}: {e}")
    
    def _load_domains(self) -> None:
        """Load all domain definitions."""
        if not self.domains_dir.exists():
            return
            
        for yaml_file in self.domains_dir.glob("*.yaml"):
            try:
                with open(yaml_file) as f:
                    data = yaml.safe_load(f)
                    if data and "name" in data:
                        # Convert capability dicts to Capability objects if needed
                        if "capabilities" in data:
                            caps = []
                            for cap in data["capabilities"]:
                                if isinstance(cap, str):
                                    # Reference by name - look up in loaded capabilities
                                    if cap in self._capabilities:
                                        caps.append(self._capabilities[cap])
                                elif isinstance(cap, dict):
                                    caps.append(Capability(**cap))
                                else:
                                    caps.append(cap)
                            data["capabilities"] = caps
                        
                        domain = Domain(**data)
                        self._domains[domain.name] = domain
            except Exception as e:
                print(f"Warning: Could not load domain {yaml_file}: {e}")
    
    def _load_governance_rules(self) -> None:
        """Load all governance rules."""
        if not self.policies_dir.exists():
            return
            
        for yaml_file in self.policies_dir.glob("*.yaml"):
            try:
                with open(yaml_file) as f:
                    data = yaml.safe_load(f)
                    if data and "rules" in data:
                        for rule_data in data["rules"]:
                            rule = GovernanceRule(**rule_data)
                            self._governance_rules.append(rule)
            except Exception as e:
                print(f"Warning: Could not load policy {yaml_file}: {e}")
    
    def _load_archetype(self, archetype: str) -> PlaygroundArchetype:
        """Load archetype definition from YAML."""
        role_path = self.archetypes_dir / f"{archetype}.yaml"
        
        if not role_path.exists():
            raise ValueError(f"Archetype not found: {archetype} (looked in {role_path})")
        
        with open(role_path) as f:
            data = yaml.safe_load(f)
        
        return PlaygroundArchetype(**data)
    
    def compile_agent(self, archetype: str) -> CompiledAgent:
        """
        Compile archetype into runtime-ready spec using FabricBuilder.
        
        Args:
            archetype: Name of archetype to compile
        
        Returns:
            CompiledAgent with all resolved dependencies
        """
        # Load archetype
        playground_arch = self._load_archetype(archetype)
        role = playground_arch.to_fabric_role()
        
        # Resolve capabilities for this role
        resolved_capabilities = [
            self._capabilities[cap_name]
            for cap_name in role.default_capabilities
            if cap_name in self._capabilities
        ]
        
        # Find domains that provide these capabilities
        resolved_domains = []
        for domain in self._domains.values():
            domain_cap_names = [c.name for c in domain.capabilities]
            if any(cap in domain_cap_names for cap in role.default_capabilities):
                resolved_domains.append(domain)
        
        # Build FabricSpec
        spec = FabricSpec(
            name=f"{archetype}_agent",
            role=role,
            domains=resolved_domains,
            governance=self._governance_rules,
        )
        
        # Use FabricBuilder to compile
        builder = FabricBuilder(spec)
        compiled_dict = builder.build()
        
        # Return as CompiledAgent
        return CompiledAgent(
            name=role.name,
            archetype=archetype,
            system_prompt=role.system_prompt_template,
            base_template=role.base_template,
            capabilities=role.default_capabilities,
            domains=[d.name for d in resolved_domains],
            governance_rules=[r.name for r in self._governance_rules],
            compiled=True,
            metadata={
                "fabric_output": compiled_dict,
                "personality": playground_arch.personality,
            }
        )
    
    def get_capabilities(self) -> Dict[str, Capability]:
        """Get all loaded capabilities."""
        return self._capabilities.copy()
    
    def get_domains(self) -> Dict[str, Domain]:
        """Get all loaded domains."""
        return self._domains.copy()
    
    def get_governance_rules(self) -> List[GovernanceRule]:
        """Get all loaded governance rules."""
        return self._governance_rules.copy()


# Singleton instance
_compiler: Optional[PlaygroundCompiler] = None


def get_compiler(reset: bool = False) -> PlaygroundCompiler:
    """Get singleton compiler instance."""
    global _compiler
    if _compiler is None or reset:
        _compiler = PlaygroundCompiler()
    return _compiler


def compile_archetype(archetype: str) -> CompiledAgent:
    """Convenience function to compile an archetype."""
    return get_compiler().compile_agent(archetype)
