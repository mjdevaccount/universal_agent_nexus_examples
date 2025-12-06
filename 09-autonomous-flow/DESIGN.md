# AutonomousFlow: Code Knowledge Management System

## Overview

A multi-agent system that keeps a vector database synchronized with GitHub repositories and answers questions about the codebase.

## Quick Start

```bash
# Start the MCP server
cd 09-autonomous-flow
python tools/server.py &

# Check current status
python agent.py status

# Sync all repos (will chunk Python files)
python agent.py sync

# Ask questions about the code
python agent.py query -q "How does the AWS adapter work?"
```

## Current Status

✅ **Working Features:**
- GitHub CLI integration (uses your `gh` auth)
- Automatic Python file discovery
- AST-based chunking (classes, functions, modules)
- Sync state tracking (SHA comparison)
- Change detection (only syncs modified files)
- Q&A agent for code questions

📊 **Example Output:**
```
📦 Sync Status:
   • mjdevaccount/universal_agent_fabric: 2 files, 10 chunks

💾 Storage Stats:
   Repos tracked: 1
   Total files: 2
   Total chunks: 10
```

## Target Repositories

```python
MANAGED_REPOS = [
    "mjdevaccount/universal_agent_fabric",
    "mjdevaccount/universal_agent_architecture",
    "mjdevaccount/universal_agent_nexus",
    "mjdevaccount/universal_agent_nexus_examples",
]
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR AGENT                        │
│  Decides: sync, query, or maintain based on user request    │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│  SYNC AGENT   │ │   QA AGENT    │ │ MAINT AGENT   │
│               │ │               │ │               │
│ • Check diffs │ │ • Search code │ │ • Cleanup     │
│ • Update      │ │ • Answer Qs   │ │ • Reindex     │
│ • Chunk       │ │ • Summarize   │ │ • Validate    │
└───────────────┘ └───────────────┘ └───────────────┘
```

## Tools

### 1. GitHub Tools (via `gh` CLI)

| Tool | Description | Parameters |
|------|-------------|------------|
| `gh_get_repo_commits` | Get recent commits with dates | `repo`, `since` |
| `gh_list_python_files` | List all .py files in repo | `repo`, `path` |
| `gh_get_file_with_metadata` | Get file content + last modified | `repo`, `path` |
| `gh_get_file_history` | Get commit history for a file | `repo`, `path` |

### 2. Chunk Management Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_sync_status` | Compare GitHub vs Qdrant state | `repo` |
| `chunk_and_store` | Chunk Python file and store | `repo`, `path`, `content` |
| `get_chunk_metadata` | Get chunk info (last_synced, hash) | `repo`, `path` |
| `delete_chunks` | Remove chunks for a file | `repo`, `path` |
| `list_stored_files` | List all files we have chunks for | `repo` |

### 3. Query Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `search_code` | Semantic search over all chunks | `query`, `repo` (optional) |
| `get_file_summary` | Get summary of what a file does | `repo`, `path` |
| `find_related_code` | Find code related to a concept | `concept` |
| `answer_question` | RAG-based Q&A over codebase | `question` |

### 4. Reasoning Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `analyze_changes` | Determine what needs syncing | `repo` |
| `create_sync_plan` | Create ordered list of sync tasks | `repos` |
| `validate_chunks` | Check chunk integrity | `repo` |

## Sync Flow

```
1. CHECK PHASE
   ├── For each managed repo:
   │   ├── gh_get_repo_commits(since=last_sync)
   │   └── Compare with stored metadata
   │
2. PLAN PHASE
   ├── Identify files that changed
   ├── Identify new files
   ├── Identify deleted files
   │
3. EXECUTE PHASE
   ├── For changed/new files:
   │   ├── gh_get_file_with_metadata
   │   ├── chunk_and_store
   │   └── update_metadata
   ├── For deleted files:
   │   └── delete_chunks
   │
4. VERIFY PHASE
   └── validate_chunks for each repo
```

## Data Model

### Chunk Metadata (stored in Qdrant)

```json
{
  "id": "uuid",
  "repo": "mjdevaccount/universal_agent_nexus",
  "file_path": "adapters/aws/compiler.py",
  "chunk_type": "class",
  "chunk_name": "AWSCompiler",
  "line_start": 45,
  "line_end": 120,
  "content_hash": "sha256:abc123...",
  "github_sha": "abc123def456",
  "last_synced": "2025-12-06T03:30:00Z",
  "embedding": [0.1, 0.2, ...]
}
```

### Sync State (stored locally)

```json
{
  "repos": {
    "mjdevaccount/universal_agent_nexus": {
      "last_sync": "2025-12-06T03:30:00Z",
      "last_github_commit": "abc123",
      "files_synced": 42,
      "total_chunks": 156
    }
  }
}
```

## User Interactions

### Sync Commands
- "Sync all repos" → Full sync check
- "Sync universal_agent_nexus" → Single repo sync
- "What needs updating?" → Show sync status

### Query Commands
- "How does the AWS compiler work?"
- "What files implement the MCP protocol?"
- "Show me the data flow for agent execution"
- "Find all TODO comments"

### Maintenance Commands
- "Reindex everything"
- "Validate chunk integrity"
- "Show storage statistics"

