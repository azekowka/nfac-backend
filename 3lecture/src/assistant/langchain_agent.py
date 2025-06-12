import os
import time
import logging
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from assistant.models import LangchainAgentInput, LangchainAgentOutput
import google.generativeai as genai
from langchain.schema import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import uvicorn
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="LangChain Agent", description="LangChain Agent with Google Gemini", version="1.0.0")

# Configure Google Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY environment variable is not set")
    raise ValueError("GEMINI_API_KEY environment variable is required")

genai.configure(api_key=GEMINI_API_KEY)

# Initialize LangChain with Gemini
llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    google_api_key=GEMINI_API_KEY,
    temperature=0.7,
    convert_system_message_to_human=True
)


def extract_keywords(text: str) -> List[str]:
    """Extract keywords from text using simple regex and filtering"""
    # Remove common stop words and extract meaningful words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
        'what', 'how', 'when', 'where', 'why', 'who', 'which', 'that', 'this', 'these', 'those',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
        'will', 'would', 'could', 'should', 'may', 'might', 'can', 'cannot', 'shall'
    }
    
    # Extract words (alphanumeric sequences)
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Filter out stop words and return unique keywords
    keywords = list(set([word for word in words if word not in stop_words]))
    
    return keywords[:10]  # Return top 10 keywords


def generate_summary(text: str) -> str:
    """Generate a summary of the input text using Gemini"""
    try:
        prompt = f"""
        Please provide a concise summary of the following text in 2-3 sentences:
        
        {text}
        
        Focus on the main topics, intent, and key information.
        """
        
        message = HumanMessage(content=prompt)
        response = llm.invoke([message])
        
        return response.content.strip()
    
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return f"Summary: {text[:100]}..." if len(text) > 100 else text


def process_query_with_gemini(query: str, context: str = None) -> str:
    """Process and enhance query using Google Gemini"""
    try:
        context_part = f"\nAdditional context: {context}" if context else ""
        
        prompt = f"""
        You are an intelligent assistant that processes and enhances user queries.
        
        User query: {query}{context_part}
        
        Please:
        1. Understand the user's intent
        2. Enhance the query with relevant context and details
        3. Provide a structured and comprehensive response
        4. Include any relevant background information that would be helpful
        
        Provide a clear, well-structured response that addresses the user's needs.
        """
        
        message = HumanMessage(content=prompt)
        response = llm.invoke([message])
        
        return response.content.strip()
    
    except Exception as e:
        logger.error(f"Error processing query with Gemini: {e}")
        return f"Enhanced query: {query}"


@app.post("/process", response_model=LangchainAgentOutput)
async def process_query(input_data: LangchainAgentInput):
    """Process query using LangChain with Google Gemini"""
    start_time = time.time()
    
    try:
        logger.info(f"Processing query: {input_data.query}")
        
        # Extract keywords
        keywords = extract_keywords(input_data.query)
        
        # Generate summary
        summary = generate_summary(input_data.query)
        
        # Process query with Gemini
        processed_query = process_query_with_gemini(
            input_data.query, 
            input_data.additional_context
        )
        
        # Prepare context
        context = {
            "original_query": input_data.query,
            "user_id": input_data.user_id,
            "session_id": input_data.session_id,
            "has_context": bool(input_data.additional_context),
            "keyword_count": len(keywords)
        }
        
        processing_time = time.time() - start_time
        
        result = LangchainAgentOutput(
            processed_query=processed_query,
            keywords=keywords,
            summary=summary,
            context=context,
            processing_time=processing_time
        )
        
        logger.info(f"Successfully processed query in {processing_time:.2f}s")
        return result
    
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent": "langchain_agent",
        "model": "gemini-pro",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "LangChain Agent with Google Gemini",
        "endpoints": {
            "process": "/process",
            "health": "/health",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    logger.info("Starting LangChain Agent on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000) 