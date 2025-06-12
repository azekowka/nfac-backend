# 🚀 NFAC Backend Project - Complete Launch Guide

This guide will help you launch the complete NFAC Backend system including the A2A chatbot backend, data fetcher, and frontend interface.

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   A2A Chatbot   │    │ Data Fetcher    │
│   Port: 3000    │────│   Port: 8102    │    │   Port: 8000    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │     Infrastructure        │
                    │                           │
                    │  📊 PostgreSQL (5432)     │
                    │  🔴 Redis (6379)          │
                    │  ⚙️  Celery Workers        │
                    │  ⏰ Celery Beat            │
                    └───────────────────────────┘
```

## 📋 Prerequisites

### Required Software
- **Docker Desktop** (for Windows/Mac) or **Docker Engine** (for Linux)
- **Python 3.8+** (for frontend server)
- **PowerShell** (Windows) or **Bash** (Linux/Mac)

### API Keys (Required)
Create a `.env` file in the `3lecture/` directory:
```bash
# Copy and fill these values
GEMINI_API_KEY=your_google_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Database (leave as default for Docker)
DB_USER=username
DB_PASSWORD=password
DB_NAME=postgresdb
DB_HOST=db
DB_PORT=5432

# Redis (leave as default for Docker)
REDIS_URL=redis://redis:6379/0
```

### Get API Keys
1. **Google Gemini API**: https://makersuite.google.com/app/apikey
2. **OpenAI API**: https://platform.openai.com/api-keys

## 🚀 Quick Start (Recommended)

### Step 1: Start Backend Services
```powershell
# Windows PowerShell
cd 3lecture
docker-compose up -d

# Wait for services to initialize (2-3 minutes)
docker-compose logs -f
```

```bash
# Linux/Mac
cd 3lecture
docker-compose up -d

# Wait for services to initialize (2-3 minutes)
docker-compose logs -f
```

### Step 2: Start Frontend
```powershell
# Windows - Option 1 (Easiest)
cd frontend
./start.ps1

# Windows - Option 2 (Manual)
cd frontend
python server.py
```

```bash
# Linux/Mac
cd frontend
python3 server.py
```

### Step 3: Open Browser
Open your browser and navigate to:
- **Frontend**: http://localhost:3000
- **Data Fetcher API**: http://localhost:8000/docs
- **A2A Chatbot**: http://localhost:8102/docs

## 🔧 Detailed Setup

### Backend Services Overview

| Service | Port | Description | Health Check |
|---------|------|-------------|--------------|
| **Main API** | 8000 | FastAPI + Data Fetcher | http://localhost:8000/health |
| **LangChain Agent** | 8100 | Google Gemini Agent | http://localhost:8100/health |
| **PydanticAI Agent** | 8101 | OpenAI + TextBlob Agent | http://localhost:8101/health |
| **A2A Chatbot** | 8102 | Main Chat Orchestrator | http://localhost:8102/health |
| **PostgreSQL** | 5432 | Database | `docker-compose exec db pg_isready` |
| **Redis** | 6379 | Cache & Queue | `docker-compose exec redis redis-cli ping` |

### Step-by-Step Backend Launch

1. **Environment Setup**
   ```bash
   cd 3lecture
   
   # Create .env file with your API keys
   # See prerequisites section above
   ```

2. **Start Infrastructure**
   ```bash
   # Start database and redis first
   docker-compose up -d db redis
   
   # Wait 30 seconds for initialization
   sleep 30
   ```

3. **Start Application Services**
   ```bash
   # Start all services
   docker-compose up -d
   
   # Check status
   docker-compose ps
   ```

4. **Verify Services**
   ```bash
   # Check health endpoints
   curl http://localhost:8000/health      # Main API
   curl http://localhost:8100/health      # LangChain Agent
   curl http://localhost:8101/health      # PydanticAI Agent
   curl http://localhost:8102/health      # A2A Chatbot
   ```

### Frontend Launch Options

#### Option 1: PowerShell Script (Windows - Easiest)
```powershell
cd frontend
./start.ps1
```

#### Option 2: Python Server (Cross-platform)
```bash
cd frontend
python server.py

# Custom port
python server.py --port 3001
```

#### Option 3: Direct Browser (No server)
```bash
# Open directly in browser (may have CORS issues)
open frontend/index.html
```

#### Option 4: Node.js Live Server
```bash
# Install live-server globally
npm install -g live-server

cd frontend
live-server --port=3000
```

## 🧪 Testing the System

### 1. Test Data Fetcher
```bash
# Manual news fetch
curl -X POST "http://localhost:8000/data-fetcher/fetch/manual"

# Check fetched news
curl "http://localhost:8000/data-fetcher/news?limit=5"

# View statistics
curl "http://localhost:8000/data-fetcher/stats"
```

### 2. Test A2A Chatbot API
```bash
# Send a test message
curl -X POST "http://localhost:8102/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you today?"}'
```

### 3. Test Frontend
1. Open http://localhost:3000
2. Type a message in the chat interface
3. Verify AI response with sentiment analysis
4. Check connection status in header
5. Try exporting chat history

## 🔍 Monitoring & Logs

### View Service Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f celery
docker-compose logs -f a2a-chatbot
```

### Check Celery Tasks
```bash
# Active tasks
docker-compose exec celery celery -A celery_app.celery_app inspect active

# Scheduled tasks
docker-compose exec celery celery -A celery_app.celery_app inspect scheduled

# Worker status
docker-compose exec celery celery -A celery_app.celery_app status
```

### Database Access
```bash
# Connect to PostgreSQL
docker-compose exec db psql -U username -d postgresdb

# Check tables
\dt

# View fetched news
SELECT COUNT(*) FROM fetched_news;
```

### Redis Monitoring
```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Check queue status
LLEN celery
KEYS *
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Services Won't Start
```bash
# Check Docker is running
docker --version
docker-compose --version

# Check port conflicts
netstat -tulpn | grep :8000
netstat -tulpn | grep :8102

# Reset containers
docker-compose down
docker-compose up -d
```

#### 2. API Key Errors
```bash
# Verify .env file exists
cat 3lecture/.env

# Check environment variables in container
docker-compose exec web env | grep API
```

#### 3. Database Connection Issues
```bash
# Check database status
docker-compose exec db pg_isready

# View database logs
docker-compose logs db

# Reset database
docker-compose down -v
docker-compose up -d
```

#### 4. Frontend Connection Issues
- Ensure backend is running: http://localhost:8102/health
- Check browser console for errors
- Verify CORS is enabled (use Python server, not file://)
- Try different port: `python server.py --port 3001`

#### 5. Celery Task Issues
```bash
# Restart Celery workers
docker-compose restart celery

# Check beat scheduler
docker-compose logs celery-beat

# Manual task execution
docker-compose exec web python -c "
from data_fetcher.tasks import daily_news_fetch_task
daily_news_fetch_task.delay()
"
```

## 📊 Performance Tips

### Resource Requirements
- **RAM**: 4GB minimum, 8GB recommended
- **CPU**: 2 cores minimum, 4 cores recommended
- **Disk**: 10GB free space

### Optimization
```bash
# Increase worker count
# Edit docker-compose.yml:
# command: celery -A celery_app.celery_app worker --loglevel=info --concurrency=4

# Monitor resource usage
docker stats

# Clean up old data
curl -X POST "http://localhost:8000/data-fetcher/cleanup"
```

## 🛑 Stopping the System

### Graceful Shutdown
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (CAUTION: deletes data)
docker-compose down -v

# Stop frontend
Ctrl+C in terminal running Python server
```

### Clean Reset
```bash
# Complete cleanup
docker-compose down -v --rmi all
docker system prune -f

# Restart fresh
docker-compose up -d
```

## 📱 Usage Examples

### Chat with A2A System
1. Open http://localhost:3000
2. Type: "Analyze the sentiment of this text: I love working with AI!"
3. Observe sentiment analysis tags in response
4. Try: "What are the latest news headlines?"
5. Export chat history using the export button

### API Integration
```javascript
// Example frontend integration
const response = await fetch('http://localhost:8102/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        message: "Hello AI!",
        session_id: "unique_session_id"
    })
});

const data = await response.json();
console.log(data.response, data.analysis);
```

## 🎯 Next Steps

After successful launch:
1. **Customize news sources** in `data_fetcher/news_fetcher.py`
2. **Add authentication** to frontend
3. **Configure HTTPS** for production
4. **Set up monitoring** with Prometheus/Grafana
5. **Deploy to cloud** (DigitalOcean, AWS, etc.)

## 🆘 Support

If you encounter issues:
1. Check this troubleshooting guide
2. Review service logs: `docker-compose logs`
3. Verify API keys are correctly set
4. Ensure all ports are available
5. Try a complete reset with `docker-compose down -v`

---

**🎉 Congratulations! Your A2A Chatbot system is now running!**

**Frontend**: http://localhost:3000  
**Backend API**: http://localhost:8000/docs  
**A2A Chatbot**: http://localhost:8102/docs 