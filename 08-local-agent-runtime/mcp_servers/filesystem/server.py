"""
MCP Filesystem Server
Implements Model Context Protocol for filesystem operations.

December 2025 MCP Spec compliant.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import re

app = FastAPI(title="MCP Filesystem Server")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class ReadFileRequest(BaseModel):
    path: str


class WriteFileRequest(BaseModel):
    path: str
    content: str


class ListDirectoryRequest(BaseModel):
    path: str


class SearchCodeRequest(BaseModel):
    pattern: str
    directory: str


# Tool definitions
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
                "path": {"type": "string", "description": "Path to file to write"},
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
                "path": {"type": "string", "description": "Directory path"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "search_code",
        "description": "Search for code patterns in files",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Search pattern (regex)"},
                "directory": {"type": "string", "description": "Directory to search"}
            },
            "required": ["pattern", "directory"]
        }
    }
]


@app.get("/mcp/tools")
async def list_tools():
    """MCP introspection endpoint."""
    return {"tools": TOOLS}


@app.post("/mcp/tools/read_file")
async def read_file(request: ReadFileRequest):
    """Read file contents."""
    try:
        file_path = Path(request.path)
        if not file_path.exists():
            return {"content": f"Error: File not found: {request.path}"}
        
        if not file_path.is_file():
            return {"content": f"Error: Not a file: {request.path}"}
        
        content = file_path.read_text(encoding='utf-8', errors='replace')
        return {"content": content}
    except Exception as e:
        return {"content": f"Error: {str(e)}"}


@app.post("/mcp/tools/write_file")
async def write_file(request: WriteFileRequest):
    """Write content to file."""
    try:
        file_path = Path(request.path)
        
        # Create parent directory if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_path.write_text(request.content, encoding='utf-8')
        return {"content": f"File written: {request.path}"}
    except Exception as e:
        return {"content": f"Error: {str(e)}"}


@app.post("/mcp/tools/list_directory")
async def list_directory(request: ListDirectoryRequest):
    """List files in directory."""
    try:
        dir_path = Path(request.path)
        if not dir_path.exists():
            return {"content": f"Error: Directory not found: {request.path}"}
        
        if not dir_path.is_dir():
            return {"content": f"Error: Not a directory: {request.path}"}
        
        items = []
        for item in sorted(dir_path.iterdir()):
            item_type = "directory" if item.is_dir() else "file"
            items.append(f"{item_type}: {item.name}")
        
        return {"content": "\n".join(items) if items else "Directory is empty"}
    except Exception as e:
        return {"content": f"Error: {str(e)}"}


@app.post("/mcp/tools/search_code")
async def search_code(request: SearchCodeRequest):
    """Search for code patterns."""
    try:
        dir_path = Path(request.directory)
        if not dir_path.exists():
            return {"content": f"Error: Directory not found: {request.directory}"}
        
        if not dir_path.is_dir():
            return {"content": f"Error: Not a directory: {request.directory}"}
        
        pattern = re.compile(request.pattern, re.IGNORECASE)
        matches = []
        
        # Search in Python files
        for py_file in dir_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8', errors='replace')
                for line_num, line in enumerate(content.split('\n'), 1):
                    if pattern.search(line):
                        matches.append(f"{py_file}:{line_num}: {line.strip()}")
            except Exception:
                continue
        
        return {"content": "\n".join(matches) if matches else "No matches found"}
    except Exception as e:
        return {"content": f"Error: {str(e)}"}


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "server": "filesystem", "tools": len(TOOLS)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8144)
