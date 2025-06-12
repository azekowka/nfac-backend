import asyncio
import time
import logging
from typing import Optional
import httpx
from assistant.models import (
    LangchainAgentInput,
    LangchainAgentOutput,
    PydanticAIAgentInput,
    PydanticAIAgentOutput,
    FinalResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class A2AClient:
    """Agent-to-Agent communication client"""
    
    def __init__(
        self, 
        langchain_url: str = "http://langchain-agent:8000",
        pydantic_ai_url: str = "http://pydantic-ai-agent:8001",
        timeout: float = 30.0
    ):
        self.langchain_url = langchain_url
        self.pydantic_ai_url = pydantic_ai_url
        self.timeout = timeout
        
    async def check_agents_health(self) -> dict:
        """Check health status of both agents"""
        results = {
            "langchain_agent": {"status": "unknown", "error": None},
            "pydantic_ai_agent": {"status": "unknown", "error": None}
        }
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check LangChain agent
            try:
                response = await client.get(f"{self.langchain_url}/health")
                if response.status_code == 200:
                    results["langchain_agent"]["status"] = "healthy"
                    results["langchain_agent"]["data"] = response.json()
                else:
                    results["langchain_agent"]["status"] = "unhealthy"
                    results["langchain_agent"]["error"] = f"HTTP {response.status_code}"
            except Exception as e:
                results["langchain_agent"]["status"] = "error"
                results["langchain_agent"]["error"] = str(e)
            
            # Check PydanticAI agent
            try:
                response = await client.get(f"{self.pydantic_ai_url}/health")
                if response.status_code == 200:
                    results["pydantic_ai_agent"]["status"] = "healthy"
                    results["pydantic_ai_agent"]["data"] = response.json()
                else:
                    results["pydantic_ai_agent"]["status"] = "unhealthy"
                    results["pydantic_ai_agent"]["error"] = f"HTTP {response.status_code}"
            except Exception as e:
                results["pydantic_ai_agent"]["status"] = "error"
                results["pydantic_ai_agent"]["error"] = str(e)
        
        return results
    
    async def process_query(
        self, 
        query: str, 
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        additional_context: Optional[str] = None
    ) -> FinalResponse:
        """Process query through both agents using A2A communication"""
        start_time = time.time()
        
        try:
            logger.info(f"Starting A2A processing for query: {query[:100]}...")
            
            # Step 1: Send query to LangChain agent
            langchain_input = LangchainAgentInput(
                query=query,
                user_id=user_id,
                session_id=session_id,
                additional_context=additional_context
            )
            
            logger.info("Sending request to LangChain agent...")
            langchain_result = await self._call_langchain_agent(langchain_input)
            
            # Step 2: Send LangChain result to PydanticAI agent
            pydantic_ai_input = PydanticAIAgentInput(
                langchain_output=langchain_result
            )
            
            logger.info("Sending LangChain result to PydanticAI agent...")
            pydantic_ai_result = await self._call_pydantic_ai_agent(pydantic_ai_input)
            
            # Step 3: Combine results
            total_processing_time = time.time() - start_time
            
            # Create combined response
            combined_response = self._create_combined_response(
                langchain_result, 
                pydantic_ai_result
            )
            
            final_response = FinalResponse(
                original_query=query,
                langchain_result=langchain_result,
                pydantic_ai_result=pydantic_ai_result,
                combined_response=combined_response,
                total_processing_time=total_processing_time,
                success=True
            )
            
            logger.info(f"A2A processing completed successfully in {total_processing_time:.2f}s")
            return final_response
            
        except Exception as e:
            total_processing_time = time.time() - start_time
            logger.error(f"Error in A2A processing: {e}")
            
            # Return error response
            return FinalResponse(
                original_query=query,
                langchain_result=LangchainAgentOutput(
                    processed_query="Error occurred during processing",
                    keywords=[],
                    summary="Processing failed",
                    processing_time=0.0
                ),
                pydantic_ai_result=PydanticAIAgentOutput(
                    enhanced_response="Error occurred during processing",
                    sentiment_analysis={"polarity": 0.0, "subjectivity": 0.0, "label": "neutral"},
                    confidence_score=0.0,
                    enriched_keywords=[],
                    processing_time=0.0
                ),
                combined_response=f"Sorry, I encountered an error while processing your query: {str(e)}",
                total_processing_time=total_processing_time,
                success=False,
                error_message=str(e)
            )
    
    async def _call_langchain_agent(self, input_data: LangchainAgentInput) -> LangchainAgentOutput:
        """Call LangChain agent"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.langchain_url}/process",
                json=input_data.model_dump()
            )
            
            if response.status_code != 200:
                raise Exception(f"LangChain agent error: HTTP {response.status_code} - {response.text}")
            
            return LangchainAgentOutput(**response.json())
    
    async def _call_pydantic_ai_agent(self, input_data: PydanticAIAgentInput) -> PydanticAIAgentOutput:
        """Call PydanticAI agent"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.pydantic_ai_url}/process",
                json=input_data.model_dump()
            )
            
            if response.status_code != 200:
                raise Exception(f"PydanticAI agent error: HTTP {response.status_code} - {response.text}")
            
            return PydanticAIAgentOutput(**response.json())
    
    def _create_combined_response(
        self, 
        langchain_result: LangchainAgentOutput, 
        pydantic_ai_result: PydanticAIAgentOutput
    ) -> str:
        """Create a combined response from both agents' outputs"""
        try:
            # Use the enhanced response from PydanticAI as the primary response
            primary_response = pydantic_ai_result.enhanced_response
            
            # Add sentiment information if significant
            sentiment = pydantic_ai_result.sentiment_analysis
            if abs(sentiment.polarity) > 0.3:  # Only mention sentiment if it's significant
                sentiment_note = f"\n\n*Note: I detected a {sentiment.label} sentiment in your query.*"
                primary_response += sentiment_note
            
            # Add confidence information if low
            if pydantic_ai_result.confidence_score < 0.6:
                confidence_note = f"\n\n*Please note: My confidence in this response is moderate ({pydantic_ai_result.confidence_score:.1%}). Feel free to ask for clarification.*"
                primary_response += confidence_note
            
            return primary_response
            
        except Exception as e:
            logger.error(f"Error creating combined response: {e}")
            return langchain_result.processed_query


# Demo function for testing
async def demo_a2a_client():
    """Demo function to test A2A communication"""
    client = A2AClient()
    
    # Check agents health
    print("🔍 Checking agents health...")
    health = await client.check_agents_health()
    print("Health status:")
    for agent, status in health.items():
        print(f"  {agent}: {status['status']}")
        if status.get('error'):
            print(f"    Error: {status['error']}")
    
    # Test queries
    test_queries = [
        "What is artificial intelligence and how does it work?",
        "I'm feeling frustrated with my computer problems. Can you help?",
        "Explain the benefits of renewable energy sources",
        "How do I improve my programming skills?",
        "What are the latest trends in machine learning?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"🤖 Processing: {query}")
        print('='*50)
        
        try:
            result = await client.process_query(
                query=query,
                user_id="demo_user",
                session_id="demo_session"
            )
            
            print(f"\n📊 Processing Results:")
            print(f"   Total Time: {result.total_processing_time:.2f}s")
            print(f"   Success: {result.success}")
            
            if result.success:
                print(f"\n📝 Keywords: {', '.join(result.langchain_result.keywords[:5])}")
                print(f"📊 Sentiment: {result.pydantic_ai_result.sentiment_analysis.label}")
                print(f"🎯 Confidence: {result.pydantic_ai_result.confidence_score:.1%}")
                print(f"\n💬 Final Response:")
                print(result.combined_response)
            else:
                print(f"\n❌ Error: {result.error_message}")
                
        except Exception as e:
            print(f"❌ Demo error: {e}")
        
        # Wait a bit between requests
        await asyncio.sleep(1)


if __name__ == "__main__":
    print("🚀 Starting A2A Client Demo...")
    asyncio.run(demo_a2a_client()) 