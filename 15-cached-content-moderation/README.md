# Example 15 - Cached Content Moderation

**Demonstrates Cache Fabric Layer integration with Nexus compiler and Agent runtime.**

## Features

- ✅ **Nexus Integration** - System prompts stored in fabric during compilation
- ✅ **Runtime Integration** - Reads prompts from fabric (hot-reload enabled)
- ✅ **Execution Tracking** - All executions tracked in fabric
- ✅ **Feedback Loop** - Feedback recorded for continuous improvement
- ✅ **Metrics** - Real-time cache hit rate, latency, cost savings

## Architecture

```
Nexus Compiler
    ↓ stores system prompts
Cache Fabric (In-Memory/Redis/Vector)
    ↓ reads on each execution
Agent Runtime
    ↓ tracks state + feedback
Cache Fabric (updated)
```

## Usage

```bash
# Run with in-memory fabric (development)
python run_fabric_demo.py

# Run with Redis fabric (production)
REDIS_URL=redis://localhost:6379 python run_fabric_demo.py

# Run with Vector DB fabric (semantic search)
python run_fabric_demo.py --vector
```

## Files

- `manifest.yaml` - Content moderation graph definition
- `compiler_with_fabric.py` - Nexus + fabric integration
- `run_fabric_demo.py` - Full end-to-end demo

