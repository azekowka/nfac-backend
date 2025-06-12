# A2A Chatbot Frontend Launcher (PowerShell)
# Automatically starts the frontend server with backend health check

Write-Host "`n🤖 A2A Chatbot Frontend Launcher" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found! Please install Python 3.7+" -ForegroundColor Red
    Write-Host "💡 Download from: https://python.org/downloads" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check backend connection
Write-Host "`n🔍 Checking A2A Backend connection..." -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8102/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ A2A Backend is running (Port 8102)" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  A2A Backend not detected on port 8102" -ForegroundColor Yellow
    Write-Host "💡 Make sure to start the backend first:" -ForegroundColor Yellow
    Write-Host "   cd 3lecture" -ForegroundColor Gray
    Write-Host "   docker-compose up -d" -ForegroundColor Gray
    Write-Host "`n🚀 Starting frontend anyway..." -ForegroundColor Cyan
}

# Start frontend server
Write-Host "`n🌐 Starting frontend server..." -ForegroundColor Cyan

try {
    # Check if port 3000 is available
    $portCheck = Test-NetConnection -ComputerName localhost -Port 3000 -WarningAction SilentlyContinue
    if ($portCheck.TcpTestSucceeded) {
        Write-Host "⚠️  Port 3000 is already in use, trying port 3001..." -ForegroundColor Yellow
        python server.py --port 3001
    } else {
        python server.py
    }
} catch {
    Write-Host "❌ Failed to start server: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
} 