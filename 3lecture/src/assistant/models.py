from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class AgentRequest(BaseModel):
    """Base request model for agent communication"""
    query: str = Field(..., description="User query to process")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class LangchainAgentInput(AgentRequest):
    """Input model for LangChain agent"""
    additional_context: Optional[str] = Field(None, description="Additional context for processing")


class LangchainAgentOutput(BaseModel):
    """Output model from LangChain agent"""
    processed_query: str = Field(..., description="Processed and enhanced query")
    keywords: List[str] = Field(..., description="Extracted keywords")
    summary: str = Field(..., description="Query summary")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    agent_name: str = Field(default="langchain_agent")
    processing_time: float = Field(..., description="Processing time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PydanticAIAgentInput(BaseModel):
    """Input model for PydanticAI agent (receives LangChain output)"""
    langchain_output: LangchainAgentOutput
    additional_instructions: Optional[str] = Field(None, description="Additional processing instructions")


class SentimentAnalysis(BaseModel):
    """Sentiment analysis result"""
    polarity: float = Field(..., description="Sentiment polarity (-1 to 1)")
    subjectivity: float = Field(..., description="Subjectivity (0 to 1)")
    label: str = Field(..., description="Sentiment label (positive/negative/neutral)")


class PydanticAIAgentOutput(BaseModel):
    """Output model from PydanticAI agent"""
    enhanced_response: str = Field(..., description="Enhanced and enriched response")
    sentiment_analysis: SentimentAnalysis = Field(..., description="Sentiment analysis results")
    confidence_score: float = Field(..., description="Confidence score (0 to 1)")
    enriched_keywords: List[str] = Field(..., description="Enriched keywords from OpenAI")
    agent_name: str = Field(default="pydantic_ai_agent")
    processing_time: float = Field(..., description="Processing time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FinalResponse(BaseModel):
    """Final combined response from both agents"""
    original_query: str = Field(..., description="Original user query")
    langchain_result: LangchainAgentOutput = Field(..., description="LangChain agent results")
    pydantic_ai_result: PydanticAIAgentOutput = Field(..., description="PydanticAI agent results")
    combined_response: str = Field(..., description="Combined final response")
    total_processing_time: float = Field(..., description="Total processing time")
    success: bool = Field(default=True, description="Processing success status")
    error_message: Optional[str] = Field(None, description="Error message if any")


class ChatMessage(BaseModel):
    """Chat message model for storing conversation history"""
    id: Optional[int] = None
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    query: str = Field(..., description="User query")
    response: str = Field(..., description="Bot response")
    langchain_data: Optional[Dict[str, Any]] = Field(None, description="LangChain processing data")
    pydantic_ai_data: Optional[Dict[str, Any]] = Field(None, description="PydanticAI processing data")
    processing_time: float = Field(..., description="Total processing time")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True 