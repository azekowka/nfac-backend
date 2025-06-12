from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func, text
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
from database import SessionLocal
from data_fetcher.models import FetchedNews, FetchLog, FetchedWebsiteData
from data_fetcher.tasks import manual_news_fetch_task, cleanup_old_data_task, fetch_status_report_task
from celery.result import AsyncResult
from celery_app import celery_app

router = APIRouter(prefix="/data-fetcher", tags=["Data Fetcher"])

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models for API responses
class NewsArticle(BaseModel):
    id: int
    title: str
    description: Optional[str]
    url: str
    source: str
    author: Optional[str]
    published_date: Optional[datetime]
    category: Optional[str]
    tags: Optional[List[str]]
    fetch_date: datetime
    processed: bool
    sentiment_score: Optional[float]
    
    class Config:
        from_attributes = True

class FetchLogResponse(BaseModel):
    id: int
    task_name: str
    source: str
    start_time: datetime
    end_time: Optional[datetime]
    status: str
    items_fetched: int
    items_new: int
    error_message: Optional[str]
    execution_time: Optional[float]
    
    class Config:
        from_attributes = True

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

class StatsResponse(BaseModel):
    total_articles: int
    articles_today: int
    articles_this_week: int
    sources_count: int
    last_fetch: Optional[datetime]
    success_rate: float

# GET endpoints for data retrieval

@router.get("/news", response_model=List[NewsArticle])
def get_news(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    source: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get fetched news articles with filtering and pagination"""
    
    query = db.query(FetchedNews)
    
    # Apply filters
    if source:
        query = query.filter(FetchedNews.source == source)
    
    if category:
        query = query.filter(FetchedNews.category == category)
    
    if from_date:
        query = query.filter(FetchedNews.fetch_date >= from_date)
    
    if to_date:
        query = query.filter(FetchedNews.fetch_date <= to_date)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            FetchedNews.title.ilike(search_term) | 
            FetchedNews.description.ilike(search_term)
        )
    
    # Order by fetch date descending
    query = query.order_by(desc(FetchedNews.fetch_date))
    
    # Apply pagination
    articles = query.offset(skip).limit(limit).all()
    
    return articles

@router.get("/news/{article_id}", response_model=NewsArticle)
def get_news_article(article_id: int, db: Session = Depends(get_db)):
    """Get a specific news article by ID"""
    
    article = db.query(FetchedNews).filter(FetchedNews.id == article_id).first()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return article

@router.get("/sources")
def get_news_sources(db: Session = Depends(get_db)):
    """Get list of available news sources"""
    
    sources = db.query(FetchedNews.source, func.count(FetchedNews.id).label('count')).group_by(FetchedNews.source).all()
    
    return [{"source": source, "count": count} for source, count in sources]

@router.get("/categories")
def get_news_categories(db: Session = Depends(get_db)):
    """Get list of available news categories"""
    
    categories = db.query(FetchedNews.category, func.count(FetchedNews.id).label('count')).group_by(FetchedNews.category).all()
    
    return [{"category": category, "count": count} for category, count in categories]

@router.get("/stats", response_model=StatsResponse)
def get_statistics(db: Session = Depends(get_db)):
    """Get overall statistics about fetched data"""
    
    today = datetime.utcnow().date()
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    # Total articles
    total_articles = db.query(FetchedNews).count()
    
    # Articles today
    articles_today = db.query(FetchedNews).filter(
        func.date(FetchedNews.fetch_date) == today
    ).count()
    
    # Articles this week
    articles_this_week = db.query(FetchedNews).filter(
        FetchedNews.fetch_date >= week_ago
    ).count()
    
    # Number of sources
    sources_count = db.query(FetchedNews.source).distinct().count()
    
    # Last successful fetch
    last_successful_log = db.query(FetchLog).filter(
        FetchLog.status == 'success'
    ).order_by(desc(FetchLog.end_time)).first()
    
    last_fetch = last_successful_log.end_time if last_successful_log else None
    
    # Success rate (last 7 days)
    total_fetches = db.query(FetchLog).filter(
        FetchLog.start_time >= week_ago
    ).count()
    
    successful_fetches = db.query(FetchLog).filter(
        FetchLog.start_time >= week_ago,
        FetchLog.status == 'success'
    ).count()
    
    success_rate = (successful_fetches / total_fetches * 100) if total_fetches > 0 else 0
    
    return StatsResponse(
        total_articles=total_articles,
        articles_today=articles_today,
        articles_this_week=articles_this_week,
        sources_count=sources_count,
        last_fetch=last_fetch,
        success_rate=round(success_rate, 2)
    )

@router.get("/logs", response_model=List[FetchLogResponse])
def get_fetch_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    task_name: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get fetch operation logs"""
    
    query = db.query(FetchLog)
    
    if status:
        query = query.filter(FetchLog.status == status)
    
    if task_name:
        query = query.filter(FetchLog.task_name == task_name)
    
    # Order by start time descending
    query = query.order_by(desc(FetchLog.start_time))
    
    logs = query.offset(skip).limit(limit).all()
    
    return logs

# POST endpoints for triggering operations

@router.post("/fetch/manual", response_model=TaskResponse)
def trigger_manual_fetch(fetch_content: bool = Query(False)):
    """Manually trigger a news fetch operation"""
    
    try:
        # Start the manual fetch task
        task = manual_news_fetch_task.delay(fetch_content=fetch_content)
        
        return TaskResponse(
            task_id=task.id,
            status="started",
            message=f"Manual fetch task started with ID: {task.id}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start fetch task: {str(e)}")

@router.post("/cleanup", response_model=TaskResponse)
def trigger_cleanup(days_to_keep: int = Query(30, ge=1, le=365)):
    """Manually trigger data cleanup operation"""
    
    try:
        # Start the cleanup task
        task = cleanup_old_data_task.delay(days_to_keep=days_to_keep)
        
        return TaskResponse(
            task_id=task.id,
            status="started",
            message=f"Cleanup task started with ID: {task.id}, keeping {days_to_keep} days"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start cleanup task: {str(e)}")

@router.post("/report", response_model=TaskResponse)
def generate_status_report():
    """Generate a comprehensive status report"""
    
    try:
        # Start the status report task
        task = fetch_status_report_task.delay()
        
        return TaskResponse(
            task_id=task.id,
            status="started",
            message=f"Status report task started with ID: {task.id}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start report task: {str(e)}")

# Task monitoring endpoints

@router.get("/task/{task_id}")
def get_task_status(task_id: str):
    """Get the status of a running task"""
    
    try:
        task = AsyncResult(task_id, app=celery_app)
        
        if task.state == 'PENDING':
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': 'Task is waiting to be processed'
            }
        elif task.state == 'PROGRESS':
            response = {
                'task_id': task_id,
                'state': task.state,
                'current': task.info.get('current', 0),
                'total': task.info.get('total', 1),
                'status': task.info.get('status', '')
            }
        elif task.state == 'SUCCESS':
            response = {
                'task_id': task_id,
                'state': task.state,
                'result': task.result
            }
        else:  # FAILURE
            response = {
                'task_id': task_id,
                'state': task.state,
                'error': str(task.info)
            }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")

@router.get("/health")
def health_check():
    """Health check endpoint for data fetcher service"""
    try:
        db = SessionLocal()
        
        # Test database connection
        db.execute(text("SELECT 1"))
        
        # Test Redis connection through Celery
        celery_status = celery_app.control.inspect().ping()
        
        # Test recent fetch status
        recent_fetch = db.query(FetchLog).order_by(desc(FetchLog.start_time)).first()
        
        db.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "celery": "connected" if celery_status else "disconnected",
            "last_fetch": recent_fetch.start_time.isoformat() if recent_fetch else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        } 