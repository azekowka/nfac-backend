# A2A Multi-Agent Chatbot System

This is an implementation of an **Agent-to-Agent (A2A)** multi-agent chatbot system based on the repository [azekowka/a2a](https://github.com/azekowka/a2a). The system uses two specialized AI agents that communicate with each other to provide enhanced responses.

## 🏗️ Architecture

The A2A system consists of three main components:

1. **LangChain Agent** (Port 8100) - Uses Google Gemini for query processing and enhancement
2. **PydanticAI Agent** (Port 8101) - Uses OpenAI GPT and TextBlob for sentiment analysis and response enhancement
3. **Main Chatbot API** (Port 8102) - Orchestrates communication between agents and manages chat history

## 🔄 How It Works

```
User Query → LangChain Agent → PydanticAI Agent → Combined Response
```

1. **Step 1**: User sends a query to the main chatbot API
2. **Step 2**: LangChain Agent processes the query using Google Gemini:
   - Extracts keywords
   - Generates summary
   - Enhances the query with context
3. **Step 3**: PydanticAI Agent receives LangChain output and:
   - Analyzes sentiment using TextBlob
   - Enriches keywords using OpenAI
   - Generates final enhanced response
4. **Step 4**: Main API combines both results and saves to database

## 📁 Project Structure

```
3lecture/src/assistant/
├── __init__.py              # Package initialization
├── models.py                # Pydantic models for A2A communication
├── langchain_agent.py       # LangChain agent with Google Gemini
├── pydantic_ai_agent.py     # PydanticAI agent with OpenAI & TextBlob
├── a2a_client.py           # Client for agent-to-agent communication
├── chat_database.py        # Database models and operations
└── chatbot_api.py          # Main FastAPI application
```

## 🚀 Quick Start

### 1. Set up API Keys

You need API keys for:
- **Google Gemini**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **OpenAI**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)

Create a `.env` file in the `3lecture/` directory:

```env
# A2A System API Keys
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration (already set)
DATABASE_URL=postgresql+asyncpg://username:password@db:5432/postgresdb
SYNC_DATABASE_URL=postgresql://username:password@db:5432/postgresdb
SECRET_KEY=your_super_secret_key_here_change_me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 2. Run with Docker Compose

```bash
cd 3lecture
docker compose up --build
```

This will start:
- **PostgreSQL** (port 5432)
- **Redis** (port 6379)
- **Original FastAPI app** (port 8000)
- **LangChain Agent** (port 8100)
- **PydanticAI Agent** (port 8101)
- **A2A Chatbot API** (port 8102)
- **Celery Worker & Beat**

### 3. Test the System

#### Health Check
```bash
curl http://localhost:8102/health
```

#### Test Agents
```bash
curl -X POST http://localhost:8102/test-agents
```

#### Chat with the Bot
```bash
curl -X POST http://localhost:8102/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is artificial intelligence?",
    "user_id": "test_user",
    "session_id": "test_session"
  }'
```

## 🔌 API Endpoints

### Main Chatbot API (Port 8102)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Send message to chatbot |
| `/health` | GET | Check system health |
| `/test-agents` | POST | Test both agents |
| `/history/{user_id}` | GET | Get chat history |
| `/stats/{user_id}` | GET | Get user statistics |
| `/sessions/{user_id}` | GET | Get user sessions |

### Individual Agent APIs

**LangChain Agent (Port 8100):**
- `GET /health` - Health check
- `POST /process` - Process query with Gemini

**PydanticAI Agent (Port 8101):**
- `GET /health` - Health check  
- `POST /process` - Process LangChain output

## 📊 Features

### Multi-Agent Processing
- **Keyword Extraction**: Automatic keyword extraction from user queries
- **Query Enhancement**: Context-aware query processing using Google Gemini
- **Sentiment Analysis**: Real-time sentiment analysis using TextBlob
- **Response Enhancement**: Intelligent response generation using OpenAI

### Database Integration
- **Chat History**: Persistent storage of all conversations
- **User Statistics**: Track success rates, processing times, sentiment trends
- **Session Management**: Organize conversations by sessions

### Monitoring & Health
- **Health Checks**: Monitor all agent services
- **Processing Metrics**: Track response times and success rates
- **Error Handling**: Graceful fallbacks when agents are unavailable

## 🛠️ Configuration

### Agent URLs (for local development)
```python
# In a2a_client.py
a2a_client = A2AClient(
    langchain_url="http://localhost:8100",
    pydantic_ai_url="http://localhost:8101"
)
```

### Docker Service URLs (production)
```python
# For Docker Compose
a2a_client = A2AClient(
    langchain_url="http://langchain-agent:8000",
    pydantic_ai_url="http://pydantic-ai-agent:8001"
)
```

## 📈 Example Response

```json
{
  "message": "Artificial Intelligence (AI) is a branch of computer science focused on creating intelligent machines that can perform tasks typically requiring human intelligence...",
  "user_id": "test_user",
  "session_id": "test_session",
  "processing_time": 2.34,
  "success": true,
  "metadata": {
    "langchain_processing_time": 1.12,
    "pydantic_ai_processing_time": 0.89,
    "keywords": ["artificial", "intelligence", "machine", "learning", "computer"],
    "sentiment": "neutral",
    "confidence_score": 0.85
  }
}
```

## 🔧 Development

### Running Individual Components

**LangChain Agent:**
```bash
cd 3lecture/src
python -m assistant.langchain_agent
```

**PydanticAI Agent:**
```bash
cd 3lecture/src  
python -m assistant.pydantic_ai_agent
```

**Main Chatbot API:**
```bash
cd 3lecture/src
python -m assistant.chatbot_api
```

### Testing A2A Communication
```bash
cd 3lecture/src
python -m assistant.a2a_client
```

## 🐛 Troubleshooting

### Common Issues

1. **Missing API Keys**: Ensure GEMINI_API_KEY and OPENAI_API_KEY are set
2. **Agent Connection Errors**: Check that both agents are running and accessible
3. **Database Errors**: Ensure PostgreSQL is running and accessible
4. **Port Conflicts**: Make sure ports 8100, 8101, 8102 are available

### Logs
Check Docker logs for each service:
```bash
docker compose logs langchain-agent
docker compose logs pydantic-ai-agent  
docker compose logs a2a-chatbot
```

## 🎯 Next Steps

- [ ] Add more specialized agents (e.g., for different domains)
- [ ] Implement agent load balancing
- [ ] Add WebSocket support for real-time chat
- [ ] Create a web UI for the chatbot
- [ ] Add more sophisticated error handling and retries
- [ ] Implement agent performance monitoring

## 📝 Credits

Based on the A2A architecture from: https://github.com/azekowka/a2a 