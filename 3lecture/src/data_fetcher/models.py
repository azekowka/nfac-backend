from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON
from database import engine, Base
from datetime import datetime
from typing import Optional, Dict, Any
import json

class FetchedNews(Base):
    """Database model for fetched news articles"""
    __tablename__ = "fetched_news"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    url = Column(String(1000), nullable=False, unique=True, index=True)
    source = Column(String(100), nullable=False, index=True)
    author = Column(String(200), nullable=True)
    published_date = Column(DateTime, nullable=True)
    content = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    tags = Column(JSON, nullable=True)  # Store as JSON array
    
    # Metadata
    fetch_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed = Column(Boolean, default=False, index=True)
    sentiment_score = Column(Float, nullable=True)  # Can be used with AI analysis
    
    def __repr__(self):
        return f"<FetchedNews(id={self.id}, title='{self.title[:50]}...', source='{self.source}')>"


class FetchedWebsiteData(Base):
    """Generic model for any website data"""
    __tablename__ = "fetched_website_data"
    
    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String(100), nullable=False, index=True)
    source_url = Column(String(1000), nullable=False)
    data_type = Column(String(50), nullable=False, index=True)  # 'news', 'price', 'weather', etc.
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)
    structured_data = Column(JSON, nullable=True)  # Store any structured data as JSON
    
    # Metadata
    fetch_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    processing_time = Column(Float, nullable=True)
    
    def __repr__(self):
        return f"<FetchedWebsiteData(id={self.id}, type='{self.data_type}', source='{self.source_name}')>"


class FetchLog(Base):
    """Log of fetch operations"""
    __tablename__ = "fetch_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(100), nullable=False, index=True)
    source = Column(String(100), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, index=True)  # 'running', 'success', 'failed'
    items_fetched = Column(Integer, default=0)
    items_new = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    execution_time = Column(Float, nullable=True)
    
    def __repr__(self):
        return f"<FetchLog(id={self.id}, task='{self.task_name}', status='{self.status}')>"


# Create tables
def create_tables():
    """Create all tables if they don't exist"""
    Base.metadata.create_all(bind=engine) 