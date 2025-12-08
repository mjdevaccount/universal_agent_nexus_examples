# Cache Fabric Integration Guide

## Overview

Cache fabric sits between Nexus (compilation) and runtime agents.

Provides:
- **System prompt caching** - Store & hot-reload prompts
- **Execution tracking** - Record input/output/state
- **Feedback recording** - Collect user/automated feedback
- **Multiple backends** - Memory, Redis, Vector DBs

## Architecture

```
Nexus (Compilation)
    ↓
Cache Fabric (Persistence)
    ├─ Memory (development)
    ├─ Redis (production)
    └─ Vector DB (semantic search)
    ↓
Runtime Agent (Execution)
```

## Quick Start

### 1. Initialize Fabric

```python
from shared.cache_fabric import InMemoryFabric, RedisFabric

# Development: In-memory
fabric = InMemoryFabric()

# Production: Redis
fabric = RedisFabric(redis_url="redis://localhost:6379")
```

### 2. Store System Prompt

```python
import asyncio

async def setup():
    await fabric.set_context(
        key="router:main:system_message",
        value="You are a helpful assistant",
        scope="GLOBAL",
        metadata={"router_name": "main", "version": "1.0"}
    )

asyncio.run(setup())
```

### 3. Retrieve & Use

```python
async def execute():
    context = await fabric.get_context(
        key="router:main:system_message",
        scope="GLOBAL"
    )
    
    system_prompt = context.value if context else "default prompt"
    print(system_prompt)

asyncio.run(execute())
```

## Backend Comparison

| Feature | Memory | Redis | Vector |
|---------|--------|-------|--------|
| **Speed** | Very fast | Fast | Medium |
| **Persistence** | No | Yes | Yes |
| **Multi-process** | No | Yes | Yes |
| **Semantic search** | No | No | Yes |
| **Use case** | Dev/Test | Production | Semantic queries |

## Scopes

Context is organized by scope:

```python
# GLOBAL - Shared across all executions
await fabric.set_context(
    key="system_prompt",
    value="...",
    scope="GLOBAL"
)

# EXECUTION - Specific to one execution
await fabric.set_context(
    key="execution:exec-123:state",
    value={...},
    scope="EXECUTION"
)

# FEEDBACK - Feedback data
await fabric.set_context(
    key="feedback:exec-123:rating",
    value={"score": 5},
    scope="FEEDBACK"
)

# USER - User-specific context
await fabric.set_context(
    key="user:user-456:preferences",
    value={...},
    scope="USER"
)
```

## System Prompt Caching

### Store on Startup

```python
class MyExample(StandardExample):
    def __init__(self):
        super().__init__(cache_backend="redis")
        # Cache prompts from manifest
        asyncio.run(self._cache_system_prompts())
    
    async def _cache_system_prompts(self):
        # Extract from manifest or IR
        prompts = {
            "router:main:system_message": "Your prompt here",
            "router:tool_router:system_message": "Tool router prompt",
        }
        
        for key, value in prompts.items():
            await self.fabric.set_context(
                key=key,
                value=value,
                scope="GLOBAL",
                metadata={"source": "manifest"}
            )
```

### Retrieve During Execution

```python
async def execute(self, input_data):
    # Get system prompt (cached)
    system_prompt = await self.fabric.get_context(
        key="router:main:system_message",
        scope="GLOBAL"
    )
    
    if system_prompt:
        system = system_prompt.value
    else:
        system = "default system prompt"
    
    # Use in execution
    response = await llm.generate(system=system, **input_data)
    
    return response
```

### Hot-Reload Pattern

```python
# Update prompt without restarting
async def update_prompt(fabric, key, new_prompt):
    await fabric.set_context(
        key=key,
        value=new_prompt,
        scope="GLOBAL"
    )

# All future executions use new prompt
await update_prompt(
    fabric,
    "router:main:system_message",
    "Updated system prompt"
)
```

## Execution Tracking

### Record Execution

```python
import uuid
from datetime import datetime

async def execute(self, input_data):
    execution_id = str(uuid.uuid4())
    start_time = datetime.now()
    
    # Execute graph
    output = await self.run_graph(input_data)
    
    # Record execution
    await self.fabric.set_context(
        key=f"execution:{execution_id}",
        value={
            "timestamp": start_time.isoformat(),
            "input": input_data,
            "output": output,
            "latency_ms": (datetime.now() - start_time).total_seconds() * 1000,
        },
        scope="EXECUTION",
        metadata={"execution_id": execution_id}
    )
    
    return output
```

### Query Executions

```python
# Get recent executions
executions = await fabric.query(
    pattern="execution:*",
    scope="EXECUTION",
    limit=10
)

# Calculate metrics
total = len(executions)
avg_latency = sum(
    e.value.get("latency_ms", 0)
    for e in executions
) / total if total > 0 else 0

print(f"Total executions: {total}")
print(f"Avg latency: {avg_latency:.2f}ms")
```

## Feedback Recording

### Record User Feedback

```python
async def record_feedback(self, execution_id, feedback):
    await self.fabric.set_context(
        key=f"feedback:{execution_id}",
        value={
            "timestamp": datetime.now().isoformat(),
            "rating": feedback.get("rating"),  # 1-5
            "comment": feedback.get("comment"),
            "corrections": feedback.get("corrections"),  # Ground truth corrections
        },
        scope="FEEDBACK",
        metadata={"execution_id": execution_id}
    )
```

### Automated Feedback

```python
async def record_automated_feedback(self, execution_id, output):
    # Auto-scoring based on metrics
    score = 0
    
    if output.get("confidence", 0) > 0.9:
        score += 1
    if output.get("latency_ms", 0) < 500:
        score += 1
    if output.get("parsed", {}).get("category"):
        score += 1
    
    await self.fabric.set_context(
        key=f"feedback:{execution_id}:auto",
        value={"auto_score": score, "max_score": 3},
        scope="FEEDBACK"
    )
```

## Multi-User Context

```python
async def store_user_context(fabric, user_id, context_data):
    """Store user-specific context."""
    await fabric.set_context(
        key=f"user:{user_id}:context",
        value={
            "preferences": context_data.get("preferences"),
            "history": context_data.get("history"),
            "settings": context_data.get("settings"),
        },
        scope="USER",
        metadata={"user_id": user_id}
    )

async def get_user_context(fabric, user_id):
    """Retrieve user context for personalization."""
    context = await fabric.get_context(
        key=f"user:{user_id}:context",
        scope="USER"
    )
    return context.value if context else {}
```

## Redis Configuration

### Connection Setup

```python
from shared.cache_fabric import RedisFabric

fabric = RedisFabric(
    redis_url="redis://localhost:6379",
    db=0,  # Redis database number
    password="optional_password",
    ssl=False,
    decode_responses=True
)
```

### TTL (Time To Live)

```python
# Expire context after 1 hour
await fabric.set_context(
    key="temp_data",
    value={...},
    scope="GLOBAL",
    ttl=3600  # seconds
)
```

### Persistence

```python
# Redis configuration for persistence
# In redis.conf:
# save 900 1      # Save if 1 key changed in 900s
# save 300 10     # Save if 10 keys changed in 300s
# save 60 10000   # Save if 10000 keys changed in 60s
```

## Vector DB (Qdrant)

### Setup

```python
from shared.cache_fabric import VectorFabric

fabric = VectorFabric(
    qdrant_url="http://localhost:6333",
    collection_name="contexts",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    vector_size=384  # Model dimension
)
```

### Semantic Search

```python
# Store embeddings of prompts
await fabric.set_context(
    key="prompt:1",
    value="You are a helpful assistant focused on Python",
    scope="GLOBAL"
)

# Search for similar prompts
similar = await fabric.search(
    query="Python programming help",
    scope="GLOBAL",
    limit=5
)

for result in similar:
    print(f"Similarity: {result.similarity:.2f}")
    print(f"Value: {result.value}")
```

## Monitoring & Metrics

```python
async def get_fabric_metrics(fabric):
    """Get cache fabric metrics."""
    return {
        "context_count": await fabric.count_contexts(),
        "memory_usage_bytes": await fabric.get_memory_usage(),
        "hit_rate": await fabric.get_hit_rate(),
        "avg_latency_ms": await fabric.get_avg_latency(),
    }

metrics = asyncio.run(get_fabric_metrics(fabric))
print(f"Cache hit rate: {metrics['hit_rate']:.2%}")
print(f"Avg latency: {metrics['avg_latency_ms']:.2f}ms")
```

## Error Handling

```python
async def safe_get_context(fabric, key, scope):
    """Safely retrieve context with fallback."""
    try:
        context = await fabric.get_context(key=key, scope=scope)
        return context.value if context else None
    except Exception as e:
        logger.warning(f"Error retrieving {key}: {e}")
        return None  # Fallback to None
```

## Best Practices

1. **Use GLOBAL for shared data** - System prompts, configuration
2. **Use EXECUTION for transient data** - Per-execution state
3. **Use FEEDBACK for analytics** - Training data collection
4. **Use USER for personalization** - User preferences, history
5. **Implement TTL** - Prevent unbounded growth
6. **Monitor memory** - Watch fabric size in production
7. **Batch operations** - Reduce round-trips
8. **Handle errors gracefully** - Fallback when fabric unavailable

## Troubleshooting

### Redis Connection Issues

```python
# Check connection
from redis import Redis

r = Redis.from_url("redis://localhost:6379")
try:
    r.ping()
    print("Connected!")
except Exception as e:
    print(f"Connection failed: {e}")
```

### Memory Leaks

```python
# Monitor size
info = fabric.backend.info()
print(f"Memory: {info.get('memory_human')}")
print(f"Keys: {fabric.backend.dbsize()}")

# Clear old data
await fabric.cleanup(before_timestamp="2024-01-01")
```

### Performance Tuning

```python
# Enable pipeline for batch operations
async with fabric.pipeline() as pipe:
    for i in range(1000):
        await pipe.set_context(
            key=f"key:{i}",
            value={"data": i}
        )
    await pipe.execute()  # Single batch operation
```
