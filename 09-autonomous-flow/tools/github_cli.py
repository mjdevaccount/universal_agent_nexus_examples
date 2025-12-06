"""
GitHub CLI Tools
Uses `gh` CLI for reliable, authenticated GitHub access.
"""

import subprocess
import json
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

# Managed repositories
MANAGED_REPOS = [
    "mjdevaccount/universal_agent_fabric",
    "mjdevaccount/universal_agent_architecture",
    "mjdevaccount/universal_agent_nexus",
    "mjdevaccount/universal_agent_nexus_examples",
]


def run_gh_command(args: List[str], timeout: int = 30) -> dict:
    """Run a gh CLI command and return parsed output."""
    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode != 0:
            return {"error": result.stderr.strip() or f"Command failed with code {result.returncode}"}
        
        # Try to parse as JSON
        try:
            return {"data": json.loads(result.stdout)}
        except json.JSONDecodeError:
            return {"data": result.stdout.strip()}
            
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out"}
    except FileNotFoundError:
        return {"error": "gh CLI not found. Install from https://cli.github.com"}


def gh_list_managed_repos() -> dict:
    """List all managed repositories with their status."""
    repos_info = []
    
    for repo in MANAGED_REPOS:
        result = run_gh_command([
            "repo", "view", repo, "--json",
            "name,description,pushedAt,defaultBranchRef"
        ])
        
        if "error" in result:
            repos_info.append({"repo": repo, "error": result["error"]})
        else:
            data = result["data"]
            repos_info.append({
                "repo": repo,
                "name": data.get("name"),
                "description": data.get("description"),
                "last_pushed": data.get("pushedAt"),
                "default_branch": data.get("defaultBranchRef", {}).get("name", "main")
            })
    
    return {"repos": repos_info}


def gh_get_repo_commits(repo: str, since: Optional[str] = None, limit: int = 10) -> dict:
    """
    Get recent commits for a repository.
    
    Args:
        repo: Repository in owner/name format
        since: ISO date string to get commits since (e.g., "2025-12-01")
        limit: Maximum number of commits to return
    """
    if repo not in MANAGED_REPOS:
        return {"error": f"Repository {repo} is not in managed repos list"}
    
    args = [
        "api", f"/repos/{repo}/commits",
        "--jq", f".[:{limit}] | .[] | {{sha: .sha, message: .commit.message, date: .commit.author.date, author: .commit.author.name}}"
    ]
    
    if since:
        args.extend(["--method", "GET", "-f", f"since={since}"])
    
    result = run_gh_command(args)
    
    if "error" in result:
        return result
    
    # Parse JSONL output
    commits = []
    for line in result["data"].strip().split("\n"):
        if line:
            try:
                commits.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    
    return {"repo": repo, "commits": commits}


def get_default_branch(repo: str) -> str:
    """Get the default branch for a repo."""
    result = run_gh_command(["api", f"/repos/{repo}", "--jq", ".default_branch"])
    if "data" in result and isinstance(result["data"], str):
        return result["data"].strip()
    return "main"  # fallback


# File types relevant to our development
SUPPORTED_EXTENSIONS = [
    ".py",      # Python code
    ".yaml",    # Agent manifests, configs
    ".yml",     # YAML configs
    ".md",      # Documentation, READMEs
    ".json",    # Schemas, configs
    ".toml",    # pyproject.toml, configs
    ".sh",      # Shell scripts
    ".ps1",     # PowerShell scripts
    ".dockerfile", # Container configs
]


def gh_list_code_files(repo: str, path: str = "") -> dict:
    """
    List all relevant code/config files in a repository.
    
    Includes: .py, .yaml, .yml, .md, .json, .toml, .sh, .ps1
    
    Args:
        repo: Repository in owner/name format
        path: Path within repo (empty for root)
    """
    if repo not in MANAGED_REPOS:
        return {"error": f"Repository {repo} is not in managed repos list"}
    
    # Get the correct default branch
    branch = get_default_branch(repo)
    
    # Build jq filter for all supported extensions
    ext_filters = " or ".join([f'endswith("{ext}")' for ext in SUPPORTED_EXTENSIONS])
    # Also include Dockerfile (no extension)
    jq_filter = f'.tree[] | select((.path | ({ext_filters})) or (.path | endswith("Dockerfile"))) | {{path: .path, sha: .sha, size: .size}}'
    
    # Get tree recursively
    args = [
        "api", f"/repos/{repo}/git/trees/{branch}?recursive=1",
        "--jq", jq_filter
    ]
    
    result = run_gh_command(args)
    
    if "error" in result:
        return result
    
    # Parse JSONL output
    files = []
    for line in result["data"].strip().split("\n"):
        if line:
            try:
                file_info = json.loads(line)
                # Filter by path prefix if specified
                if not path or file_info["path"].startswith(path):
                    files.append(file_info)
            except json.JSONDecodeError:
                pass
    
    return {"repo": repo, "path": path, "code_files": files, "count": len(files)}


def gh_get_file_with_metadata(repo: str, path: str) -> dict:
    """
    Get file content along with its metadata (last commit, sha).
    
    Args:
        repo: Repository in owner/name format
        path: File path within repo
    """
    if repo not in MANAGED_REPOS:
        return {"error": f"Repository {repo} is not in managed repos list"}
    
    # Get the correct default branch
    branch = get_default_branch(repo)
    
    # Get file content
    content_result = run_gh_command([
        "api", f"/repos/{repo}/contents/{path}?ref={branch}",
        "--jq", '{sha: .sha, size: .size, content: .content, encoding: .encoding}'
    ])
    
    if "error" in content_result:
        return content_result
    
    # Get last commit for this file
    commit_result = run_gh_command([
        "api", f"/repos/{repo}/commits?path={path}&per_page=1",
        "--jq", '.[0] | {commit_sha: .sha, commit_date: .commit.author.date, commit_message: .commit.message}'
    ])
    
    try:
        content_data = json.loads(content_result["data"]) if isinstance(content_result["data"], str) else content_result["data"]
        commit_data = json.loads(commit_result["data"]) if isinstance(commit_result["data"], str) else commit_result.get("data", {})
        
        # Decode content
        import base64
        decoded_content = ""
        if content_data.get("encoding") == "base64" and content_data.get("content"):
            try:
                decoded_content = base64.b64decode(content_data["content"]).decode("utf-8")
            except:
                decoded_content = "[Binary or encoding error]"
        
        return {
            "repo": repo,
            "path": path,
            "sha": content_data.get("sha"),
            "size": content_data.get("size"),
            "content": decoded_content,
            "last_commit": commit_data if commit_data else None,
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        return {"error": f"Failed to parse response: {str(e)}"}


def gh_get_repo_changed_files(repo: str, since: str) -> dict:
    """
    Get list of files that changed since a given date.
    
    Args:
        repo: Repository in owner/name format
        since: ISO date string (e.g., "2025-12-01T00:00:00Z")
    """
    if repo not in MANAGED_REPOS:
        return {"error": f"Repository {repo} is not in managed repos list"}
    
    # Get commits since date
    commits_result = gh_get_repo_commits(repo, since=since, limit=50)
    
    if "error" in commits_result:
        return commits_result
    
    # For each commit, get changed files
    changed_files = set()
    
    for commit in commits_result.get("commits", []):
        sha = commit.get("sha")
        if sha:
            files_result = run_gh_command([
                "api", f"/repos/{repo}/commits/{sha}",
                "--jq", '.files[].filename'
            ])
            
            if "data" in files_result:
                for filename in files_result["data"].strip().split("\n"):
                    if filename.endswith(".py"):
                        changed_files.add(filename)
    
    return {
        "repo": repo,
        "since": since,
        "changed_python_files": sorted(list(changed_files)),
        "count": len(changed_files)
    }


# Tool definitions for MCP server
TOOLS = [
    {
        "name": "gh_list_managed_repos",
        "description": "List all managed repositories (universal_agent_*) with their current status",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "gh_get_repo_commits",
        "description": "Get recent commits for a managed repository",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository in owner/name format"},
                "since": {"type": "string", "description": "ISO date to get commits since"},
                "limit": {"type": "integer", "description": "Max commits to return", "default": 10}
            },
            "required": ["repo"]
        }
    },
    {
        "name": "gh_list_code_files",
        "description": "List all code/config files in a repo (.py, .yaml, .md, .json, .toml, .sh, etc.)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository in owner/name format"},
                "path": {"type": "string", "description": "Path prefix to filter", "default": ""}
            },
            "required": ["repo"]
        }
    },
    {
        "name": "gh_get_file_with_metadata",
        "description": "Get file content with metadata (sha, last commit date)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository in owner/name format"},
                "path": {"type": "string", "description": "File path in repo"}
            },
            "required": ["repo", "path"]
        }
    },
    {
        "name": "gh_get_repo_changed_files",
        "description": "Get list of code files that changed since a date",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository in owner/name format"},
                "since": {"type": "string", "description": "ISO date string"}
            },
            "required": ["repo", "since"]
        }
    }
]


if __name__ == "__main__":
    # Test the tools
    print("Testing GitHub CLI tools...")
    
    print("\n1. List managed repos:")
    result = gh_list_managed_repos()
    print(json.dumps(result, indent=2, default=str)[:500])
    
    print("\n2. List Python files in nexus:")
    result = gh_list_python_files("mjdevaccount/universal_agent_nexus")
    print(json.dumps(result, indent=2, default=str)[:500])

