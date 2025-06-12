from celery.schedules import crontab
from celery_app import celery_app

# Configure Celery Beat schedule
celery_app.conf.beat_schedule = {
    # Daily news fetch at 6:00 AM UTC
    'daily-news-fetch': {
        'task': 'daily_news_fetch',
        'schedule': crontab(hour=6, minute=0),  # 6:00 AM UTC daily
        'kwargs': {'fetch_content': False}  # Don't fetch full content for daily runs
    },
    
    # Weekly comprehensive fetch with full content on Sundays at 3:00 AM UTC
    'weekly-comprehensive-fetch': {
        'task': 'manual_news_fetch',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Sunday 3:00 AM UTC
        'kwargs': {'fetch_content': True}  # Fetch full content weekly
    },
    
    # Cleanup old data weekly on Sundays at 2:00 AM UTC
    'weekly-cleanup': {
        'task': 'cleanup_old_data',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Sunday 2:00 AM UTC
        'kwargs': {'days_to_keep': 30}
    },
    
    # Generate status report every 6 hours
    'status-report': {
        'task': 'fetch_status_report',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
    },
}

# Set timezone for the scheduler
celery_app.conf.timezone = 'UTC'

# Alternative schedule examples (commented out):
"""
# More frequent testing schedules:

# Every 30 minutes (for testing)
'frequent-news-fetch': {
    'task': 'daily_news_fetch',
    'schedule': crontab(minute='*/30'),
    'kwargs': {'fetch_content': False}
},

# Every hour during business hours
'business-hours-fetch': {
    'task': 'daily_news_fetch',
    'schedule': crontab(minute=0, hour='9-17'),
    'kwargs': {'fetch_content': False}
},

# Twice daily (morning and evening)
'twice-daily-fetch': {
    'task': 'daily_news_fetch',
    'schedule': crontab(hour=[6, 18], minute=0),
    'kwargs': {'fetch_content': False}
},
""" 