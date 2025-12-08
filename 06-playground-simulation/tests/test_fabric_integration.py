"""
Tests for Universal Agent Fabric integration.

Validates that:
1. Archetypes match upstream schemas
2. Capabilities are properly defined
3. Domains correctly group capabilities
4. Governance rules are valid
5. Compiler produces valid output
"""

import pytest
from pathlib import Path
import yaml
import sys

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from universal_agent_fabric import (
    Role,
    Capability,
    Domain,
    GovernanceRule,
    FabricSpec,
    FabricBuilder,
)


# ===== PATHS =====

ARCHETYPES_DIR = Path(__file__).parent.parent / "fabric_archetypes"
CAPABILITIES_DIR = Path(__file__).parent.parent / "ontology" / "capabilities"
DOMAINS_DIR = Path(__file__).parent.parent / "ontology" / "domains"
POLICIES_DIR = Path(__file__).parent.parent / "policy" / "rules"


# ===== ARCHETYPE TESTS =====

def test_archetypes_are_valid_yaml():
    """Test all archetype files are valid YAML."""
    for yaml_file in ARCHETYPES_DIR.glob("*.yaml"):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
            assert data is not None, f"{yaml_file.name} is empty"


def test_archetypes_match_role_schema():
    """Test all archetypes match universal_agent_fabric.Role schema."""
    for yaml_file in ARCHETYPES_DIR.glob("*.yaml"):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
        
        # Should be able to create Role from archetype
        role = Role(**data)
        
        assert role.name, f"{yaml_file.name} missing name"
        assert role.base_template, f"{yaml_file.name} missing base_template"
        assert role.system_prompt_template, f"{yaml_file.name} missing system_prompt_template"


def test_all_expected_archetypes_exist():
    """Test that all expected archetypes are defined."""
    expected = {"bully", "shy_kid", "mediator", "joker", "teacher"}
    
    actual = {f.stem for f in ARCHETYPES_DIR.glob("*.yaml")}
    
    assert expected.issubset(actual), f"Missing archetypes: {expected - actual}"


# ===== CAPABILITY TESTS =====

def test_capabilities_are_valid_yaml():
    """Test all capability files are valid YAML."""
    if not CAPABILITIES_DIR.exists():
        pytest.skip("Capabilities directory not found")
    
    for yaml_file in CAPABILITIES_DIR.glob("*.yaml"):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
            assert data is not None, f"{yaml_file.name} is empty"


def test_capabilities_match_schema():
    """Test all capabilities match universal_agent_fabric.Capability schema."""
    if not CAPABILITIES_DIR.exists():
        pytest.skip("Capabilities directory not found")
    
    for yaml_file in CAPABILITIES_DIR.glob("*.yaml"):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
        
        cap = Capability(**data)
        
        assert cap.name, f"{yaml_file.name} missing name"
        assert cap.description, f"{yaml_file.name} missing description"


def test_archetype_capabilities_are_defined():
    """Test that capabilities referenced by archetypes are defined."""
    if not CAPABILITIES_DIR.exists():
        pytest.skip("Capabilities directory not found")
    
    # Load all defined capabilities
    defined_caps = set()
    for yaml_file in CAPABILITIES_DIR.glob("*.yaml"):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
            if data and "name" in data:
                defined_caps.add(data["name"])
    
    # Check each archetype's capabilities
    for yaml_file in ARCHETYPES_DIR.glob("*.yaml"):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
        
        required_caps = data.get("default_capabilities", [])
        for cap in required_caps:
            assert cap in defined_caps, f"Archetype {yaml_file.name} requires undefined capability: {cap}"


# ===== DOMAIN TESTS =====

def test_domains_are_valid_yaml():
    """Test all domain files are valid YAML."""
    if not DOMAINS_DIR.exists():
        pytest.skip("Domains directory not found")
    
    for yaml_file in DOMAINS_DIR.glob("*.yaml"):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
            assert data is not None, f"{yaml_file.name} is empty"


def test_domains_match_schema():
    """Test all domains match universal_agent_fabric.Domain schema."""
    if not DOMAINS_DIR.exists():
        pytest.skip("Domains directory not found")
    
    for yaml_file in DOMAINS_DIR.glob("*.yaml"):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
        
        domain = Domain(**data)
        
        assert domain.name, f"{yaml_file.name} missing name"
        assert domain.description, f"{yaml_file.name} missing description"


# ===== GOVERNANCE TESTS =====

def test_governance_rules_are_valid_yaml():
    """Test all governance rule files are valid YAML."""
    if not POLICIES_DIR.exists():
        pytest.skip("Policies directory not found")
    
    for yaml_file in POLICIES_DIR.glob("*.yaml"):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
            assert data is not None, f"{yaml_file.name} is empty"


def test_governance_rules_match_schema():
    """Test all governance rules match universal_agent_fabric.GovernanceRule schema."""
    if not POLICIES_DIR.exists():
        pytest.skip("Policies directory not found")
    
    for yaml_file in POLICIES_DIR.glob("*.yaml"):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
        
        if "rules" in data:
            for rule_data in data["rules"]:
                rule = GovernanceRule(**rule_data)
                assert rule.name, f"Rule in {yaml_file.name} missing name"
                assert rule.action, f"Rule {rule.name} missing action"


# ===== COMPILER TESTS =====

def test_compiler_can_load():
    """Test compiler can be imported and instantiated."""
    from fabric_compiler import get_compiler
    
    compiler = get_compiler()
    assert compiler is not None


def test_compiler_loads_capabilities():
    """Test compiler loads all defined capabilities."""
    from fabric_compiler import get_compiler
    
    compiler = get_compiler()
    caps = compiler.get_capabilities()
    
    # Should have at least the core capabilities
    assert "speak" in caps


def test_compiler_compiles_archetypes():
    """Test compiler can compile all archetypes."""
    from fabric_compiler import compile_archetype
    
    archetypes = ["bully", "shy_kid", "mediator", "joker", "teacher"]
    
    for archetype in archetypes:
        compiled = compile_archetype(archetype)
        
        assert compiled.name, f"{archetype} compilation missing name"
        assert compiled.system_prompt, f"{archetype} compilation missing system_prompt"
        assert compiled.compiled is True, f"{archetype} not marked as compiled"


# ===== PROVIDER TESTS =====

def test_provider_creation():
    """Test provider can be created for all archetypes."""
    from llm_provider import create_provider
    
    archetypes = ["bully", "shy_kid", "mediator", "joker", "teacher"]
    
    for archetype in archetypes:
        provider = create_provider(archetype)
        
        info = provider.get_info()
        assert info["archetype"] == archetype
        assert "provider" in info


def test_provider_with_compiler():
    """Test provider uses compiler when available."""
    from llm_provider import create_provider
    
    provider = create_provider("mediator")
    info = provider.get_info()
    
    # Provider should have basic info
    assert "archetype" in info
    assert "provider" in info


# ===== INTEGRATION TESTS =====

def test_full_fabric_spec_build():
    """Test building a complete FabricSpec with all components."""
    # Load an archetype
    with open(ARCHETYPES_DIR / "mediator.yaml") as f:
        role_data = yaml.safe_load(f)
    
    role = Role(**role_data)
    
    # Load capabilities
    capabilities = []
    if CAPABILITIES_DIR.exists():
        for yaml_file in CAPABILITIES_DIR.glob("*.yaml"):
            with open(yaml_file) as f:
                cap_data = yaml.safe_load(f)
                if cap_data:
                    capabilities.append(Capability(**cap_data))
    
    # Load domains
    domains = []
    if DOMAINS_DIR.exists():
        for yaml_file in DOMAINS_DIR.glob("*.yaml"):
            with open(yaml_file) as f:
                domain_data = yaml.safe_load(f)
                if domain_data:
                    domains.append(Domain(**domain_data))
    
    # Load governance
    governance = []
    if POLICIES_DIR.exists():
        for yaml_file in POLICIES_DIR.glob("*.yaml"):
            with open(yaml_file) as f:
                policy_data = yaml.safe_load(f)
                if policy_data and "rules" in policy_data:
                    for rule in policy_data["rules"]:
                        governance.append(GovernanceRule(**rule))
    
    # Build FabricSpec
    spec = FabricSpec(
        name="test_agent",
        role=role,
        domains=domains,
        governance=governance,
    )
    
    # Use FabricBuilder
    builder = FabricBuilder(spec)
    result = builder.build()
    
    assert result is not None, "FabricBuilder.build() returned None"

