import uuid
import time
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from assistant.a2a_client import A2AClient
from assistant.chat_database import chat_service
from assistant.models import FinalResponse
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="A2A Chatbot API",
    description="Multi-Agent Chatbot with LangChain and PydanticAI",
    version="1.0.0"
)

# Initialize A2A client
a2a_client = A2AClient()

# Request/Response models
class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., description="User message", min_length=1, max_length=2000)
    user_id: Optional[str] = Field(None, description="User ID (will be auto-generated if not provided)")
    session_id: Optional[str] = Field(None, description="Session ID (will be auto-generated if not provided)")
    save_to_history: bool = Field(True, description="Whether to save this conversation to history")


class ChatResponse(BaseModel):
    """Chat response model"""
    message: str = Field(..., description="Bot response message")
    user_id: str = Field(..., description="User ID")
    session_id: str = Field(..., description="Session ID")
    chat_id: Optional[int] = Field(None, description="Database chat ID if saved")
    processing_time: float = Field(..., description="Total processing time in seconds")
    success: bool = Field(..., description="Whether processing was successful")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    agents_status: Dict[str, Any]
    timestamp: str


class StatsResponse(BaseModel):
    """User statistics response"""
    user_id: str
    total_messages: int
    successful_messages: int
    success_rate: float
    average_processing_time: float
    average_confidence_score: float
    sentiment_distribution: Dict[str, int]


class SessionResponse(BaseModel):
    """Session information response"""
    session_id: str
    last_message: str
    message_count: int


async def save_chat_to_database(
    user_id: str,
    session_id: str,
    query: str,
    final_response: FinalResponse
) -> Optional[int]:
    """Save chat conversation to database"""
    try:
        if final_response.success:
            # Prepare LangChain data
            langchain_data = {
                "processing_time": final_response.langchain_result.processing_time,
                "keywords": final_response.langchain_result.keywords,
                "summary": final_response.langchain_result.summary,
                "context": final_response.langchain_result.context
            }
            
            # Prepare PydanticAI data
            pydantic_ai_data = {
                "processing_time": final_response.pydantic_ai_result.processing_time,
                "sentiment_analysis": {
                    "polarity": final_response.pydantic_ai_result.sentiment_analysis.polarity,
                    "subjectivity": final_response.pydantic_ai_result.sentiment_analysis.subjectivity,
                    "label": final_response.pydantic_ai_result.sentiment_analysis.label
                },
                "confidence_score": final_response.pydantic_ai_result.confidence_score,
                "enriched_keywords": final_response.pydantic_ai_result.enriched_keywords
            }
        else:
            langchain_data = None
            pydantic_ai_data = None
        
        # Save to database
        chat_id = chat_service.save_chat_message(
            user_id=user_id,
            session_id=session_id,
            query=query,
            response=final_response.combined_response,
            langchain_data=langchain_data,
            pydantic_ai_data=pydantic_ai_data,
            total_processing_time=final_response.total_processing_time,
            success=final_response.success,
            error_message=final_response.error_message
        )
        
        logger.info(f"Saved chat to database with ID: {chat_id}")
        return chat_id
        
    except Exception as e:
        logger.error(f"Error saving chat to database: {e}")
        return None


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    background_tasks: BackgroundTasks
):
    """Main chat endpoint for A2A communication"""
    start_time = time.time()
    
    try:
        # Generate IDs if not provided
        user_id = request.user_id or f"user_{uuid.uuid4().hex[:8]}"
        session_id = request.session_id or f"session_{uuid.uuid4().hex[:8]}"
        
        logger.info(f"Processing chat request from user {user_id}, session {session_id}")
        
        # Process query through A2A system
        final_response = await a2a_client.process_query(
            query=request.message,
            user_id=user_id,
            session_id=session_id
        )
        
        # Save to database in background if requested
        chat_id = None
        if request.save_to_history and final_response.success:
            background_tasks.add_task(
                save_chat_to_database,
                user_id,
                session_id,
                request.message,
                final_response
            )
            # We can't get the chat_id here since it's in background, but that's okay
        
        # Prepare metadata
        metadata = {}
        if final_response.success:
            metadata = {
                "langchain_processing_time": final_response.langchain_result.processing_time,
                "pydantic_ai_processing_time": final_response.pydantic_ai_result.processing_time,
                "keywords": final_response.langchain_result.keywords[:5],  # Top 5 keywords
                "sentiment": final_response.pydantic_ai_result.sentiment_analysis.label,
                "confidence_score": final_response.pydantic_ai_result.confidence_score
            }
        
        response = ChatResponse(
            message=final_response.combined_response,
            user_id=user_id,
            session_id=session_id,
            chat_id=chat_id,
            processing_time=final_response.total_processing_time,
            success=final_response.success,
            metadata=metadata
        )
        
        logger.info(f"Chat processed successfully in {final_response.total_processing_time:.2f}s")
        return response
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error in chat endpoint: {e}")
        
        return ChatResponse(
            message="I apologize, but I encountered an error while processing your request. Please try again.",
            user_id=request.user_id or "unknown",
            session_id=request.session_id or "unknown",
            processing_time=processing_time,
            success=False,
            metadata={"error": str(e)}
        )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        agents_status = await a2a_client.check_agents_health()
        
        # Determine overall health
        all_healthy = all(
            status.get("status") == "healthy" 
            for status in agents_status.values()
        )
        
        overall_status = "healthy" if all_healthy else "degraded"
        
        return HealthResponse(
            status=overall_status,
            agents_status=agents_status,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return HealthResponse(
            status="error",
            agents_status={"error": str(e)},
            timestamp=datetime.utcnow().isoformat()
        )


@app.get("/history/{user_id}")
async def get_chat_history(
    user_id: str,
    session_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get chat history for a user"""
    try:
        history = chat_service.get_chat_history(
            user_id=user_id,
            session_id=session_id,
            limit=limit,
            offset=offset
        )
        
        return {
            "user_id": user_id,
            "session_id": session_id,
            "total_messages": len(history),
            "history": history
        }
        
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving chat history: {str(e)}")


@app.get("/stats/{user_id}", response_model=StatsResponse)
async def get_user_stats(user_id: str):
    """Get statistics for a user"""
    try:
        stats = chat_service.get_user_stats(user_id)
        return StatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving user stats: {str(e)}")


@app.get("/sessions/{user_id}")
async def get_user_sessions(user_id: str, limit: int = 10) -> List[SessionResponse]:
    """Get recent sessions for a user"""
    try:
        sessions = chat_service.get_recent_sessions(user_id, limit)
        return [SessionResponse(**session) for session in sessions]
        
    except Exception as e:
        logger.error(f"Error getting user sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving user sessions: {str(e)}")


@app.post("/test-agents")
async def test_agents():
    """Test endpoint to verify both agents are working"""
    test_query = "Hello, this is a test message to verify the A2A system is working correctly."
    
    try:
        result = await a2a_client.process_query(
            query=test_query,
            user_id="test_user",
            session_id="test_session"
        )
        
        return {
            "test_query": test_query,
            "success": result.success,
            "processing_time": result.total_processing_time,
            "response": result.combined_response,
            "langchain_keywords": result.langchain_result.keywords if result.success else None,
            "sentiment": result.pydantic_ai_result.sentiment_analysis.label if result.success else None,
            "confidence": result.pydantic_ai_result.confidence_score if result.success else None
        }
        
    except Exception as e:
        logger.error(f"Error testing agents: {e}")
        raise HTTPException(status_code=500, detail=f"Agent test failed: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "A2A Multi-Agent Chatbot API",
        "version": "1.0.0",
        "description": "Advanced chatbot using LangChain and PydanticAI agents",
        "endpoints": {
            "chat": "/chat",
            "health": "/health",
            "history": "/history/{user_id}",
            "stats": "/stats/{user_id}",
            "sessions": "/sessions/{user_id}",
            "test": "/test-agents",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    logger.info("Starting A2A Chatbot API on port 8002...")
    uvicorn.run(app, host="0.0.0.0", port=8002) 