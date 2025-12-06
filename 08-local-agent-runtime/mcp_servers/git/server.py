"""
MCP Git Server
Implements Model Context Protocol for Git operations.

December 2025 MCP Spec compliant.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import subprocess

app = FastAPI(title="MCP Git Server")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class ToolRequest(BaseModel):
    repo_path: Optional[str] = "."
    message: Optional[str] = None


# Tool definitions
TOOLS = [
    {
        "name": "git_status",
        "description": "Get Git repository status",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {"type": "string", "description": "Path to Git repository", "default": "."}
            }
        }
    },
    {
        "name": "git_commit",
        "description": "Create a Git commit",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {"type": "string", "description": "Path to Git repository", "default": "."},
                "message": {"type": "string", "description": "Commit message"}
            },
            "required": ["message"]
        }
    },
    {
        "name": "git_diff",
        "description": "Get Git diff of changes",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {"type": "string", "description": "Path to Git repository", "default": "."}
            }
        }
    }
]


@app.get("/mcp/tools")
async def list_tools():
    """MCP introspection endpoint."""
    return {"tools": TOOLS}


@app.post("/mcp/tools/git_status")
async def git_status(request: ToolRequest):
    """Get Git repository status."""
    repo_path = request.repo_path or "."
    
    try:
        repo = Path(repo_path)
        if not (repo / ".git").exists():
            return {"content": f"Error: Not a Git repository: {repo_path}"}
        
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return {"content": f"Error: {result.stderr}"}
        
        return {"content": result.stdout if result.stdout else "Working tree clean"}
    except Exception as e:
        return {"content": f"Error: {str(e)}"}


@app.post("/mcp/tools/git_commit")
async def git_commit(request: ToolRequest):
    """Create a Git commit."""
    if not request.message:
        raise HTTPException(status_code=400, detail="message is required")
    
    repo_path = request.repo_path or "."
    
    try:
        repo = Path(repo_path)
        if not (repo / ".git").exists():
            return {"content": f"Error: Not a Git repository: {repo_path}"}
        
        # Stage all changes
        subprocess.run(
            ["git", "add", "-A"],
            cwd=repo,
            capture_output=True,
            timeout=5
        )
        
        # Commit
        result = subprocess.run(
            ["git", "commit", "-m", request.message],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return {"content": f"Error: {result.stderr}"}
        
        return {"content": f"Committed: {request.message}"}
    except Exception as e:
        return {"content": f"Error: {str(e)}"}


@app.post("/mcp/tools/git_diff")
async def git_diff(request: ToolRequest):
    """Get Git diff of changes."""
    repo_path = request.repo_path or "."
    
    try:
        repo = Path(repo_path)
        if not (repo / ".git").exists():
            return {"content": f"Error: Not a Git repository: {repo_path}"}
        
        result = subprocess.run(
            ["git", "diff"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return {"content": f"Error: {result.stderr}"}
        
        return {"content": result.stdout if result.stdout else "No changes"}
    except Exception as e:
        return {"content": f"Error: {str(e)}"}


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "server": "git", "tools": len(TOOLS)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
