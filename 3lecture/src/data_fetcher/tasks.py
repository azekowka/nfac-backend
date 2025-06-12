import asyncio
import logging
from datetime import datetime
from celery import Celery
from celery_app import celery_app
from data_fetcher.news_fetcher import news_fetcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="daily_news_fetch")
def daily_news_fetch_task(self, fetch_content: bool = False):
    """Celery task to fetch news daily"""
    try:
        logger.info("Starting daily news fetch task...")
        
        # Run the async news fetcher
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(news_fetcher.fetch_all_news(fetch_content=fetch_content))
            logger.info(f"Daily news fetch completed: {result}")
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in daily news fetch task: {e}")
        # Update task state
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'timestamp': datetime.utcnow().isoformat()}
        )
        raise


@celery_app.task(bind=True, name="manual_news_fetch")
def manual_news_fetch_task(self, fetch_content: bool = True):
    """Manual news fetch task (can be triggered via API)"""
    try:
        logger.info("Starting manual news fetch task...")
        
        # Run the async news fetcher with content fetching enabled
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(news_fetcher.fetch_all_news(fetch_content=fetch_content))
            logger.info(f"Manual news fetch completed: {result}")
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in manual news fetch task: {e}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'timestamp': datetime.utcnow().isoformat()}
        )
        raise


@celery_app.task(bind=True, name="cleanup_old_data")
def cleanup_old_data_task(self, days_to_keep: int = 30):
    """Task to cleanup old fetched data"""
    try:
        logger.info(f"Starting cleanup task - keeping data from last {days_to_keep} days")
        
        from datetime import timedelta
        from data_fetcher.models import FetchedNews, FetchLog
        from database import SessionLocal
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        db = SessionLocal()
        
        try:
            # Delete old news
            old_news_count = db.query(FetchedNews).filter(
                FetchedNews.fetch_date < cutoff_date
            ).count()
            
            db.query(FetchedNews).filter(
                FetchedNews.fetch_date < cutoff_date
            ).delete()
            
            # Delete old logs (keep logs longer - 90 days)
            log_cutoff_date = datetime.utcnow() - timedelta(days=90)
            old_logs_count = db.query(FetchLog).filter(
                FetchLog.start_time < log_cutoff_date
            ).count()
            
            db.query(FetchLog).filter(
                FetchLog.start_time < log_cutoff_date
            ).delete()
            
            db.commit()
            
            result = {
                "success": True,
                "old_news_deleted": old_news_count,
                "old_logs_deleted": old_logs_count,
                "cutoff_date": cutoff_date.isoformat(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Cleanup completed: {result}")
            return result
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'timestamp': datetime.utcnow().isoformat()}
        )
        raise


@celery_app.task(bind=True, name="fetch_status_report")
def fetch_status_report_task(self):
    """Generate a status report of fetch operations"""
    try:
        logger.info("Generating fetch status report...")
        
        from data_fetcher.models import FetchedNews, FetchLog
        from database import SessionLocal
        from datetime import timedelta
        from sqlalchemy import func
        
        db = SessionLocal()
        
        try:
            # Get stats for last 7 days
            week_ago = datetime.utcnow() - timedelta(days=7)
            
            # News stats
            total_news = db.query(FetchedNews).count()
            recent_news = db.query(FetchedNews).filter(
                FetchedNews.fetch_date >= week_ago
            ).count()
            
            # Source breakdown
            source_stats = db.query(
                FetchedNews.source,
                func.count(FetchedNews.id).label('count')
            ).filter(
                FetchedNews.fetch_date >= week_ago
            ).group_by(FetchedNews.source).all()
            
            # Recent fetch logs
            recent_logs = db.query(FetchLog).filter(
                FetchLog.start_time >= week_ago
            ).order_by(FetchLog.start_time.desc()).limit(10).all()
            
            # Success rate
            total_recent_fetches = db.query(FetchLog).filter(
                FetchLog.start_time >= week_ago
            ).count()
            
            successful_fetches = db.query(FetchLog).filter(
                FetchLog.start_time >= week_ago,
                FetchLog.status == 'success'
            ).count()
            
            success_rate = (successful_fetches / total_recent_fetches * 100) if total_recent_fetches > 0 else 0
            
            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "total_articles": total_news,
                "articles_last_7_days": recent_news,
                "success_rate_percent": round(success_rate, 2),
                "total_fetch_operations_last_7_days": total_recent_fetches,
                "sources_breakdown": [
                    {"source": source, "count": count} 
                    for source, count in source_stats
                ],
                "recent_fetch_logs": [
                    {
                        "id": log.id,
                        "task": log.task_name,
                        "source": log.source,
                        "status": log.status,
                        "items_new": log.items_new,
                        "execution_time": log.execution_time,
                        "start_time": log.start_time.isoformat()
                    }
                    for log in recent_logs
                ]
            }
            
            logger.info(f"Status report generated: {report}")
            return report
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error generating status report: {e}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'timestamp': datetime.utcnow().isoformat()}
        )
        raise 