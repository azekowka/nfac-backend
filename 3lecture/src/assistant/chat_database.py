from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, JSON
from sqlalchemy.orm import sessionmaker
from database import engine, get_db, Base, SessionLocal
from datetime import datetime
from typing import List, Optional, Dict, Any
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatHistoryDB(Base):
    """Database model for chat history"""
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), index=True, nullable=False)
    session_id = Column(String(255), index=True, nullable=False)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    
    # LangChain agent data
    langchain_processing_time = Column(Float, nullable=True)
    langchain_keywords = Column(JSON, nullable=True)
    langchain_summary = Column(Text, nullable=True)
    langchain_context = Column(JSON, nullable=True)
    
    # PydanticAI agent data
    pydantic_ai_processing_time = Column(Float, nullable=True)
    sentiment_polarity = Column(Float, nullable=True)
    sentiment_subjectivity = Column(Float, nullable=True)
    sentiment_label = Column(String(50), nullable=True)
    confidence_score = Column(Float, nullable=True)
    enriched_keywords = Column(JSON, nullable=True)
    
    # Overall processing data
    total_processing_time = Column(Float, nullable=False)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatService:
    """Service for managing chat history and database operations"""
    
    def __init__(self):
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
    
    def save_chat_message(
        self,
        user_id: str,
        session_id: str,
        query: str,
        response: str,
        langchain_data: Optional[Dict[str, Any]] = None,
        pydantic_ai_data: Optional[Dict[str, Any]] = None,
        total_processing_time: float = 0.0,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> int:
        """Save chat message to database"""
        try:
            db = SessionLocal()
            
            # Prepare LangChain data
            langchain_keywords = None
            langchain_summary = None
            langchain_context = None
            langchain_processing_time = None
            
            if langchain_data:
                langchain_keywords = langchain_data.get('keywords', [])
                langchain_summary = langchain_data.get('summary')
                langchain_context = langchain_data.get('context', {})
                langchain_processing_time = langchain_data.get('processing_time', 0.0)
            
            # Prepare PydanticAI data
            sentiment_polarity = None
            sentiment_subjectivity = None
            sentiment_label = None
            confidence_score = None
            enriched_keywords = None
            pydantic_ai_processing_time = None
            
            if pydantic_ai_data:
                sentiment_analysis = pydantic_ai_data.get('sentiment_analysis', {})
                sentiment_polarity = sentiment_analysis.get('polarity')
                sentiment_subjectivity = sentiment_analysis.get('subjectivity')
                sentiment_label = sentiment_analysis.get('label')
                confidence_score = pydantic_ai_data.get('confidence_score')
                enriched_keywords = pydantic_ai_data.get('enriched_keywords', [])
                pydantic_ai_processing_time = pydantic_ai_data.get('processing_time', 0.0)
            
            # Create chat history record
            chat_record = ChatHistoryDB(
                user_id=user_id,
                session_id=session_id,
                query=query,
                response=response,
                langchain_processing_time=langchain_processing_time,
                langchain_keywords=langchain_keywords,
                langchain_summary=langchain_summary,
                langchain_context=langchain_context,
                pydantic_ai_processing_time=pydantic_ai_processing_time,
                sentiment_polarity=sentiment_polarity,
                sentiment_subjectivity=sentiment_subjectivity,
                sentiment_label=sentiment_label,
                confidence_score=confidence_score,
                enriched_keywords=enriched_keywords,
                total_processing_time=total_processing_time,
                success=success,
                error_message=error_message
            )
            
            db.add(chat_record)
            db.commit()
            db.refresh(chat_record)
            
            logger.info(f"Saved chat message with ID: {chat_record.id}")
            return chat_record.id
            
        except Exception as e:
            logger.error(f"Error saving chat message: {e}")
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_chat_history(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get chat history for a user"""
        try:
            db = SessionLocal()
            
            query = db.query(ChatHistoryDB).filter(ChatHistoryDB.user_id == user_id)
            
            if session_id:
                query = query.filter(ChatHistoryDB.session_id == session_id)
            
            query = query.order_by(ChatHistoryDB.created_at.desc())
            query = query.offset(offset).limit(limit)
            
            chat_records = query.all()
            
            # Convert to dictionaries
            chat_history = []
            for record in chat_records:
                chat_data = {
                    "id": record.id,
                    "user_id": record.user_id,
                    "session_id": record.session_id,
                    "query": record.query,
                    "response": record.response,
                    "langchain_data": {
                        "processing_time": record.langchain_processing_time,
                        "keywords": record.langchain_keywords,
                        "summary": record.langchain_summary,
                        "context": record.langchain_context
                    },
                    "pydantic_ai_data": {
                        "processing_time": record.pydantic_ai_processing_time,
                        "sentiment_analysis": {
                            "polarity": record.sentiment_polarity,
                            "subjectivity": record.sentiment_subjectivity,
                            "label": record.sentiment_label
                        },
                        "confidence_score": record.confidence_score,
                        "enriched_keywords": record.enriched_keywords
                    },
                    "total_processing_time": record.total_processing_time,
                    "success": record.success,
                    "error_message": record.error_message,
                    "created_at": record.created_at.isoformat()
                }
                chat_history.append(chat_data)
            
            return chat_history
            
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            raise e
        finally:
            db.close()
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for a user"""
        try:
            db = SessionLocal()
            
            # Basic stats
            total_messages = db.query(ChatHistoryDB).filter(ChatHistoryDB.user_id == user_id).count()
            successful_messages = db.query(ChatHistoryDB).filter(
                ChatHistoryDB.user_id == user_id,
                ChatHistoryDB.success == True
            ).count()
            
            # Average processing time
            avg_processing_time_result = db.query(
                db.func.avg(ChatHistoryDB.total_processing_time)
            ).filter(
                ChatHistoryDB.user_id == user_id,
                ChatHistoryDB.success == True
            ).scalar()
            
            avg_processing_time = avg_processing_time_result or 0.0
            
            # Sentiment stats
            sentiment_stats = db.query(
                ChatHistoryDB.sentiment_label,
                db.func.count(ChatHistoryDB.sentiment_label)
            ).filter(
                ChatHistoryDB.user_id == user_id,
                ChatHistoryDB.sentiment_label.isnot(None)
            ).group_by(ChatHistoryDB.sentiment_label).all()
            
            sentiment_distribution = {label: count for label, count in sentiment_stats}
            
            # Average confidence score
            avg_confidence_result = db.query(
                db.func.avg(ChatHistoryDB.confidence_score)
            ).filter(
                ChatHistoryDB.user_id == user_id,
                ChatHistoryDB.confidence_score.isnot(None)
            ).scalar()
            
            avg_confidence = avg_confidence_result or 0.0
            
            stats = {
                "user_id": user_id,
                "total_messages": total_messages,
                "successful_messages": successful_messages,
                "success_rate": successful_messages / total_messages if total_messages > 0 else 0.0,
                "average_processing_time": avg_processing_time,
                "average_confidence_score": avg_confidence,
                "sentiment_distribution": sentiment_distribution
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            raise e
        finally:
            db.close()
    
    def get_recent_sessions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent sessions for a user"""
        try:
            db = SessionLocal()
            
            # Get distinct sessions with latest message date
            sessions_query = db.query(
                ChatHistoryDB.session_id,
                db.func.max(ChatHistoryDB.created_at).label('last_message'),
                db.func.count(ChatHistoryDB.id).label('message_count')
            ).filter(
                ChatHistoryDB.user_id == user_id
            ).group_by(
                ChatHistoryDB.session_id
            ).order_by(
                db.func.max(ChatHistoryDB.created_at).desc()
            ).limit(limit)
            
            sessions = sessions_query.all()
            
            session_list = []
            for session in sessions:
                session_data = {
                    "session_id": session.session_id,
                    "last_message": session.last_message.isoformat(),
                    "message_count": session.message_count
                }
                session_list.append(session_data)
            
            return session_list
            
        except Exception as e:
            logger.error(f"Error getting recent sessions: {e}")
            raise e
        finally:
            db.close()


# Global chat service instance
chat_service = ChatService() 