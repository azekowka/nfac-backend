from celery import current_app
from celery_app import celery_app
from redis_client import redis_client
import time
import logging
from tasks.tasks import add_random_task, add_multiple_random_tasks

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def example_task(self, name: str):
    """
    Example Celery task that demonstrates basic functionality
    """
    try:
        logger.info(f"Starting task for {name}")
        
        # Simulate some work
        time.sleep(2)
        
        # Store result in Redis
        redis_client.setex(f"task_result_{self.request.id}", 3600, f"Hello {name}!")
        
        logger.info(f"Task completed for {name}")
        return f"Task completed for {name}"
    
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        self.retry(exc=exc, countdown=60, max_retries=3)

@celery_app.task
def send_notification(message: str, recipient: str):
    """
    Example task for sending notifications
    """
    logger.info(f"Sending notification to {recipient}: {message}")
    # Simulate notification sending
    time.sleep(1)
    return f"Notification sent to {recipient}"

@celery_app.task
def process_data(data: dict):
    """
    Example task for data processing
    """
    logger.info(f"Processing data: {data}")
    
    # Simulate data processing
    time.sleep(3)
    
    # Store processed data in Redis
    processed_key = f"processed_data_{int(time.time())}"
    redis_client.setex(processed_key, 3600, str(data))
    
    return {
        "status": "processed",
        "data": data,
        "key": processed_key
    }

@celery_app.task
def cleanup_old_data():
    """
    Example periodic task for cleanup operations
    """
    logger.info("Running cleanup task")
    
    # Example: Clean up old Redis keys
    # This is just an example - implement your actual cleanup logic
    keys_deleted = 0
    for key in redis_client.scan_iter(match="temp_*"):
        redis_client.delete(key)
        keys_deleted += 1
    
    logger.info(f"Cleanup completed. Deleted {keys_deleted} keys")
    return f"Cleaned up {keys_deleted} temporary keys"

@celery_app.task
def trigger_random_task_creation():
    """
    Example task that triggers the creation of random tasks
    """
    logger.info("Triggering random task creation")
    
    # Call the random task creation
    result1 = add_random_task.delay()
    result2 = add_multiple_random_tasks.delay(3)
    
    return {
        "status": "triggered",
        "single_task_id": result1.id,
        "multiple_tasks_id": result2.id,
        "message": "Random task creation has been triggered"
    } 