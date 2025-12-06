# Start Local Agent Runtime - All Services (PowerShell)

Write-Host "🚀 Starting Local Agent Runtime..." -ForegroundColor Cyan
Write-Host ""

# Check Ollama
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Ollama not found. Install from https://ollama.com" -ForegroundColor Red
    exit 1
}

# Check if model exists
$models = ollama list
if ($models -notmatch "llama3.2:11b") {
    Write-Host "📥 Pulling llama3.2:11b..." -ForegroundColor Yellow
    ollama pull llama3.2:11b
}

# Start MCP servers in background
Write-Host "🔌 Starting MCP servers..." -ForegroundColor Cyan

Start-Process python -ArgumentList "mcp_servers/filesystem/server.py" -WindowStyle Hidden
Start-Process python -ArgumentList "mcp_servers/git/server.py" -WindowStyle Hidden

Start-Sleep -Seconds 2

# Check servers
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/mcp/tools" -UseBasicParsing -ErrorAction Stop
    Write-Host "✅ Filesystem server running (port 8000)" -ForegroundColor Green
} catch {
    Write-Host "❌ Filesystem server failed to start" -ForegroundColor Red
    exit 1
}

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8001/mcp/tools" -UseBasicParsing -ErrorAction Stop
    Write-Host "✅ Git server running (port 8001)" -ForegroundColor Green
} catch {
    Write-Host "❌ Git server failed to start" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ All services started!" -ForegroundColor Green
Write-Host ""
Write-Host "Run agent:" -ForegroundColor Yellow
Write-Host "  python runtime/agent_runtime.py"
Write-Host ""
Write-Host "Or compile from Fabric:" -ForegroundColor Yellow
Write-Host "  python backend/compiler_bridge.py"

