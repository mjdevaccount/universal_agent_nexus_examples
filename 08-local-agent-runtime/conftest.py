"""
Pytest fixtures for 08-local-agent-runtime

December 2025 pattern: Ephemeral MCP servers with automatic cleanup
"""

import pytest
import sys
from pathlib import Path

# Add tests/helpers to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tests" / "helpers"))

from mcp_server_runner import run_mcp_servers_for_example


@pytest.fixture(scope="function")
def mcp_servers():
    """
    Fixture that starts MCP servers for tests and cleans up automatically.
    
    Usage:
        def test_something(mcp_servers):
            filesystem_url = mcp_servers["filesystem"]
            git_url = mcp_servers["git"]
            # Use servers
    """
    with run_mcp_servers_for_example("08", [
        {
            "module": "mcp_servers.filesystem.server:app",
            "port_name": "test-filesystem",
            "name": "filesystem"
        },
        {
            "module": "mcp_servers.git.server:app",
            "port_name": "test-git",
            "name": "git"
        }
    ]) as server_urls:
        yield server_urls
    # Servers automatically stopped here


@pytest.fixture(scope="function")
def filesystem_server():
    """Single filesystem server fixture."""
    from mcp_server_runner import run_mcp_server_in_process
    
    with run_mcp_server_in_process(
        "mcp_servers.filesystem.server:app",
        port_name="test-filesystem"
    ) as url:
        yield url


@pytest.fixture(scope="function")
def git_server():
    """Single git server fixture."""
    from mcp_server_runner import run_mcp_server_in_process
    
    with run_mcp_server_in_process(
        "mcp_servers.git.server:app",
        port_name="test-git"
    ) as url:
        yield url

