"""
Chunk Manager Tools
Manages code chunks in Qdrant with sync state tracking.
"""

import json
import hashlib
import ast
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import uuid

# Sync state file
SYNC_STATE_FILE = Path(__file__).parent.parent / "sync_state.json"

# Collection name
COLLECTION_NAME = "universal_agent_code"


def load_sync_state() -> dict:
    """Load sync state from file."""
    if SYNC_STATE_FILE.exists():
        with open(SYNC_STATE_FILE, 'r') as f:
            return json.load(f)
    return {"repos": {}, "last_full_sync": None}


def save_sync_state(state: dict):
    """Save sync state to file."""
    with open(SYNC_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, default=str)


def get_content_hash(content: str) -> str:
    """Generate hash of content for change detection."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def get_file_type(file_path: str) -> str:
    """Determine file type from path."""
    path = Path(file_path)
    ext = path.suffix.lower()
    name = path.name.lower()
    
    if ext == ".py":
        return "python"
    elif ext in [".yaml", ".yml"]:
        return "yaml"
    elif ext == ".md":
        return "markdown"
    elif ext == ".json":
        return "json"
    elif ext == ".toml":
        return "toml"
    elif ext in [".sh", ".bash"]:
        return "shell"
    elif ext == ".ps1":
        return "powershell"
    elif name == "dockerfile" or ext == ".dockerfile":
        return "dockerfile"
    else:
        return "text"


def chunk_content(content: str, file_path: str) -> List[Dict]:
    """
    Chunk content based on file type.
    Uses appropriate strategy for each type.
    """
    file_type = get_file_type(file_path)
    
    if file_type == "python":
        return chunk_python_content(content, file_path)
    elif file_type == "yaml":
        return chunk_yaml_content(content, file_path)
    elif file_type == "markdown":
        return chunk_markdown_content(content, file_path)
    elif file_type == "json":
        return chunk_json_content(content, file_path)
    else:
        # Generic chunking for other file types
        return chunk_generic_content(content, file_path, file_type)


def chunk_python_content(content: str, file_path: str) -> List[Dict]:
    """Chunk Python content using AST parsing."""
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return chunk_generic_content(content, file_path, "python")
    
    chunks = []
    lines = content.split('\n')
    
    # Extract imports
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            start = node.lineno - 1
            end = getattr(node, 'end_lineno', node.lineno)
            imports.append('\n'.join(lines[start:end]))
    
    import_block = '\n'.join(imports) if imports else ""
    
    # Extract classes
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            start = node.lineno - 1
            end = getattr(node, 'end_lineno', node.lineno)
            class_code = '\n'.join(lines[start:end])
            
            if not chunks and import_block:
                class_code = import_block + '\n\n' + class_code
            
            chunks.append({
                "type": "class",
                "name": node.name,
                "content": class_code,
                "line_start": node.lineno,
                "line_end": end,
                "docstring": ast.get_docstring(node) or ""
            })
    
    # Extract standalone functions
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            start = node.lineno - 1
            end = getattr(node, 'end_lineno', node.lineno)
            func_code = '\n'.join(lines[start:end])
            
            if not chunks and import_block:
                func_code = import_block + '\n\n' + func_code
            
            chunks.append({
                "type": "function",
                "name": node.name,
                "content": func_code,
                "line_start": node.lineno,
                "line_end": end,
                "docstring": ast.get_docstring(node) or ""
            })
    
    # If no classes/functions, chunk as module
    if not chunks:
        chunks.append({
            "type": "module",
            "name": Path(file_path).stem,
            "content": content,
            "line_start": 1,
            "line_end": len(lines),
            "docstring": ast.get_docstring(tree) or ""
        })
    
    return chunks


def chunk_yaml_content(content: str, file_path: str) -> List[Dict]:
    """Chunk YAML content by top-level keys."""
    chunks = []
    lines = content.split('\n')
    
    # Find top-level keys (lines starting with non-whitespace, ending with :)
    current_chunk_start = 0
    current_key = None
    
    for i, line in enumerate(lines):
        # Skip empty lines and comments at start
        if not line.strip() or line.strip().startswith('#'):
            continue
        
        # Check if this is a top-level key
        if line and not line[0].isspace() and ':' in line:
            # Save previous chunk
            if current_key is not None:
                chunk_content = '\n'.join(lines[current_chunk_start:i])
                if chunk_content.strip():
                    chunks.append({
                        "type": "yaml_section",
                        "name": current_key,
                        "content": chunk_content,
                        "line_start": current_chunk_start + 1,
                        "line_end": i,
                        "docstring": ""
                    })
            
            current_key = line.split(':')[0].strip()
            current_chunk_start = i
    
    # Don't forget the last chunk
    if current_key is not None:
        chunk_content = '\n'.join(lines[current_chunk_start:])
        if chunk_content.strip():
            chunks.append({
                "type": "yaml_section",
                "name": current_key,
                "content": chunk_content,
                "line_start": current_chunk_start + 1,
                "line_end": len(lines),
                "docstring": ""
            })
    
    # If no sections found, return whole file
    if not chunks:
        return chunk_generic_content(content, file_path, "yaml")
    
    return chunks


def chunk_markdown_content(content: str, file_path: str) -> List[Dict]:
    """Chunk Markdown content by headers."""
    chunks = []
    lines = content.split('\n')
    
    current_header = Path(file_path).stem
    current_start = 0
    current_level = 0
    
    for i, line in enumerate(lines):
        # Check for markdown headers
        if line.startswith('#'):
            # Count header level
            level = len(line) - len(line.lstrip('#'))
            header_text = line.lstrip('#').strip()
            
            # Save previous chunk (only for h1, h2, h3)
            if level <= 3 and current_start < i:
                chunk_content = '\n'.join(lines[current_start:i])
                if chunk_content.strip():
                    chunks.append({
                        "type": f"markdown_h{current_level}" if current_level else "markdown_intro",
                        "name": current_header,
                        "content": chunk_content,
                        "line_start": current_start + 1,
                        "line_end": i,
                        "docstring": ""
                    })
            
            if level <= 3:
                current_header = header_text
                current_start = i
                current_level = level
    
    # Don't forget the last chunk
    chunk_content = '\n'.join(lines[current_start:])
    if chunk_content.strip():
        chunks.append({
            "type": f"markdown_h{current_level}" if current_level else "markdown_content",
            "name": current_header,
            "content": chunk_content,
            "line_start": current_start + 1,
            "line_end": len(lines),
            "docstring": ""
        })
    
    return chunks if chunks else chunk_generic_content(content, file_path, "markdown")


def chunk_json_content(content: str, file_path: str) -> List[Dict]:
    """Chunk JSON content - usually keep as single chunk but extract metadata."""
    try:
        data = json.loads(content)
        
        # If it's a dict with top-level keys, describe the structure
        if isinstance(data, dict):
            top_keys = list(data.keys())[:10]
            description = f"JSON with keys: {', '.join(top_keys)}"
        else:
            description = f"JSON array with {len(data)} items" if isinstance(data, list) else "JSON value"
        
        return [{
            "type": "json_document",
            "name": Path(file_path).stem,
            "content": content,
            "line_start": 1,
            "line_end": len(content.split('\n')),
            "docstring": description
        }]
    except json.JSONDecodeError:
        return chunk_generic_content(content, file_path, "json")


def chunk_generic_content(content: str, file_path: str, file_type: str) -> List[Dict]:
    """Generic chunking for any file type - chunk by size with overlap."""
    lines = content.split('\n')
    chunks = []
    
    # For small files, keep as single chunk
    if len(lines) <= 100:
        return [{
            "type": file_type,
            "name": Path(file_path).name,
            "content": content,
            "line_start": 1,
            "line_end": len(lines),
            "docstring": ""
        }]
    
    # For larger files, chunk with overlap
    chunk_size = 80
    overlap = 10
    
    i = 0
    chunk_num = 1
    while i < len(lines):
        end = min(i + chunk_size, len(lines))
        chunk_content = '\n'.join(lines[i:end])
        
        chunks.append({
            "type": file_type,
            "name": f"{Path(file_path).stem}_part{chunk_num}",
            "content": chunk_content,
            "line_start": i + 1,
            "line_end": end,
            "docstring": ""
        })
        
        i += chunk_size - overlap
        chunk_num += 1
    
    return chunks


def get_sync_status(repo: Optional[str] = None) -> dict:
    """
    Get sync status for all or one repository.
    
    Compares stored state with what we expect.
    """
    state = load_sync_state()
    
    if repo:
        repo_state = state["repos"].get(repo, {})
        return {
            "repo": repo,
            "last_sync": repo_state.get("last_sync"),
            "last_github_sha": repo_state.get("last_github_sha"),
            "files_synced": repo_state.get("files_synced", 0),
            "total_chunks": repo_state.get("total_chunks", 0),
            "needs_sync": repo_state.get("needs_sync", True)
        }
    
    # Return all repos
    statuses = []
    for r, data in state["repos"].items():
        statuses.append({
            "repo": r,
            "last_sync": data.get("last_sync"),
            "files_synced": data.get("files_synced", 0),
            "total_chunks": data.get("total_chunks", 0)
        })
    
    return {
        "repos": statuses,
        "last_full_sync": state.get("last_full_sync")
    }


def update_sync_state(repo: str, file_path: str, github_sha: str, chunks_count: int) -> dict:
    """
    Update sync state after chunking a file.
    """
    state = load_sync_state()
    
    if repo not in state["repos"]:
        state["repos"][repo] = {
            "files": {},
            "files_synced": 0,
            "total_chunks": 0
        }
    
    repo_state = state["repos"][repo]
    
    # Update file info
    repo_state["files"][file_path] = {
        "github_sha": github_sha,
        "chunks": chunks_count,
        "synced_at": datetime.utcnow().isoformat() + "Z"
    }
    
    # Recalculate totals
    repo_state["files_synced"] = len(repo_state["files"])
    repo_state["total_chunks"] = sum(f["chunks"] for f in repo_state["files"].values())
    repo_state["last_sync"] = datetime.utcnow().isoformat() + "Z"
    
    save_sync_state(state)
    
    return {
        "repo": repo,
        "file": file_path,
        "status": "synced",
        "chunks_stored": chunks_count
    }


def check_file_needs_sync(repo: str, file_path: str, github_sha: str) -> dict:
    """
    Check if a file needs to be re-synced based on SHA.
    """
    state = load_sync_state()
    
    repo_state = state["repos"].get(repo, {})
    file_state = repo_state.get("files", {}).get(file_path, {})
    
    stored_sha = file_state.get("github_sha")
    
    needs_sync = stored_sha != github_sha
    
    return {
        "repo": repo,
        "file": file_path,
        "needs_sync": needs_sync,
        "stored_sha": stored_sha,
        "github_sha": github_sha,
        "last_synced": file_state.get("synced_at")
    }


def store_chunks(repo: str, file_path: str, content: str, github_sha: str) -> dict:
    """
    Chunk content and prepare for storage.
    
    In production, this would generate embeddings and store in Qdrant.
    For now, we update sync state and return chunk info.
    """
    chunks = chunk_python_content(content, file_path)
    
    # Generate chunk records (would be stored in Qdrant)
    chunk_records = []
    for i, chunk in enumerate(chunks):
        chunk_records.append({
            "id": str(uuid.uuid4()),
            "repo": repo,
            "file_path": file_path,
            "chunk_type": chunk["type"],
            "chunk_name": chunk["name"],
            "line_start": chunk["line_start"],
            "line_end": chunk["line_end"],
            "content_hash": get_content_hash(chunk["content"]),
            "github_sha": github_sha,
            "docstring": chunk.get("docstring", ""),
            "content_preview": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"]
        })
    
    # Update sync state
    update_sync_state(repo, file_path, github_sha, len(chunks))
    
    return {
        "repo": repo,
        "file_path": file_path,
        "chunks_created": len(chunks),
        "chunks": chunk_records,
        "status": "stored"
    }


def delete_file_chunks(repo: str, file_path: str) -> dict:
    """
    Delete chunks for a file (when file is deleted/renamed).
    """
    state = load_sync_state()
    
    if repo in state["repos"] and file_path in state["repos"][repo].get("files", {}):
        del state["repos"][repo]["files"][file_path]
        
        # Recalculate totals
        repo_state = state["repos"][repo]
        repo_state["files_synced"] = len(repo_state["files"])
        repo_state["total_chunks"] = sum(f["chunks"] for f in repo_state["files"].values())
        
        save_sync_state(state)
        
        return {
            "repo": repo,
            "file_path": file_path,
            "status": "deleted"
        }
    
    return {
        "repo": repo,
        "file_path": file_path,
        "status": "not_found"
    }


def search_code(query: str, repo: Optional[str] = None) -> dict:
    """
    Search code by keyword matching (simple but effective).
    Returns files that likely contain relevant content.
    """
    state = load_sync_state()
    query_lower = query.lower()
    query_terms = query_lower.split()
    
    results = []
    repos_to_search = [repo] if repo else list(state["repos"].keys())
    
    for r in repos_to_search:
        repo_state = state["repos"].get(r, {})
        for file_path, file_info in repo_state.get("files", {}).items():
            # Simple keyword matching on file path
            path_lower = file_path.lower()
            relevance = sum(1 for term in query_terms if term in path_lower)
            
            if relevance > 0 or any(term in path_lower for term in ['api', 'main', 'core', 'base']):
                results.append({
                    "repo": r,
                    "file_path": file_path,
                    "chunks": file_info.get("chunks", 0),
                    "relevance": relevance
                })
    
    # Sort by relevance
    results.sort(key=lambda x: x["relevance"], reverse=True)
    
    return {
        "query": query,
        "results": results[:15],
        "total_results": len(results)
    }


def get_repo_overview(repo: str) -> dict:
    """
    Get a comprehensive overview of a repository's structure.
    Returns organized view of all files by type and purpose.
    """
    state = load_sync_state()
    
    if repo not in state.get("repos", {}):
        return {"error": f"Repository {repo} not synced"}
    
    repo_state = state["repos"][repo]
    files = repo_state.get("files", {})
    
    # Organize by directory and type
    structure = {
        "core_modules": [],      # Main Python packages
        "adapters": [],          # Integration adapters
        "tests": [],             # Test files
        "configs": [],           # YAML/JSON/TOML configs
        "docs": [],              # Markdown documentation
        "scripts": [],           # Shell/PowerShell scripts
        "workflows": [],         # CI/CD workflows
        "other": []
    }
    
    for file_path in files:
        entry = {"path": file_path, "chunks": files[file_path]["chunks"]}
        path_lower = file_path.lower()
        
        if ".github/workflows" in path_lower:
            structure["workflows"].append(entry)
        elif path_lower.endswith(".md"):
            structure["docs"].append(entry)
        elif path_lower.endswith((".yaml", ".yml", ".json", ".toml")):
            structure["configs"].append(entry)
        elif path_lower.endswith((".sh", ".ps1")):
            structure["scripts"].append(entry)
        elif "/test" in path_lower or path_lower.startswith("test"):
            structure["tests"].append(entry)
        elif "/adapters/" in path_lower:
            structure["adapters"].append(entry)
        elif path_lower.endswith(".py"):
            structure["core_modules"].append(entry)
        else:
            structure["other"].append(entry)
    
    # Summary stats
    summary = {
        "repo": repo,
        "total_files": len(files),
        "total_chunks": sum(f["chunks"] for f in files.values()),
        "structure": {k: len(v) for k, v in structure.items() if v},
        "key_files": structure
    }
    
    return summary


def get_file_chunks(repo: str, file_path: str) -> dict:
    """
    Get the actual content chunks for a specific file.
    This re-fetches and chunks the file to return content.
    """
    from github_cli import gh_get_file_with_metadata, MANAGED_REPOS
    
    if repo not in MANAGED_REPOS:
        return {"error": f"Repository {repo} not managed"}
    
    # Fetch file content
    result = gh_get_file_with_metadata(repo, file_path)
    if "error" in result:
        return result
    
    content = result.get("content", "")
    if not content:
        return {"error": "No content"}
    
    # Chunk it
    chunks = chunk_content(content, file_path)
    
    return {
        "repo": repo,
        "file_path": file_path,
        "file_type": get_file_type(file_path),
        "chunks": [
            {
                "type": c["type"],
                "name": c["name"],
                "lines": f"{c['line_start']}-{c['line_end']}",
                "content": c["content"][:2000],  # Limit content size
                "docstring": c.get("docstring", "")[:500]
            }
            for c in chunks
        ]
    }


def get_api_surface(repo: str) -> dict:
    """
    Extract the API surface of a repository from sync state.
    Returns overview of key files and their purposes.
    """
    state = load_sync_state()
    if repo not in state.get("repos", {}):
        return {"error": f"Repository {repo} not synced. Run sync first."}
    
    files = state["repos"][repo].get("files", {})
    
    # Categorize files by their likely purpose
    api_surface = {
        "packages": [],      # __init__.py files
        "core_modules": [],  # main.py, core.py, base.py
        "adapters": [],      # adapter files
        "compilers": [],     # compiler files
        "handlers": [],      # handler files  
        "utilities": [],     # utils, helpers
        "configs": [],       # YAML/JSON configs
        "total_files": len(files),
        "total_chunks": sum(f["chunks"] for f in files.values())
    }
    
    for file_path in files:
        path_lower = file_path.lower()
        entry = {"file": file_path, "chunks": files[file_path]["chunks"]}
        
        if "__init__.py" in path_lower:
            # Extract package name from path
            parts = file_path.replace("__init__.py", "").strip("/").split("/")
            entry["package"] = parts[-1] if parts and parts[-1] else "root"
            api_surface["packages"].append(entry)
        elif any(x in path_lower for x in ["main.py", "core.py", "base.py", "api.py"]):
            api_surface["core_modules"].append(entry)
        elif "adapter" in path_lower:
            api_surface["adapters"].append(entry)
        elif "compiler" in path_lower:
            api_surface["compilers"].append(entry)
        elif "handler" in path_lower:
            api_surface["handlers"].append(entry)
        elif any(x in path_lower for x in ["util", "helper", "common"]):
            api_surface["utilities"].append(entry)
        elif path_lower.endswith((".yaml", ".yml", ".json", ".toml")):
            api_surface["configs"].append(entry)
    
    # Clean up empty categories
    api_surface = {k: v for k, v in api_surface.items() if v}
    
    return {
        "repo": repo,
        "api_surface": api_surface
    }


def analyze_full_stack() -> dict:
    """
    Analyze the entire Universal Agent stack in one call.
    Returns comprehensive summary of all repositories.
    """
    from github_cli import MANAGED_REPOS
    
    state = load_sync_state()
    
    stack_analysis = {
        "summary": "Universal Agent Stack Analysis",
        "repositories": {}
    }
    
    for repo in MANAGED_REPOS:
        if repo not in state.get("repos", {}):
            stack_analysis["repositories"][repo] = {"status": "not synced"}
            continue
        
        files = state["repos"][repo].get("files", {})
        
        # Categorize files
        packages = []
        core_files = []
        adapters = []
        configs = []
        docs = []
        
        for file_path in files:
            path_lower = file_path.lower()
            chunks = files[file_path]["chunks"]
            
            if "__init__.py" in path_lower:
                pkg = file_path.replace("__init__.py", "").strip("/").split("/")
                packages.append(pkg[-1] if pkg and pkg[-1] else "root")
            elif any(x in path_lower for x in ["main.py", "core.py", "base.py", "compiler", "builder"]):
                core_files.append(file_path)
            elif "adapter" in path_lower:
                adapters.append(file_path)
            elif path_lower.endswith((".yaml", ".yml")):
                configs.append(file_path)
            elif path_lower.endswith(".md"):
                docs.append(file_path)
        
        # Determine repo purpose from structure
        purpose = "Unknown"
        if "compiler" in str(core_files).lower():
            purpose = "Compiler/Translator - Converts agent definitions to runtime code"
        elif "builder" in str(core_files).lower() or "fabric" in repo:
            purpose = "Composition Layer - Builds and assembles agent definitions"
        elif "architecture" in repo:
            purpose = "Reference Architecture - Design patterns and templates"
        elif "examples" in repo:
            purpose = "Examples - Demonstrations and tutorials"
        
        stack_analysis["repositories"][repo] = {
            "purpose": purpose,
            "packages": list(set(packages))[:10],
            "core_modules": core_files[:5],
            "adapters": adapters[:5],
            "configs": configs[:5],
            "docs": docs[:5],
            "total_files": len(files),
            "total_chunks": sum(f["chunks"] for f in files.values())
        }
    
    # Add stack-level summary
    total_files = sum(r.get("total_files", 0) for r in stack_analysis["repositories"].values() if isinstance(r, dict))
    total_chunks = sum(r.get("total_chunks", 0) for r in stack_analysis["repositories"].values() if isinstance(r, dict))
    
    stack_analysis["totals"] = {
        "repositories": len(MANAGED_REPOS),
        "total_files": total_files,
        "total_chunks": total_chunks
    }
    
    return stack_analysis


def get_storage_stats() -> dict:
    """Get storage statistics."""
    state = load_sync_state()
    
    total_files = 0
    total_chunks = 0
    
    for repo_state in state["repos"].values():
        total_files += repo_state.get("files_synced", 0)
        total_chunks += repo_state.get("total_chunks", 0)
    
    return {
        "repos_tracked": len(state["repos"]),
        "total_files": total_files,
        "total_chunks": total_chunks,
        "last_full_sync": state.get("last_full_sync"),
        "state_file": str(SYNC_STATE_FILE)
    }


def bulk_sync_repo(repo: str) -> dict:
    """
    Bulk sync an entire repository in one optimized call.
    
    This does everything:
    1. Lists all code files (.py, .yaml, .md, .json, .toml, .sh, etc.)
    2. Checks which ones need syncing (by SHA)
    3. Fetches and chunks changed files
    4. Updates sync state
    
    Much faster than agent doing it file-by-file.
    """
    from github_cli import gh_list_code_files, gh_get_file_with_metadata, MANAGED_REPOS
    
    if repo not in MANAGED_REPOS:
        return {"error": f"Repository {repo} is not managed"}
    
    results = {
        "repo": repo,
        "files_checked": 0,
        "files_synced": 0,
        "files_unchanged": 0,
        "chunks_created": 0,
        "by_type": {},
        "errors": []
    }
    
    # Get all code files (not just Python)
    files_result = gh_list_code_files(repo)
    if "error" in files_result:
        return {"error": files_result["error"]}
    
    # Handle both old key name and new
    code_files = files_result.get("code_files") or files_result.get("python_files", [])
    results["files_checked"] = len(code_files)
    
    state = load_sync_state()
    
    for file_info in code_files:
        file_path = file_info["path"]
        github_sha = file_info["sha"]
        
        # Check if needs sync
        stored_sha = state.get("repos", {}).get(repo, {}).get("files", {}).get(file_path, {}).get("github_sha")
        
        if stored_sha == github_sha:
            results["files_unchanged"] += 1
            continue
        
        # Needs sync - fetch content
        file_result = gh_get_file_with_metadata(repo, file_path)
        if "error" in file_result:
            results["errors"].append(f"{file_path}: {file_result['error']}")
            continue
        
        content = file_result.get("content", "")
        if not content:
            results["errors"].append(f"{file_path}: No content")
            continue
        
        # Chunk using appropriate strategy for file type
        chunks = chunk_content(content, file_path)
        
        # Track by file type
        file_type = get_file_type(file_path)
        if file_type not in results["by_type"]:
            results["by_type"][file_type] = {"files": 0, "chunks": 0}
        results["by_type"][file_type]["files"] += 1
        results["by_type"][file_type]["chunks"] += len(chunks)
        
        # Update state
        update_sync_state(repo, file_path, github_sha, len(chunks))
        
        results["files_synced"] += 1
        results["chunks_created"] += len(chunks)
    
    # Mark full sync time
    state = load_sync_state()
    state["last_full_sync"] = datetime.utcnow().isoformat() + "Z"
    save_sync_state(state)
    
    results["status"] = "complete"
    return results


def bulk_sync_all() -> dict:
    """
    Sync ALL managed repositories in one call.
    
    Returns summary of what was synced.
    """
    from github_cli import MANAGED_REPOS
    
    results = {
        "repos_synced": [],
        "total_files_synced": 0,
        "total_chunks_created": 0,
        "errors": []
    }
    
    for repo in MANAGED_REPOS:
        print(f"  Syncing {repo}...")
        repo_result = bulk_sync_repo(repo)
        
        if "error" in repo_result:
            results["errors"].append(f"{repo}: {repo_result['error']}")
        else:
            results["repos_synced"].append({
                "repo": repo,
                "files_synced": repo_result.get("files_synced", 0),
                "files_unchanged": repo_result.get("files_unchanged", 0),
                "chunks_created": repo_result.get("chunks_created", 0)
            })
            results["total_files_synced"] += repo_result.get("files_synced", 0)
            results["total_chunks_created"] += repo_result.get("chunks_created", 0)
    
    results["status"] = "complete"
    return results


# Tool definitions for MCP server
TOOLS = [
    {
        "name": "get_sync_status",
        "description": "Get sync status for all or one repository",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository to check (optional)"}
            }
        }
    },
    {
        "name": "bulk_sync_repo",
        "description": "FAST: Sync an entire repository in one call",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository to sync"}
            },
            "required": ["repo"]
        }
    },
    {
        "name": "bulk_sync_all",
        "description": "FAST: Sync ALL managed repositories in one call",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_repo_overview",
        "description": "Get comprehensive overview of a repo's structure (files organized by type/purpose)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository to analyze"}
            },
            "required": ["repo"]
        }
    },
    {
        "name": "get_api_surface",
        "description": "Extract API surface (classes, functions, exports) from a repository",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository to analyze"}
            },
            "required": ["repo"]
        }
    },
    {
        "name": "get_file_chunks",
        "description": "Get actual content chunks for a specific file",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository"},
                "file_path": {"type": "string", "description": "Path to file"}
            },
            "required": ["repo", "file_path"]
        }
    },
    {
        "name": "search_code",
        "description": "Search code by keywords, returns relevant files",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search terms"},
                "repo": {"type": "string", "description": "Filter by repo (optional)"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "analyze_full_stack",
        "description": "Analyze entire Universal Agent stack in ONE call. Returns all repos, their purposes, key files, and structure.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_storage_stats",
        "description": "Get storage statistics",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]


if __name__ == "__main__":
    # Test
    print("Testing chunk manager...")
    
    print("\n1. Get sync status:")
    print(json.dumps(get_sync_status(), indent=2))
    
    print("\n2. Get storage stats:")
    print(json.dumps(get_storage_stats(), indent=2))

