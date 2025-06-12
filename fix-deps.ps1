# Fix Dependencies Script
Write-Host "🔧 Fixing NFAC Backend Dependencies..." -ForegroundColor Cyan

# Navigate to 3lecture directory
if (Test-Path "3lecture") {
    cd 3lecture
} else {
    Write-Host "❌ 3lecture directory not found! Run this from project root." -ForegroundColor Red
    exit 1
}

Write-Host "`n📋 Available Fix Options:" -ForegroundColor Yellow
Write-Host "1. Use fixed requirements.txt (recommended)"
Write-Host "2. Use minimal requirements-minimal.txt (safest)"
Write-Host "3. Remove pydantic-ai temporarily"
Write-Host ""

$choice = Read-Host "Choose option (1-3)"

switch ($choice) {
    "1" {
        Write-Host "`n🔄 Using fixed requirements.txt..." -ForegroundColor Green
        # requirements.txt is already fixed
    }
    "2" {
        Write-Host "`n🔄 Switching to minimal requirements..." -ForegroundColor Green
        if (Test-Path "requirements-minimal.txt") {
            Copy-Item "requirements-minimal.txt" "requirements.txt" -Force
            Write-Host "✅ Switched to minimal requirements" -ForegroundColor Green
        } else {
            Write-Host "❌ requirements-minimal.txt not found!" -ForegroundColor Red
            exit 1
        }
    }
    "3" {
        Write-Host "`n🔄 Removing pydantic-ai temporarily..." -ForegroundColor Green
        (Get-Content "requirements.txt") | Where-Object { $_ -notmatch "pydantic-ai" } | Set-Content "requirements.txt"
        Write-Host "✅ Removed pydantic-ai from requirements" -ForegroundColor Green
    }
    default {
        Write-Host "❌ Invalid choice. Using fixed requirements.txt" -ForegroundColor Yellow
    }
}

Write-Host "`n🏗️ Rebuilding Docker containers..." -ForegroundColor Cyan

# Stop existing containers
Write-Host "🛑 Stopping containers..." -ForegroundColor Yellow
docker-compose down

# Clean build
Write-Host "🧹 Cleaning Docker cache..." -ForegroundColor Yellow
docker system prune -f

# Build with no cache
Write-Host "🔨 Building containers..." -ForegroundColor Yellow
docker-compose build --no-cache

# Start services
Write-Host "🚀 Starting services..." -ForegroundColor Yellow
docker-compose up -d

# Wait for startup
Write-Host "`n⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check status
Write-Host "`n📊 Checking service status..." -ForegroundColor Cyan
docker-compose ps

# Test health endpoints
Write-Host "`n🔍 Testing health endpoints..." -ForegroundColor Cyan

$endpoints = @(
    @{url="http://localhost:8000/health"; name="Main API"}
    @{url="http://localhost:8102/health"; name="A2A Chatbot"}
)

foreach ($endpoint in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri $endpoint.url -Method GET -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $($endpoint.name) is healthy" -ForegroundColor Green
        } else {
            Write-Host "⚠️ $($endpoint.name) returned status $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ $($endpoint.name) is not responding" -ForegroundColor Red
    }
}

Write-Host "`n🎉 Fix complete! Try starting the frontend:" -ForegroundColor Green
Write-Host "cd ../frontend" -ForegroundColor Gray
Write-Host "python server.py" -ForegroundColor Gray
Write-Host "`nThen open: http://localhost:3000" -ForegroundColor Cyan 