from celery import Celery
from config import settings

# Create Celery instance
celery_app = Celery(
    "tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["celery_tasks", "tasks.tasks", "data_fetcher.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
)

# Import data fetcher scheduler (this will configure beat_schedule)
from data_fetcher.scheduler import *

# Optional: Add additional periodic tasks
# celery_app.conf.beat_schedule.update({
#     'example-periodic-task': {
#         'task': 'celery_tasks.example_task',
#         'schedule': 300.0,  # Run every 5 minutes
#         'args': ('Scheduled Task',)
#     },
# })

if __name__ == "__main__":
    celery_app.start() 