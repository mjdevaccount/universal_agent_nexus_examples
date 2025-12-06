"""
MCP Qdrant Server
Implements Model Context Protocol for Qdrant vector database operations.

Features:
- Python file chunking with AST parsing
- Unique collection names per context
- Semantic chunking (functions, classes)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from pathlib import Path
import ast
import hashlib
import json
import uuid
from datetime import datetime

app = FastAPI(title="MCP Qdrant Server")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Qdrant client (lazy import)
_qdrant_client = None
_qdrant_collections = {}  # Cache collection names


def get_qdrant_client():
    """Lazy import and initialize Qdrant client."""
    global _qdrant_client
    if _qdrant_client is None:
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams, PointStruct
            _qdrant_client = QdrantClient(host="localhost", port=6333)
            return _qdrant_client, VectorParams, PointStruct, Distance
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="qdrant-client not installed. Install with: pip install qdrant-client"
            )
    from qdrant_client.models import Distance, VectorParams, PointStruct
    return _qdrant_client, VectorParams, PointStruct, Distance


class ToolRequest(BaseModel):
    collection_name: Optional[str] = None
    file_path: Optional[str] = None
    text: Optional[str] = None
    query: Optional[str] = None
    limit: Optional[int] = 10
    context_id: Optional[str] = None  # For unique storage


def generate_unique_collection_name(context_id: str, base_name: str = "autonomous_flow") -> str:
    """Generate unique collection name with context ID."""
    if context_id:
        return f"{base_name}_{context_id}_{datetime.now().strftime('%Y%m%d')}"
    return f"{base_name}_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d')}"


def chunk_python_content(content: str, file_name: str = "unknown.py", max_chunk_size: int = 2000) -> List[Dict]:
    """
    Chunk Python content using AST parsing.
    
    Chunks by:
    - Functions (standalone or in classes)
    - Classes (with their methods)
    - Module-level code
    
    Preserves:
    - Imports at top
    - Docstrings
    - Comments
    """
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        # Fallback: simple line-based chunking for invalid Python
        return chunk_by_lines(content, max_chunk_size, file_name)
    
    chunks = []
    file_lines = content.split('\n')
    
    # Extract imports
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            start = node.lineno - 1
            end = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
            import_text = '\n'.join(file_lines[start:end])
            imports.append(import_text)
    
    import_block = '\n'.join(imports) if imports else ""
    
    # Process classes
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            start = node.lineno - 1
            end = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
            
            # Get class code
            class_code = '\n'.join(file_lines[start:end])
            
            # Add imports if this is first chunk
            if not chunks and import_block:
                class_code = import_block + '\n\n' + class_code
            
            chunks.append({
                "text": class_code,
                "type": "class",
                "name": node.name,
                "line_start": node.lineno,
                "line_end": end,
                "file_path": file_name
            })
    
    # Process standalone functions
    def is_in_class(func_node, tree):
        """Check if function is inside a class."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if item == func_node:
                        return True
        return False
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Skip if already in a class
            if is_in_class(node, tree):
                continue
            
            start = node.lineno - 1
            end = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
            
            func_code = '\n'.join(file_lines[start:end])
            
            # Add imports if this is first standalone function
            if not any(c.get('type') == 'function' for c in chunks) and import_block:
                func_code = import_block + '\n\n' + func_code
            
            chunks.append({
                "text": func_code,
                "type": "function",
                "name": node.name,
                "line_start": node.lineno,
                "line_end": end,
                "file_path": file_name
            })
    
    # If no classes/functions, chunk by lines
    if not chunks:
        chunks = chunk_by_lines(content, max_chunk_size, file_name)
        if import_block and chunks:
            chunks[0]["text"] = import_block + '\n\n' + chunks[0]["text"]
    
    return chunks


def chunk_python_file(file_path: str, max_chunk_size: int = 2000) -> List[Dict]:
    """Chunk Python file by reading it and delegating to chunk_python_content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return [{"error": f"Could not read file: {str(e)}"}]
    
    return chunk_python_content(content, file_path, max_chunk_size)


def chunk_by_lines(content: str, max_size: int, file_name: str) -> List[Dict]:
    """Fallback: chunk by lines when AST parsing fails."""
    lines = content.split('\n')
    chunks = []
    current_chunk = []
    current_size = 0
    
    for i, line in enumerate(lines):
        line_size = len(line) + 1  # +1 for newline
        if current_size + line_size > max_size and current_chunk:
            chunks.append({
                "text": '\n'.join(current_chunk),
                "type": "lines",
                "line_start": i - len(current_chunk) + 1,
                "line_end": i,
                "file_path": file_name
            })
            current_chunk = []
            current_size = 0
        current_chunk.append(line)
        current_size += line_size
    
    if current_chunk:
        chunks.append({
            "text": '\n'.join(current_chunk),
            "type": "lines",
            "line_start": len(lines) - len(current_chunk) + 1,
            "line_end": len(lines),
            "file_path": file_name
        })
    
    return chunks


# Tool definitions
TOOLS = [
    {
        "name": "chunk_and_store_python",
        "description": "Chunk a Python file using AST parsing and store in Qdrant",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to Python file"},
                "collection_name": {"type": "string", "description": "Qdrant collection name"},
                "context_id": {"type": "string", "description": "Unique context ID for storage isolation"}
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "store_text",
        "description": "Store text in Qdrant vector database",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to store"},
                "collection_name": {"type": "string", "description": "Qdrant collection name"},
                "context_id": {"type": "string", "description": "Unique context ID"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "search_qdrant",
        "description": "Search Qdrant vector database",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "collection_name": {"type": "string", "description": "Collection to search"},
                "limit": {"type": "integer", "description": "Max results", "default": 10},
                "context_id": {"type": "string", "description": "Context ID"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "list_collections",
        "description": "List all Qdrant collections",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "chunk_and_store_python_content",
        "description": "Chunk Python code content (from GitHub or elsewhere) using AST parsing and store in Qdrant",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Python code content to chunk"},
                "file_name": {"type": "string", "description": "Name of the file (for metadata)"},
                "repo_name": {"type": "string", "description": "Repository name (for metadata)"},
                "collection_name": {"type": "string", "description": "Qdrant collection name"},
                "context_id": {"type": "string", "description": "Unique context ID for storage isolation"}
            },
            "required": ["content", "file_name"]
        }
    }
]


@app.get("/mcp/tools")
async def list_tools():
    """MCP introspection endpoint."""
    return {"tools": TOOLS}


@app.post("/mcp/tools/chunk_and_store_python")
async def chunk_and_store_python(request: ToolRequest):
    """Chunk Python file and store in Qdrant."""
    if not request.file_path:
        raise HTTPException(status_code=400, detail="file_path is required")
    
    file_path = Path(request.file_path)
    if not file_path.exists() or not file_path.suffix == '.py':
        return {"content": f"Error: Python file not found: {file_path}"}
    
    # Generate unique collection name
    context_id = request.context_id or str(uuid.uuid4())[:8]
    collection_name = request.collection_name or generate_unique_collection_name(
        context_id, "python_chunks"
    )
    
    # Chunk the file
    chunks = chunk_python_file(str(file_path), max_chunk_size=2000)
    
    if chunks and "error" in chunks[0]:
        return {"content": chunks[0]["error"]}
    
    # Store in Qdrant (for now, just return chunk info - embedding would go here)
    # In production, you'd generate embeddings and store vectors
    result = {
        "collection_name": collection_name,
        "context_id": context_id,
        "chunks_created": len(chunks),
        "chunks": [
            {
                "type": c.get("type"),
                "name": c.get("name", "unknown"),
                "lines": f"{c.get('line_start')}-{c.get('line_end')}",
                "size": len(c.get("text", ""))
            }
            for c in chunks[:5]  # Show first 5
        ]
    }
    
    return {"content": json.dumps(result, indent=2)}


@app.post("/mcp/tools/store_text")
async def store_text(request: ToolRequest):
    """Store text in Qdrant."""
    if not request.text:
        raise HTTPException(status_code=400, detail="text is required")
    
    context_id = request.context_id or str(uuid.uuid4())[:8]
    collection_name = request.collection_name or generate_unique_collection_name(
        context_id, "text_store"
    )
    
    # In production, generate embedding and store
    result = {
        "collection_name": collection_name,
        "context_id": context_id,
        "text_length": len(request.text),
        "status": "ready_for_storage"
    }
    
    return {"content": json.dumps(result, indent=2)}


@app.post("/mcp/tools/search_qdrant")
async def search_qdrant(request: ToolRequest):
    """Search Qdrant vector database."""
    if not request.query:
        raise HTTPException(status_code=400, detail="query is required")
    
    # In production, generate query embedding and search
    result = {
        "query": request.query,
        "collection": request.collection_name or "default",
        "limit": request.limit,
        "status": "search_ready",
        "note": "Embedding generation required for actual search"
    }
    
    return {"content": json.dumps(result, indent=2)}


@app.post("/mcp/tools/list_collections")
async def list_collections(request: ToolRequest = None):
    """List all Qdrant collections."""
    try:
        client, _, _, _ = get_qdrant_client()
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        return {"content": json.dumps({"collections": collection_names}, indent=2)}
    except Exception as e:
        return {"content": f"Error: {str(e)}"}


class ContentChunkRequest(BaseModel):
    """Request model for chunking Python content directly."""
    content: str
    file_name: str
    repo_name: Optional[str] = None
    collection_name: Optional[str] = None
    context_id: Optional[str] = None


@app.post("/mcp/tools/chunk_and_store_python_content")
async def chunk_and_store_python_content(request: ContentChunkRequest):
    """Chunk Python code content (from GitHub or elsewhere) and store in Qdrant."""
    if not request.content:
        raise HTTPException(status_code=400, detail="content is required")
    if not request.file_name:
        raise HTTPException(status_code=400, detail="file_name is required")
    
    # Generate unique collection name
    context_id = request.context_id or (request.repo_name or str(uuid.uuid4())[:8])
    collection_name = request.collection_name or generate_unique_collection_name(
        context_id, "python_chunks"
    )
    
    # Chunk the content
    chunks = chunk_python_content(request.content, request.file_name, max_chunk_size=2000)
    
    if chunks and "error" in chunks[0]:
        return {"content": chunks[0]["error"]}
    
    # Add repo metadata to chunks
    for chunk in chunks:
        chunk["repo_name"] = request.repo_name
        chunk["file_name"] = request.file_name
    
    # Return chunk info (in production, you'd generate embeddings and store)
    result = {
        "collection_name": collection_name,
        "context_id": context_id,
        "repo_name": request.repo_name,
        "file_name": request.file_name,
        "chunks_created": len(chunks),
        "chunks": [
            {
                "type": c.get("type"),
                "name": c.get("name", "unknown"),
                "lines": f"{c.get('line_start')}-{c.get('line_end')}",
                "size": len(c.get("text", ""))
            }
            for c in chunks[:10]  # Limit preview
        ],
        "status": "chunked_successfully"
    }
    
    return {"content": json.dumps(result, indent=2)}


@app.get("/health")
async def health():
    """Health check."""
    try:
        client, _, _, _ = get_qdrant_client()
        collections = client.get_collections()
        return {
            "status": "ok",
            "server": "qdrant",
            "tools": len(TOOLS),
            "qdrant_connected": True,
            "collections": len(collections.collections)
        }
    except Exception as e:
        return {
            "status": "error",
            "server": "qdrant",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

