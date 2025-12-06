"""
AutonomousFlow MCP Server
Unified server for code knowledge management.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json

from github_cli import (
    gh_list_managed_repos,
    gh_get_repo_commits,
    gh_list_code_files,
    gh_get_file_with_metadata,
    gh_get_repo_changed_files,
    TOOLS as GITHUB_TOOLS
)

from chunk_manager import (
    get_sync_status,
    bulk_sync_repo,
    bulk_sync_all,
    search_code,
    get_storage_stats,
    get_repo_overview,
    get_api_surface,
    get_file_chunks,
    analyze_full_stack,
    TOOLS as CHUNK_TOOLS
)

from document_writer import (
    create_document_plan,
    write_section,
    compile_document,
    get_plan_status,
    TOOLS as DOC_TOOLS
)

app = FastAPI(title="AutonomousFlow MCP Server")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# Combine all tools
ALL_TOOLS = GITHUB_TOOLS + CHUNK_TOOLS + DOC_TOOLS


class ToolRequest(BaseModel):
    # GitHub tools
    repo: Optional[str] = None
    path: Optional[str] = None
    since: Optional[str] = None
    limit: Optional[int] = 10
    
    # Chunk tools
    file_path: Optional[str] = None
    content: Optional[str] = None
    github_sha: Optional[str] = None
    query: Optional[str] = None
    
    # Document writer tools
    title: Optional[str] = None
    sections: Optional[list] = None
    section_id: Optional[str] = None
    filename: Optional[str] = None


@app.get("/mcp/tools")
async def list_tools():
    """MCP introspection endpoint."""
    return {"tools": ALL_TOOLS}


# ===== GitHub CLI Tools =====

@app.post("/mcp/tools/gh_list_managed_repos")
async def api_gh_list_managed_repos(request: ToolRequest = None):
    """List all managed repositories."""
    result = gh_list_managed_repos()
    return {"content": json.dumps(result, indent=2, default=str)}


@app.post("/mcp/tools/gh_get_repo_commits")
async def api_gh_get_repo_commits(request: ToolRequest):
    """Get recent commits for a repository."""
    if not request.repo:
        raise HTTPException(status_code=400, detail="repo is required")
    result = gh_get_repo_commits(request.repo, request.since, request.limit or 10)
    return {"content": json.dumps(result, indent=2, default=str)}


@app.post("/mcp/tools/gh_list_code_files")
async def api_gh_list_code_files(request: ToolRequest):
    """List all code/config files in a repository."""
    if not request.repo:
        raise HTTPException(status_code=400, detail="repo is required")
    result = gh_list_code_files(request.repo, request.path or "")
    return {"content": json.dumps(result, indent=2, default=str)}


@app.post("/mcp/tools/gh_get_file_with_metadata")
async def api_gh_get_file_with_metadata(request: ToolRequest):
    """Get file content with metadata."""
    if not request.repo or not request.path:
        raise HTTPException(status_code=400, detail="repo and path are required")
    result = gh_get_file_with_metadata(request.repo, request.path)
    return {"content": json.dumps(result, indent=2, default=str)}


@app.post("/mcp/tools/gh_get_repo_changed_files")
async def api_gh_get_repo_changed_files(request: ToolRequest):
    """Get files changed since a date."""
    if not request.repo or not request.since:
        raise HTTPException(status_code=400, detail="repo and since are required")
    result = gh_get_repo_changed_files(request.repo, request.since)
    return {"content": json.dumps(result, indent=2, default=str)}


# ===== Chunk Management Tools =====

@app.post("/mcp/tools/get_sync_status")
async def api_get_sync_status(request: ToolRequest = None):
    """Get sync status."""
    result = get_sync_status(request.repo if request else None)
    return {"content": json.dumps(result, indent=2, default=str)}


@app.post("/mcp/tools/bulk_sync_repo")
async def api_bulk_sync_repo(request: ToolRequest):
    """Bulk sync a single repository."""
    if not request.repo:
        raise HTTPException(status_code=400, detail="repo is required")
    result = bulk_sync_repo(request.repo)
    return {"content": json.dumps(result, indent=2, default=str)}


@app.post("/mcp/tools/bulk_sync_all")
async def api_bulk_sync_all(request: ToolRequest = None):
    """Bulk sync ALL managed repositories."""
    result = bulk_sync_all()
    return {"content": json.dumps(result, indent=2, default=str)}


@app.post("/mcp/tools/search_code")
async def api_search_code(request: ToolRequest):
    """Search code chunks."""
    if not request.query:
        raise HTTPException(status_code=400, detail="query is required")
    result = search_code(request.query, request.repo)
    return {"content": json.dumps(result, indent=2, default=str)}


@app.post("/mcp/tools/get_storage_stats")
async def api_get_storage_stats(request: ToolRequest = None):
    """Get storage statistics."""
    result = get_storage_stats()
    return {"content": json.dumps(result, indent=2, default=str)}


@app.post("/mcp/tools/get_repo_overview")
async def api_get_repo_overview(request: ToolRequest):
    """Get comprehensive overview of a repository."""
    if not request.repo:
        raise HTTPException(status_code=400, detail="repo is required")
    result = get_repo_overview(request.repo)
    return {"content": json.dumps(result, indent=2, default=str)}


@app.post("/mcp/tools/get_api_surface")
async def api_get_api_surface(request: ToolRequest):
    """Extract API surface from a repository."""
    if not request.repo:
        raise HTTPException(status_code=400, detail="repo is required")
    result = get_api_surface(request.repo)
    return {"content": json.dumps(result, indent=2, default=str)}


@app.post("/mcp/tools/get_file_chunks")
async def api_get_file_chunks(request: ToolRequest):
    """Get content chunks for a file."""
    if not request.repo or not request.file_path:
        raise HTTPException(status_code=400, detail="repo and file_path are required")
    result = get_file_chunks(request.repo, request.file_path)
    return {"content": json.dumps(result, indent=2, default=str)}


@app.post("/mcp/tools/analyze_full_stack")
async def api_analyze_full_stack(request: ToolRequest = None):
    """Analyze entire Universal Agent stack."""
    result = analyze_full_stack()
    return {"content": json.dumps(result, indent=2, default=str)}


# ===== Document Writer Tools =====

@app.post("/mcp/tools/create_document_plan")
async def api_create_document_plan(request: ToolRequest):
    """STEP 1: Create a document outline."""
    if not request.title or not request.sections:
        raise HTTPException(status_code=400, detail="title and sections are required")
    result = create_document_plan(request.title, request.sections)
    return {"content": json.dumps(result, indent=2, default=str)}


@app.post("/mcp/tools/write_section")
async def api_write_section(request: ToolRequest):
    """STEP 2: Write content for one section."""
    if not request.section_id or not request.content:
        raise HTTPException(status_code=400, detail="section_id and content are required")
    result = write_section(request.section_id, request.content)
    return {"content": json.dumps(result, indent=2, default=str)}


@app.post("/mcp/tools/compile_document")
async def api_compile_document(request: ToolRequest):
    """STEP 3: Save the completed document."""
    if not request.filename:
        raise HTTPException(status_code=400, detail="filename is required")
    result = compile_document(request.filename)
    return {"content": json.dumps(result, indent=2, default=str)}


@app.post("/mcp/tools/get_plan_status")
async def api_get_plan_status(request: ToolRequest = None):
    """Check current document plan status."""
    result = get_plan_status()
    return {"content": json.dumps(result, indent=2, default=str)}


@app.get("/health")
async def health():
    """Health check."""
    stats = get_storage_stats()
    return {
        "status": "ok",
        "server": "autonomous_flow",
        "tools": len(ALL_TOOLS),
        "repos_tracked": stats["repos_tracked"],
        "total_chunks": stats["total_chunks"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)

