"""
Pytest configuration for playground tests.
"""

import pytest
import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))


@pytest.fixture
def archetypes_dir():
    """Path to fabric_archetypes directory."""
    return Path(__file__).parent.parent / "fabric_archetypes"


@pytest.fixture
def capabilities_dir():
    """Path to ontology/capabilities directory."""
    return Path(__file__).parent.parent / "ontology" / "capabilities"


@pytest.fixture
def domains_dir():
    """Path to ontology/domains directory."""
    return Path(__file__).parent.parent / "ontology" / "domains"


@pytest.fixture
def policies_dir():
    """Path to policy/rules directory."""
    return Path(__file__).parent.parent / "policy" / "rules"

