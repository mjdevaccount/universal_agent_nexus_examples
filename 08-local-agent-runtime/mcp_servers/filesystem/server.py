"""
MCP Filesystem Server
Implements Model Context Protocol for filesystem operations.

December 2025 MCP Spec:
- SEP-986: Standardized tool naming
- Auto-discovery via introspection
- Standardized schema format
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import json
import re

app = FastAPI(title="MCP Filesystem Server")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class ToolRequest(BaseModel):
    path: Optional[str] = None
    content: Optional[str] = None
    pattern: Optional[str] = None
    directory: Optional[str] = "."


# Tool definitions for introspection
TOOLS = [
    {
        "name": "read_file",
        "description": "Read contents of a file",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to file to read"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to file"},
                "content": {"type": "string", "description": "Content to write"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "list_directory",
        "description": "List files in a directory",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path", "default": "."}
            }
        }
    },
    {
        "name": "search_code",
        "description": "Search for code patterns",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern"},
                "directory": {"type": "string", "description": "Directory to search", "default": "."}
            },
            "required": ["pattern"]
        }
    }
]


@app.get("/mcp/tools")
async def list_tools():
    """MCP introspection endpoint - list available tools."""
    return {"tools": TOOLS}


@app.post("/mcp/tools/read_file")
async def read_file(request: ToolRequest):
    """Read contents of a file."""
    if not request.path:
        raise HTTPException(status_code=400, detail="path is required")
    
    try:
        file_path = Path(request.path)
        if not file_path.exists():
            return {"content": f"Error: File not found: {request.path}"}
        if not file_path.is_file():
            return {"content": f"Error: Path is not a file: {request.path}"}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {"content": content}
    except Exception as e:
        return {"content": f"Error reading file: {str(e)}"}


@app.post("/mcp/tools/write_file")
async def write_file(request: ToolRequest):
    """Write content to a file."""
    if not request.path or request.content is None:
        raise HTTPException(status_code=400, detail="path and content are required")
    
    try:
        file_path = Path(request.path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(request.content)
        
        return {"content": f"Successfully wrote {len(request.content)} bytes to {request.path}"}
    except Exception as e:
        return {"content": f"Error writing file: {str(e)}"}


@app.post("/mcp/tools/list_directory")
async def list_directory(request: ToolRequest):
    """List files and directories in a path."""
    path = request.path or "."
    
    try:
        dir_path = Path(path)
        if not dir_path.exists():
            return {"content": f"Error: Directory not found: {path}"}
        if not dir_path.is_dir():
            return {"content": f"Error: Path is not a directory: {path}"}
        
        items = []
        for item in sorted(dir_path.iterdir()):
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None
            })
        
        return {"content": json.dumps(items, indent=2)}
    except Exception as e:
        return {"content": f"Error listing directory: {str(e)}"}


@app.post("/mcp/tools/search_code")
async def search_code(request: ToolRequest):
    """Search for code patterns in files."""
    if not request.pattern:
        raise HTTPException(status_code=400, detail="pattern is required")
    
    directory = request.directory or "."
    
    try:
        dir_path = Path(directory)
        if not dir_path.exists():
            return {"content": f"Error: Directory not found: {directory}"}
        
        results = []
        regex = re.compile(request.pattern)
        
        # Search in Python files
        for py_file in dir_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if regex.search(line):
                            results.append({
                                "file": str(py_file.relative_to(dir_path)),
                                "line": line_num,
                                "match": line.strip()
                            })
            except Exception:
                continue
        
        return {"content": json.dumps(results, indent=2) if results else "No matches found"}
    except Exception as e:
        return {"content": f"Error searching: {str(e)}"}


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "server": "filesystem", "tools": len(TOOLS)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
