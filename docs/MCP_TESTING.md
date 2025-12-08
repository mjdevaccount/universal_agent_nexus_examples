# MCP Test Server Management - December 2025 Pattern

**Policy: No example test requires a manually started MCP server.**

## Overview

This repo uses **ephemeral MCP servers** with automatic cleanup. All test-started servers are managed by fixtures or helper runners, never as long-lived manual processes.

## Two Modes

### Mode A: Unit/Integration Tests

**Use pytest fixtures for automatic server lifecycle:**

```python
def test_something(mcp_servers):
    # Servers automatically started by fixture
    filesystem_url = mcp_servers["filesystem"]
    git_url = mcp_servers["git"]
    # Use servers
    ...
# Servers automatically stopped here
```

**Ports:** Test ports (8244, 8245) - separate from demo ports

**Cleanup:** Automatic via pytest fixture teardown

### Mode B: Demo/Example Run

**Use single-entry command that manages everything:**

```bash
python run_example.py
```

**Ports:** Demo ports (8344, 8345) - separate from test ports

**Cleanup:** Automatic on exit (context manager)

## Port Management

### Port Mapping

Ports are assigned via `tests/helpers/mcp_server_runner.py`:

```python
PORT_MAPPING = {
    "08-filesystem": 8144,      # Example 08 filesystem
    "08-git": 8145,             # Example 08 git
    "test-filesystem": 8244,    # Test filesystem
    "test-git": 8245,           # Test git
    "demo-filesystem": 8344,    # Demo filesystem
    "demo-git": 8345,           # Demo git
}
```

### Port Conflict Resolution

Before starting a server:
1. Check if port is in use
2. If in use and `kill_existing=True`, kill the process
3. Wait for port to be free
4. Start server

**No manual cleanup needed** - all handled automatically.

## Implementation Pattern

### For Tests (Mode A)

**Use pytest fixtures:**

```python
# conftest.py
@pytest.fixture(scope="function")
def mcp_servers():
    with run_mcp_servers_for_example("08", [
        {"module": "...", "port_name": "test-filesystem", "name": "filesystem"},
        {"module": "...", "port_name": "test-git", "name": "git"}
    ]) as server_urls:
        yield server_urls
    # Auto cleanup
```

### For Examples (Mode B)

**Use single-entry script:**

```python
# run_example.py
def main():
    with run_mcp_servers_for_example("08", [
        {"module": "...", "port_name": "demo-filesystem", "name": "filesystem"},
        {"module": "...", "port_name": "demo-git", "name": "git"}
    ]) as server_urls:
        # Run example
        ...
    # Auto cleanup
```

## Helper Functions

### `run_mcp_server_in_process()`

Start a single MCP server with automatic cleanup:

```python
with run_mcp_server_in_process(
    "mcp_servers.filesystem.server:app",
    port_name="test-filesystem"
) as url:
    # Use server at url
    ...
# Server automatically stopped
```

### `run_mcp_servers_for_example()`

Start multiple servers for an example:

```python
with run_mcp_servers_for_example("08", [
    {"module": "...", "port_name": "...", "name": "..."}
]) as server_urls:
    filesystem_url = server_urls["filesystem"]
    # Use servers
    ...
# All servers automatically stopped
```

### `ensure_port_free()`

Check and optionally kill process on port:

```python
if not ensure_port_free(port, kill_if_in_use=True):
    raise RuntimeError(f"Port {port} still in use")
```

## Best Practices

### ✅ DO

- Use fixtures for tests
- Use single-entry commands for examples
- Let helpers manage port conflicts
- Use port names from PORT_MAPPING
- Trust automatic cleanup

### ❌ DON'T

- Start servers manually for tests
- Hardcode ports (use PORT_MAPPING)
- Leave servers running after tests
- Ask contributors to manage servers
- Use production ports for tests

## Troubleshooting

### Port Still In Use

If you see "port still in use" errors:

1. Check if another process is using the port:
   ```bash
   # Windows
   netstat -ano | findstr :8144
   
   # Unix
   lsof -i :8144
   ```

2. The helper will try to kill it automatically
3. If that fails, manually kill the process

### Servers Not Starting

1. Check if required dependencies are installed
2. Verify server module paths are correct
3. Check server logs in fixture output
4. Ensure ports are not blocked by firewall

### Tests Hanging

1. Check if servers are actually starting (look for "[MCP] Server ready" messages)
2. Verify health endpoints are accessible
3. Check for port conflicts
4. Increase timeout in `run_mcp_server_in_process()` if needed

## CI/CD

In CI, servers are always ephemeral:

- Tests use fixtures (automatic cleanup)
- No containers or long-lived processes
- Each test job is isolated
- Ports are always freed after tests

## Migration Guide

**Old pattern (don't use):**
```bash
# Terminal 1
python mcp_servers/filesystem/server.py

# Terminal 2
python test_runtime.py
# Servers left running!
```

**New pattern (use this):**
```bash
# Single command
pytest test_runtime_fixed.py

# Or for demo
python run_example.py
# Everything cleaned up automatically
```

## References

- Implementation: `tests/helpers/mcp_server_runner.py`
- Example fixtures: `08-local-agent-runtime/conftest.py`
- Example runner: `08-local-agent-runtime/run_example.py`
- December 2025 MCP testing best practices

