#!/bin/bash
# Start Local Agent Runtime - All Services

echo "🚀 Starting Local Agent Runtime..."
echo ""

# Check Ollama
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not found. Install from https://ollama.com"
    exit 1
fi

# Check if model exists
if ! ollama list | grep -q "llama3.2:11b"; then
    echo "📥 Pulling llama3.2:11b..."
    ollama pull llama3.2:11b
fi

# Start MCP servers in background
echo "🔌 Starting MCP servers..."
python mcp_servers/filesystem/server.py &
FILESYSTEM_PID=$!

python mcp_servers/git/server.py &
GIT_PID=$!

sleep 2

# Check servers are running
if curl -s http://localhost:8000/mcp/tools > /dev/null; then
    echo "✅ Filesystem server running (port 8000)"
else
    echo "❌ Filesystem server failed to start"
    exit 1
fi

if curl -s http://localhost:8001/mcp/tools > /dev/null; then
    echo "✅ Git server running (port 8001)"
else
    echo "❌ Git server failed to start"
    exit 1
fi

echo ""
echo "✅ All services started!"
echo ""
echo "Run agent:"
echo "  python runtime/agent_runtime.py"
echo ""
echo "Or compile from Fabric:"
echo "  python backend/compiler_bridge.py"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "kill $FILESYSTEM_PID $GIT_PID; exit" INT TERM
wait

