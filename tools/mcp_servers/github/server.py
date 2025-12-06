"""
MCP GitHub Server
Implements Model Context Protocol for GitHub operations.

Features:
- Repository operations
- Issue management
- Pull request operations
- File content retrieval
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import json
import os

app = FastAPI(title="MCP GitHub Server")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# GitHub client (lazy import)
_github_client = None


def get_github_client():
    """Lazy import and initialize GitHub client."""
    global _github_client
    try:
        from github import Github
        token = os.getenv("GITHUB_TOKEN")
        
        # Try to get token from GitHub CLI if not set
        if not token:
            try:
                import subprocess
                result = subprocess.run(
                    ["gh", "auth", "token"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    token = result.stdout.strip()
                    # Set it in environment for future use
                    os.environ["GITHUB_TOKEN"] = token
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
        
        if not token:
            # Reset client to None so we can retry later
            _github_client = None
            return None, "GITHUB_TOKEN environment variable not set and GitHub CLI not available"
        
        # Re-initialize if we have a token (even if client was None before)
        if _github_client is None or not token:
            _github_client = Github(token)
        return _github_client, None
    except ImportError:
        return None, "PyGithub not installed. Install with: pip install PyGithub"


class ToolRequest(BaseModel):
    repo: Optional[str] = None  # owner/repo format
    path: Optional[str] = None
    issue_number: Optional[int] = None
    title: Optional[str] = None
    body: Optional[str] = None
    state: Optional[str] = "open"
    branch: Optional[str] = "main"
    query: Optional[str] = None


# Tool definitions
TOOLS = [
    {
        "name": "github_get_file",
        "description": "Get file contents from GitHub repository",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository in format owner/repo"},
                "path": {"type": "string", "description": "File path in repository"},
                "branch": {"type": "string", "description": "Branch name", "default": "main"}
            },
            "required": ["repo", "path"]
        }
    },
    {
        "name": "github_list_files",
        "description": "List files in a GitHub repository directory",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository in format owner/repo"},
                "path": {"type": "string", "description": "Directory path", "default": ""},
                "branch": {"type": "string", "description": "Branch name", "default": "main"}
            },
            "required": ["repo"]
        }
    },
    {
        "name": "github_create_issue",
        "description": "Create a GitHub issue",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository in format owner/repo"},
                "title": {"type": "string", "description": "Issue title"},
                "body": {"type": "string", "description": "Issue body"}
            },
            "required": ["repo", "title"]
        }
    },
    {
        "name": "github_list_issues",
        "description": "List issues in a GitHub repository",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository in format owner/repo"},
                "state": {"type": "string", "description": "Issue state (open/closed/all)", "default": "open"}
            },
            "required": ["repo"]
        }
    },
    {
        "name": "github_search_repos",
        "description": "Search GitHub repositories",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"]
        }
    }
]


@app.get("/mcp/tools")
async def list_tools():
    """MCP introspection endpoint."""
    return {"tools": TOOLS}


@app.post("/mcp/tools/github_get_file")
async def github_get_file(request: ToolRequest):
    """Get file contents from GitHub."""
    if not request.repo or not request.path:
        raise HTTPException(status_code=400, detail="repo and path are required")
    
    client, error = get_github_client()
    if error:
        return {"content": f"Error: {error}"}
    if not client:
        return {"content": "Error: GitHub client not available. Set GITHUB_TOKEN environment variable."}
    
    try:
        repo = client.get_repo(request.repo)
        branch = request.branch or "main"
        contents = repo.get_contents(request.path, ref=branch)
        
        if contents.encoding == "base64":
            import base64
            content = base64.b64decode(contents.content).decode('utf-8')
        else:
            content = contents.content
        
        return {
            "content": json.dumps({
                "file_path": request.path,
                "size": contents.size,
                "sha": contents.sha,
                "content": content[:5000]  # Limit for response
            }, indent=2)
        }
    except Exception as e:
        return {"content": f"Error: {str(e)}"}


@app.post("/mcp/tools/github_list_files")
async def github_list_files(request: ToolRequest):
    """List files in GitHub repository."""
    if not request.repo:
        raise HTTPException(status_code=400, detail="repo is required")
    
    client, error = get_github_client()
    if error:
        return {"content": f"Error: {error}"}
    if not client:
        return {"content": "Error: GitHub client not available. Set GITHUB_TOKEN environment variable."}
    
    try:
        repo = client.get_repo(request.repo)
        branch = request.branch or "main"
        path = request.path or ""
        contents = repo.get_contents(path, ref=branch)
        
        if isinstance(contents, list):
            files = [{"name": c.name, "type": c.type, "path": c.path} for c in contents]
        else:
            files = [{"name": contents.name, "type": contents.type, "path": contents.path}]
        
        return {"content": json.dumps({"files": files}, indent=2)}
    except Exception as e:
        return {"content": f"Error: {str(e)}"}


@app.post("/mcp/tools/github_create_issue")
async def github_create_issue(request: ToolRequest):
    """Create a GitHub issue."""
    if not request.repo or not request.title:
        raise HTTPException(status_code=400, detail="repo and title are required")
    
    client, error = get_github_client()
    if error:
        return {"content": f"Error: {error}"}
    if not client:
        return {"content": "Error: GitHub client not available. Set GITHUB_TOKEN environment variable."}
    
    try:
        repo = client.get_repo(request.repo)
        issue = repo.create_issue(
            title=request.title,
            body=request.body or ""
        )
        
        return {
            "content": json.dumps({
                "issue_number": issue.number,
                "title": issue.title,
                "url": issue.html_url,
                "state": issue.state
            }, indent=2)
        }
    except Exception as e:
        return {"content": f"Error: {str(e)}"}


@app.post("/mcp/tools/github_list_issues")
async def github_list_issues(request: ToolRequest):
    """List issues in GitHub repository."""
    if not request.repo:
        raise HTTPException(status_code=400, detail="repo is required")
    
    client, error = get_github_client()
    if error:
        return {"content": f"Error: {error}"}
    if not client:
        return {"content": "Error: GitHub client not available. Set GITHUB_TOKEN environment variable."}
    
    try:
        repo = client.get_repo(request.repo)
        state = request.state or "open"
        issues = repo.get_issues(state=state)
        
        issue_list = []
        for issue in issues[:10]:  # Limit to 10
            issue_list.append({
                "number": issue.number,
                "title": issue.title,
                "state": issue.state,
                "url": issue.html_url
            })
        
        return {"content": json.dumps({"issues": issue_list}, indent=2)}
    except Exception as e:
        return {"content": f"Error: {str(e)}"}


@app.post("/mcp/tools/github_search_repos")
async def github_search_repos(request: ToolRequest):
    """Search GitHub repositories."""
    if not request.query:
        raise HTTPException(status_code=400, detail="query is required")
    
    client, error = get_github_client()
    if error:
        return {"content": f"Error: {error}"}
    if not client:
        return {"content": "Error: GitHub client not available. Set GITHUB_TOKEN environment variable."}
    
    try:
        repos = client.search_repositories(request.query)
        repo_list = []
        for repo in repos[:10]:  # Limit to 10
            repo_list.append({
                "name": repo.full_name,
                "description": repo.description,
                "stars": repo.stargazers_count,
                "url": repo.html_url
            })
        
        return {"content": json.dumps({"repositories": repo_list}, indent=2)}
    except Exception as e:
        return {"content": f"Error: {str(e)}"}


@app.get("/health")
async def health():
    """Health check."""
    client, error = get_github_client()
    return {
        "status": "ok" if client else "error",
        "server": "github",
        "tools": len(TOOLS),
        "github_connected": client is not None,
        "error": error if error else None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

