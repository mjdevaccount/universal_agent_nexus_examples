"""
Cleanup script for leftover MCP server processes

December 2025 pattern: Kill only our test/example MCP servers, not Cursor's.

Usage:
    python tests/helpers/cleanup_mcp_servers.py
"""

import sys
import subprocess
from pathlib import Path

# Port mapping from mcp_server_runner
PORT_MAPPING = {
    "08-filesystem": 8144,
    "08-git": 8145,
    "test-filesystem": 8244,
    "test-git": 8245,
    "demo-filesystem": 8344,
    "demo-git": 8345,
}

ALL_MCP_PORTS = list(PORT_MAPPING.values())


def kill_process_on_port_windows(port: int) -> bool:
    """Kill process on port (Windows)."""
    try:
        # Find PID using netstat
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
                        # Get command line to check if it's our MCP server
                        cmd_result = subprocess.run(
                            ['wmic', 'process', 'where', f'ProcessId={pid}', 'get', 'CommandLine'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        cmdline = cmd_result.stdout
                        
                        # Only kill if it's our MCP server
                        if 'mcp_servers' in cmdline or ('uvicorn' in cmdline and 'server' in cmdline):
                            subprocess.run(
                                ['taskkill', '/F', '/PID', pid],
                                capture_output=True,
                                timeout=5
                            )
                            print(f"[CLEANUP] Killed MCP server process {pid} on port {port}")
                            return True
                    except Exception:
                        pass
    except Exception as e:
        print(f"[WARN] Could not check port {port}: {e}")
    
    return False


def kill_process_on_port_unix(port: int) -> bool:
    """Kill process on port (Unix)."""
    try:
        # Find PID using lsof
        result = subprocess.run(
            ['lsof', '-ti', f':{port}'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.stdout.strip():
            pid = result.stdout.strip()
            try:
                # Get command line
                with open(f'/proc/{pid}/cmdline', 'r') as f:
                    cmdline = f.read()
                
                # Only kill if it's our MCP server
                if 'mcp_servers' in cmdline or ('uvicorn' in cmdline and 'server' in cmdline):
                    import signal
                    os.kill(int(pid), signal.SIGTERM)
                    print(f"[CLEANUP] Killed MCP server process {pid} on port {port}")
                    return True
            except Exception:
                pass
    except Exception:
        pass
    
    return False


def cleanup_mcp_servers():
    """Clean up leftover MCP server processes."""
    print("=" * 60)
    print("MCP Server Cleanup")
    print("=" * 60)
    print(f"\nChecking ports: {ALL_MCP_PORTS}")
    
    killed_count = 0
    
    for port in ALL_MCP_PORTS:
        if sys.platform == 'win32':
            if kill_process_on_port_windows(port):
                killed_count += 1
        else:
            if kill_process_on_port_unix(port):
                killed_count += 1
    
    print(f"\n[CLEANUP] Killed {killed_count} MCP server process(es)")
    print("[OK] Cleanup complete")
    print("=" * 60)


if __name__ == "__main__":
    cleanup_mcp_servers()

