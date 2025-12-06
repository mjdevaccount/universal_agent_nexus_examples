# Repository Discovery & Chunking Task

## Objective

Discover all GitHub repositories with "universal_agent" prefix, chunk their Python files using AST parsing, store in Qdrant with structured naming, and generate a summary.

## How to Run

```bash
cd 09-autonomous-flow/backend
python discover_and_chunk_repos.py
```

## What It Does

1. **Searches GitHub** for repos with "universal_agent" prefix
2. **Discovers Python files** recursively in each repo
3. **Chunks files** using AST parsing (classes, functions)
4. **Stores in Qdrant** with unique collection names
5. **Generates summary** of connections and structure

## Collection Naming

Collections are named for easy access:
```
universal_agent_{owner}_{repo_name}_{date}
```

Example:
- `universal_agent_mjdevaccount_universal_agent_nexus_20251206`
- `universal_agent_mjdevaccount_universal_agent_fabric_20251206`

## Output Files

- `repo_summary_{context_id}.json` - Machine-readable summary
- `repo_summary_{context_id}.md` - Human-readable summary

## Requirements

- GitHub MCP server running (port 8003)
- Qdrant MCP server running (port 8002)
- Qdrant database running (Docker)
- GITHUB_TOKEN environment variable (optional, for private repos)

## Context ID

Each run gets a unique context ID:
```
discovery_{YYYYMMDD}_{HHMMSS}
```

This ensures:
- Unique storage per run
- Easy identification
- No data conflicts

