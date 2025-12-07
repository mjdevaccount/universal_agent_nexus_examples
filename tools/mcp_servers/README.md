# MCP Servers for AutonomousFlow

## Available Servers

### 1. Filesystem Server (port 8000)
**Location:** `08-local-agent-runtime/mcp_servers/filesystem/server.py`

**Tools:**
- `read_file` - Read file contents
- `write_file` - Write content to file
- `list_directory` - List directory contents
- `search_code` - Search for code patterns

### 2. Git Server (port 8001)
**Location:** `08-local-agent-runtime/mcp_servers/git/server.py`

**Tools:**
- `git_status` - Get repository status
- `git_commit` - Create a commit
- `git_diff` - Get diff of changes

### 3. Qdrant Server (port 8002)
**Location:** `tools/mcp_servers/qdrant/server.py`

**Tools:**
- `chunk_and_store_python` - Chunk Python files using AST and store in Qdrant
- `store_text` - Store text in Qdrant
- `search_qdrant` - Search Qdrant vector database
- `list_collections` - List all collections

**Features:**
- ✅ AST-based Python chunking (functions, classes)
- ✅ Unique collection names per context
- ✅ Semantic chunking (preserves structure)

**Requirements:**
```bash
pip install qdrant-client
```

**Qdrant Connection:**
- Host: localhost
- Port: 6333 (from Docker container)

### 4. GitHub Server (port 8003)
**Location:** `tools/mcp_servers/github/server.py`

**Tools:**
- `github_get_file` - Get file contents from repository
- `github_list_files` - List files in repository
- `github_create_issue` - Create GitHub issue
- `github_list_issues` - List repository issues
- `github_search_repos` - Search repositories

**Requirements:**
```bash
pip install PyGithub
```

**Configuration:**
Set `GITHUB_TOKEN` environment variable:
```bash
export GITHUB_TOKEN=your_token_here
```

## Starting Servers

```bash
# Terminal 1: Filesystem
python 08-local-agent-runtime/mcp_servers/filesystem/server.py

# Terminal 2: Git
python 08-local-agent-runtime/mcp_servers/git/server.py

# Terminal 3: Qdrant
python tools/mcp_servers/qdrant/server.py

# Terminal 4: GitHub
python tools/mcp_servers/github/server.py
```

## Health Checks

```bash
curl http://localhost:8000/health  # Filesystem
curl http://localhost:8001/health  # Git
curl http://localhost:8002/health  # Qdrant
curl http://localhost:8003/health  # GitHub
```

## Python Chunking Details

The Qdrant server uses AST parsing for intelligent Python chunking:

1. **Extracts imports** - Preserved at top of chunks
2. **Chunks by classes** - Each class becomes a chunk
3. **Chunks by functions** - Standalone functions become chunks
4. **Fallback** - Line-based chunking if AST fails

**Chunk Size:** Max 2000 characters per chunk
**Preserves:** Docstrings, comments, structure

## Unique Storage

Each context gets a unique collection name:
```
{purpose}_{context_id}_{date}
```

Example: `python_chunks_abc123_20251206`

This ensures isolation between different agent runs.


