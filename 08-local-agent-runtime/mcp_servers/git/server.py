"""
MCP Git Server
Implements Model Context Protocol for Git operations.

December 2025 MCP Spec compliant.
"""

from mcp.server import Server
from mcp.types import Tool
from typing import Any
import subprocess
from pathlib import Path
import json


server = Server("git-server")


@server.tool()
def git_status(repo_path: str = ".") -> str:
    """
    Get Git repository status.
    
    Args:
        repo_path: Path to Git repository
        
    Returns:
        Git status output
    """
    try:
        repo = Path(repo_path)
        if not (repo / ".git").exists():
            return f"Error: Not a Git repository: {repo_path}"
        
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        
        return result.stdout if result.stdout else "Working tree clean"
    except Exception as e:
        return f"Error: {str(e)}"


@server.tool()
def git_commit(repo_path: str, message: str) -> str:
    """
    Create a Git commit.
    
    Args:
        repo_path: Path to Git repository
        message: Commit message
        
    Returns:
        Commit result
    """
    try:
        repo = Path(repo_path)
        if not (repo / ".git").exists():
            return f"Error: Not a Git repository: {repo_path}"
        
        # Stage all changes
        subprocess.run(
            ["git", "add", "-A"],
            cwd=repo,
            capture_output=True,
            timeout=5
        )
        
        # Commit
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        
        return f"Committed: {message}"
    except Exception as e:
        return f"Error: {str(e)}"


@server.tool()
def git_diff(repo_path: str = ".") -> str:
    """
    Get Git diff of changes.
    
    Args:
        repo_path: Path to Git repository
        
    Returns:
        Git diff output
    """
    try:
        repo = Path(repo_path)
        if not (repo / ".git").exists():
            return f"Error: Not a Git repository: {repo_path}"
        
        result = subprocess.run(
            ["git", "diff"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        
        return result.stdout if result.stdout else "No changes"
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    import uvicorn
    from mcp.server.fastapi import create_app
    
    app = create_app(server)
    uvicorn.run(app, host="0.0.0.0", port=8001)

