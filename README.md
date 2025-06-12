# Homework

- [x] Connect to redis (Docker Compose)
- [x] Connect to celery (Docker Compose)
- [ ] Deploy your project in Droplet(with using docker)
- [ ] Add a task for everyday fetching data from the website and save it to the database
- [x] Add directory Assitant and create an assisntant(gemini,openai,claude etc.)
- [x] Use a2a to create a chatbot
- [ ] Connect chatbot to your Frontend

## Task list:

- [x] Connect to redis (Docker Compose)
- [x] Connect to celery (Docker Compose)
- [x] **NEW**: Implement A2A (Agent-to-Agent) Multi-Agent Chatbot System ✨
- [ ] Add a task for everyday fetching data from the website and save it to the database

## 🤖 A2A Multi-Agent Chatbot System

A sophisticated **Agent-to-Agent (A2A)** chatbot system has been implemented based on the [azekowka/a2a](https://github.com/azekowka/a2a) repository. This system uses multiple AI agents working together to provide enhanced responses.

### 🏗️ Architecture
- **LangChain Agent** (Port 8100) - Google Gemini for query processing
- **PydanticAI Agent** (Port 8101) - OpenAI + TextBlob for sentiment analysis  
- **Main Chatbot API** (Port 8102) - Orchestrates agents and manages chat history

### 🚀 Quick Start

1. **Set up API Keys** - Create `.env` file with:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

2. **Run the System**:
   ```bash
   cd 3lecture
   docker compose up --build
   ```

3. **Test the Chatbot**:
   ```bash
   # Health check
   curl http://localhost:8102/health
   
   # Chat with the bot
   curl -X POST http://localhost:8102/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello, how are you?"}'
   ```

### 📚 Documentation
See [`A2A_README.md`](3lecture/A2A_README.md) for complete documentation.

---

## Environment variables

The application now boots with sensible defaults when run via Docker Compose, so a `.env` file is **optional** for local development.

If you want to override any value (for example, database credentials or JWT secret key) simply create a `.env` file in `3lecture/` with variables such as:

```env
# 3lecture/.env
DATABASE_URL=postgresql+asyncpg://username:password@db:5432/postgresdb
SYNC_DATABASE_URL=postgresql://username:password@db:5432/postgresdb
SECRET_KEY=your_long_random_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# A2A System API Keys (REQUIRED for A2A functionality)
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

Docker Compose will automatically use these values if the file exists.

## Services and Ports

When running with `docker compose up --build`:

| Service | Port | Description |
|---------|------|-------------|
| **PostgreSQL** | 5432 | Database |
| **Redis** | 6379 | Cache & message broker |
| **Original FastAPI** | 8000 | Main application |
| **LangChain Agent** | 8100 | Google Gemini agent |
| **PydanticAI Agent** | 8101 | OpenAI + TextBlob agent |
| **A2A Chatbot API** | 8102 | Multi-agent chatbot |
| **Celery Worker** | - | Background task worker |
| **Celery Beat** | - | Task scheduler |