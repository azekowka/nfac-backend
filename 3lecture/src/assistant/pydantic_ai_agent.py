import os
import time
import logging
from typing import List
from fastapi import FastAPI, HTTPException
from assistant.models import (
    PydanticAIAgentInput, 
    PydanticAIAgentOutput, 
    SentimentAnalysis
)
from textblob import TextBlob
import openai
from openai import OpenAI
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="PydanticAI Agent", description="PydanticAI Agent with OpenAI and TextBlob", version="1.0.0")

# Configure OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY environment variable is not set")
    raise ValueError("OPENAI_API_KEY environment variable is required")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


def analyze_sentiment(text: str) -> SentimentAnalysis:
    """Analyze sentiment using TextBlob"""
    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Determine sentiment label
        if polarity > 0.1:
            label = "positive"
        elif polarity < -0.1:
            label = "negative"
        else:
            label = "neutral"
        
        return SentimentAnalysis(
            polarity=polarity,
            subjectivity=subjectivity,
            label=label
        )
    
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        # Return neutral sentiment as fallback
        return SentimentAnalysis(
            polarity=0.0,
            subjectivity=0.0,
            label="neutral"
        )


def enrich_keywords_with_openai(keywords: List[str], processed_query: str) -> List[str]:
    """Enrich keywords using OpenAI"""
    try:
        prompt = f"""
        Given the following keywords and processed query, suggest 5-10 additional related keywords 
        that would be relevant and useful for understanding the topic better.
        
        Original keywords: {', '.join(keywords)}
        Processed query: {processed_query}
        
        Return only the new keywords as a comma-separated list, without explanations.
        Focus on synonyms, related concepts, and contextually relevant terms.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that suggests relevant keywords."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.3
        )
        
        enriched_text = response.choices[0].message.content.strip()
        
        # Parse the response and extract keywords
        new_keywords = [kw.strip() for kw in enriched_text.split(',') if kw.strip()]
        
        # Combine original and new keywords, remove duplicates
        all_keywords = list(set(keywords + new_keywords))
        
        return all_keywords[:15]  # Return top 15 keywords
    
    except Exception as e:
        logger.error(f"Error enriching keywords with OpenAI: {e}")
        return keywords  # Return original keywords as fallback


def enhance_response_with_openai(langchain_output: dict, sentiment: SentimentAnalysis) -> str:
    """Enhance response using OpenAI based on LangChain output and sentiment"""
    try:
        sentiment_context = f"The sentiment is {sentiment.label} (polarity: {sentiment.polarity:.2f})"
        
        prompt = f"""
        You are an AI assistant that creates final, comprehensive responses for users.
        
        You have received the following processed information:
        - Original processed query: {langchain_output.get('processed_query', '')}
        - Keywords: {', '.join(langchain_output.get('keywords', []))}
        - Summary: {langchain_output.get('summary', '')}
        - Sentiment analysis: {sentiment_context}
        
        Based on this information, create a helpful, engaging, and comprehensive final response 
        that addresses the user's needs. The response should:
        1. Be informative and well-structured
        2. Take into account the sentiment analysis
        3. Incorporate the key insights from the processing
        4. Be conversational and user-friendly
        5. Provide actionable information where appropriate
        
        Create a response that feels natural and directly addresses what the user was asking about.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful, knowledgeable assistant that provides comprehensive and engaging responses."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        logger.error(f"Error enhancing response with OpenAI: {e}")
        return f"Based on your query, here's what I found: {langchain_output.get('processed_query', 'I processed your request successfully.')}"


def calculate_confidence_score(langchain_output: dict, sentiment: SentimentAnalysis) -> float:
    """Calculate confidence score based on processing results"""
    try:
        # Base confidence
        confidence = 0.5
        
        # Increase confidence based on available data
        if langchain_output.get('keywords'):
            confidence += 0.1 * min(len(langchain_output['keywords']) / 5, 1)
        
        if langchain_output.get('processed_query') and len(langchain_output['processed_query']) > 50:
            confidence += 0.2
        
        if langchain_output.get('summary') and len(langchain_output['summary']) > 20:
            confidence += 0.1
        
        # Adjust based on sentiment certainty
        sentiment_certainty = abs(sentiment.polarity)
        confidence += 0.1 * sentiment_certainty
        
        # Ensure confidence is between 0 and 1
        return min(max(confidence, 0.0), 1.0)
    
    except Exception as e:
        logger.error(f"Error calculating confidence score: {e}")
        return 0.5  # Default confidence


@app.post("/process", response_model=PydanticAIAgentOutput)
async def process_langchain_output(input_data: PydanticAIAgentInput):
    """Process LangChain output using PydanticAI with OpenAI and TextBlob"""
    start_time = time.time()
    
    try:
        langchain_result = input_data.langchain_output
        logger.info(f"Processing LangChain output for query: {langchain_result.processed_query[:100]}...")
        
        # Convert langchain output to dict for easier processing
        langchain_dict = langchain_result.model_dump()
        
        # Analyze sentiment
        sentiment = analyze_sentiment(langchain_result.processed_query)
        
        # Enrich keywords with OpenAI
        enriched_keywords = enrich_keywords_with_openai(
            langchain_result.keywords, 
            langchain_result.processed_query
        )
        
        # Enhance response with OpenAI
        enhanced_response = enhance_response_with_openai(langchain_dict, sentiment)
        
        # Calculate confidence score
        confidence_score = calculate_confidence_score(langchain_dict, sentiment)
        
        processing_time = time.time() - start_time
        
        result = PydanticAIAgentOutput(
            enhanced_response=enhanced_response,
            sentiment_analysis=sentiment,
            confidence_score=confidence_score,
            enriched_keywords=enriched_keywords,
            processing_time=processing_time
        )
        
        logger.info(f"Successfully processed LangChain output in {processing_time:.2f}s")
        return result
    
    except Exception as e:
        logger.error(f"Error processing LangChain output: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent": "pydantic_ai_agent",
        "models": ["gpt-3.5-turbo", "textblob"],
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "PydanticAI Agent with OpenAI and TextBlob",
        "endpoints": {
            "process": "/process",
            "health": "/health",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    logger.info("Starting PydanticAI Agent on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001) 