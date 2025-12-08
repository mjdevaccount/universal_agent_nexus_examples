"""
MCP Server Runner Helper - December 2025 Pattern

Manages ephemeral MCP servers for tests with automatic cleanup.
No leftover processes, no port conflicts.

Usage:
    # In-process (preferred for tests)
    async with mcp_test_client() as client:
        result = await client.call_tool("read_file", {"path": "test.txt"})
    
    # Subprocess (for integration tests)
    with run_mcp_server_in_process(server_module, port=8144) as url:
        # Server running at url, auto-cleaned on exit
        ...
"""

import socket
import subprocess
import time
import signal
import os
import sys
from pathlib import Path
from typing import Optional, Generator, Callable
from contextlib import contextmanager
import httpx


# Port mapping for examples (avoid conflicts)
PORT_MAPPING = {
    "08-filesystem": 8144,
    "08-git": 8145,
    "test-filesystem": 8244,  # Test ports (different from examples)
    "test-git": 8245,
    "demo-filesystem": 8344,   # Demo ports
    "demo-git": 8345,
}


def find_free_port(start_port: int, max_attempts: int = 10) -> int:
    """Find a free port starting from start_port."""
    for offset in range(max_attempts):
        port = start_port + offset
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"Could not find free port starting from {start_port}")


def is_port_in_use(port: int) -> bool:
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False
        except OSError:
            return True


def kill_process_on_port(port: int) -> bool:
    """
    Kill any process using the specified port.
    Returns True if a process was killed, False otherwise.
    """
    if sys.platform == 'win32':
        # Windows: use netstat to find PID, then taskkill
        try:
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True,
                timeout=5
            )
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        try:
                            subprocess.run(
                                ['taskkill', '/F', '/PID', pid],
                                capture_output=True,
                                timeout=5
                            )
                            print(f"[CLEANUP] Killed process {pid} on port {port}")
                            time.sleep(1)  # Wait for port to be released
                            return True
                        except Exception:
                            pass
        except Exception as e:
            print(f"[WARN] Could not kill process on port {port}: {e}")
    else:
        # Unix: use lsof to find PID, then kill
        try:
            result = subprocess.run(
                ['lsof', '-ti', f':{port}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.stdout.strip():
                pid = result.stdout.strip()
                try:
                    os.kill(int(pid), signal.SIGTERM)
                    time.sleep(1)
                    # Force kill if still running
                    try:
                        os.kill(int(pid), signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    print(f"[CLEANUP] Killed process {pid} on port {port}")
                    return True
                except Exception:
                    pass
        except Exception:
            pass
    
    return False


def ensure_port_free(port: int, kill_if_in_use: bool = True) -> bool:
    """
    Ensure a port is free. Optionally kill process if in use.
    Returns True if port is free, False otherwise.
    """
    if not is_port_in_use(port):
        return True
    
    if kill_if_in_use:
        if kill_process_on_port(port):
            # Wait a bit and check again
            time.sleep(2)
            return not is_port_in_use(port)
    
    return False


@contextmanager
def run_mcp_server_in_process(
    server_module: str,
    port: Optional[int] = None,
    port_name: Optional[str] = None,
    kill_existing: bool = True
) -> Generator[str, None, None]:
    """
    Run an MCP server in a subprocess with automatic cleanup.
    
    Args:
        server_module: Python module path (e.g., "mcp_servers.filesystem.server:app")
        port: Specific port to use (or None to find free port)
        port_name: Name in PORT_MAPPING (e.g., "test-filesystem")
        kill_existing: Kill existing process on port if in use
    
    Yields:
        Server URL (e.g., "http://localhost:8144/mcp")
    
    Example:
        with run_mcp_server_in_process(
            "mcp_servers.filesystem.server:app",
            port_name="test-filesystem"
        ) as url:
            # Use server at url
            ...
        # Server automatically stopped
    """
    # Determine port
    if port is None and port_name:
        port = PORT_MAPPING.get(port_name, 8144)
    elif port is None:
        port = find_free_port(8144)
    
    # Ensure port is free
    if not ensure_port_free(port, kill_if_in_use=kill_existing):
        raise RuntimeError(f"Port {port} is still in use after cleanup attempt")
    
    # Start server
    cmd = [
        sys.executable, "-m", "uvicorn",
        server_module,
        "--host", "0.0.0.0",
        "--port", str(port)
    ]
    
    process = None
    try:
        print(f"[MCP] Starting server on port {port}...")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Wait for server to be ready
        url = f"http://localhost:{port}/mcp"
        max_wait = 10
        for _ in range(max_wait):
            try:
                response = httpx.get(f"http://localhost:{port}/health", timeout=1)
                if response.status_code == 200:
                    print(f"[MCP] Server ready at {url}")
                    yield url
                    return
            except Exception:
                time.sleep(1)
        
        # Check if process is still running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise RuntimeError(
                f"Server failed to start:\n"
                f"STDOUT: {stdout.decode()}\n"
                f"STDERR: {stderr.decode()}"
            )
        
        raise RuntimeError(f"Server did not become ready within {max_wait} seconds")
        
    finally:
        # Cleanup: kill process
        if process:
            print(f"[MCP] Stopping server on port {port}...")
            try:
                if sys.platform == 'win32':
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                else:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                
                # Ensure port is free
                time.sleep(1)
                if is_port_in_use(port):
                    kill_process_on_port(port)
                
                print(f"[MCP] Server stopped")
            except Exception as e:
                print(f"[WARN] Error stopping server: {e}")


@contextmanager
def run_mcp_servers_for_example(
    example_name: str,
    servers: list[dict]
) -> Generator[dict, None, None]:
    """
    Run multiple MCP servers for an example with automatic cleanup.
    
    Args:
        example_name: Name of example (e.g., "08-local-agent-runtime")
        servers: List of server configs:
            [{"module": "...", "port_name": "...", "name": "..."}]
    
    Yields:
        Dict mapping server names to URLs
    
    Example:
        with run_mcp_servers_for_example("08", [
            {"module": "mcp_servers.filesystem.server:app", "port_name": "08-filesystem", "name": "filesystem"},
            {"module": "mcp_servers.git.server:app", "port_name": "08-git", "name": "git"}
        ]) as server_urls:
            filesystem_url = server_urls["filesystem"]
            git_url = server_urls["git"]
            # Use servers
            ...
        # All servers automatically stopped
    """
    server_urls = {}
    processes = []
    
    try:
        # Start all servers
        for server_config in servers:
            module = server_config["module"]
            port_name = server_config.get("port_name")
            name = server_config.get("name", module.split(".")[-2])
            
            port = PORT_MAPPING.get(port_name, find_free_port(8144))
            
            # Ensure port is free
            if not ensure_port_free(port, kill_if_in_use=True):
                raise RuntimeError(f"Port {port} is still in use for {name} server")
            
            # Start server
            cmd = [
                sys.executable, "-m", "uvicorn",
                module,
                "--host", "0.0.0.0",
                "--port", str(port)
            ]
            
            print(f"[MCP] Starting {name} server on port {port}...")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=Path(__file__).parent.parent.parent
            )
            processes.append((process, port, name))
            server_urls[name] = f"http://localhost:{port}/mcp"
        
        # Wait for all servers to be ready
        print("[MCP] Waiting for servers to be ready...")
        max_wait = 15
        for attempt in range(max_wait):
            all_ready = True
            for process, port, name in processes:
                if process.poll() is not None:
                    stdout, stderr = process.communicate()
                    raise RuntimeError(
                        f"Server {name} failed to start:\n"
                        f"STDOUT: {stdout.decode()}\n"
                        f"STDERR: {stderr.decode()}"
                    )
                
                try:
                    response = httpx.get(f"http://localhost:{port}/health", timeout=1)
                    if response.status_code != 200:
                        all_ready = False
                except Exception:
                    all_ready = False
            
            if all_ready:
                print(f"[MCP] All servers ready: {list(server_urls.keys())}")
                yield server_urls
                return
            
            time.sleep(1)
        
        raise RuntimeError(f"Servers did not become ready within {max_wait} seconds")
        
    finally:
        # Cleanup: stop all servers
        print("[MCP] Stopping all servers...")
        for process, port, name in processes:
            try:
                if sys.platform == 'win32':
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                else:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                
                # Ensure port is free
                time.sleep(0.5)
                if is_port_in_use(port):
                    kill_process_on_port(port)
                
                print(f"[MCP] {name} server stopped")
            except Exception as e:
                print(f"[WARN] Error stopping {name} server: {e}")


def get_port_for_example(example_name: str, server_name: str) -> int:
    """Get the assigned port for an example's server."""
    port_key = f"{example_name}-{server_name}"
    return PORT_MAPPING.get(port_key, find_free_port(8144))

