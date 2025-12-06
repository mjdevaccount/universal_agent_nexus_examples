"""
MCP Filesystem Server
Implements Model Context Protocol for filesystem operations.

December 2025 MCP Spec:
- SEP-986: Standardized tool naming
- Auto-discovery via introspection
- Standardized schema format
"""

from mcp.server import Server
from mcp.types import Tool, TextContent
from typing import Any
import os
from pathlib import Path


# Initialize MCP server
server = Server("filesystem-server")


@server.tool()
def read_file(path: str) -> str:
    """
    Read contents of a file.
    
    Args:
        path: Path to the file to read
        
    Returns:
        File contents as string
    """
    try:
        file_path = Path(path)
        if not file_path.exists():
            return f"Error: File not found: {path}"
        if not file_path.is_file():
            return f"Error: Path is not a file: {path}"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


@server.tool()
def write_file(path: str, content: str) -> str:
    """
    Write content to a file.
    
    Args:
        path: Path to the file to write
        content: Content to write
        
    Returns:
        Success message
    """
    try:
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"Successfully wrote {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


@server.tool()
def list_directory(path: str = ".") -> str:
    """
    List files and directories in a path.
    
    Args:
        path: Directory path (default: current directory)
        
    Returns:
        JSON string with directory listing
    """
    try:
        dir_path = Path(path)
        if not dir_path.exists():
            return f"Error: Directory not found: {path}"
        if not dir_path.is_dir():
            return f"Error: Path is not a directory: {path}"
        
        items = []
        for item in sorted(dir_path.iterdir()):
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None
            })
        
        import json
        return json.dumps(items, indent=2)
    except Exception as e:
        return f"Error listing directory: {str(e)}"


@server.tool()
def search_code(pattern: str, directory: str = ".") -> str:
    """
    Search for code patterns in files.
    
    Args:
        pattern: Regex pattern to search for
        directory: Directory to search in
        
    Returns:
        JSON string with search results
    """
    try:
        import re
        import json
        
        dir_path = Path(directory)
        if not dir_path.exists():
            return f"Error: Directory not found: {directory}"
        
        results = []
        regex = re.compile(pattern)
        
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
        
        return json.dumps(results, indent=2) if results else "No matches found"
    except Exception as e:
        return f"Error searching: {str(e)}"


if __name__ == "__main__":
    import uvicorn
    from mcp.server.fastapi import create_app
    
    app = create_app(server)
    uvicorn.run(app, host="0.0.0.0", port=8000)

