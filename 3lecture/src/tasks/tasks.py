from celery_app import celery_app
from database import SyncSessionLocal
from tasks.schema import Task
from tasks.models import TaskCreate
import random
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# List of random task titles and descriptions for generating sample data
RANDOM_TITLES = [
    "Complete project documentation",
    "Review code changes",
    "Update database schema",
    "Fix authentication bug",
    "Implement new feature",
    "Optimize database queries",
    "Write unit tests",
    "Deploy to production",
    "Backup database",
    "Update dependencies",
    "Refactor legacy code",
    "Create API endpoint",
    "Update user interface",
    "Monitor system performance",
    "Security audit review"
]

RANDOM_DESCRIPTIONS = [
    "This task needs to be completed as soon as possible",
    "Low priority task that can be done when time permits",
    "Critical task that affects system functionality",
    "Maintenance task for keeping the system healthy",
    "Enhancement task to improve user experience",
    "Bug fix to resolve reported issues",
    "Documentation update for better clarity",
    "Performance improvement task",
    "Security-related task requiring attention",
    "Integration task with external services"
]

@celery_app.task
def add_random_task():
    """
    Celery task that adds a random task to the database
    """
    try:
        # Create a database session
        db = SyncSessionLocal()
        
        # Generate random task data
        random_title = random.choice(RANDOM_TITLES)
        random_description = random.choice(RANDOM_DESCRIPTIONS)
        
        # Create a new task instance
        new_task = Task(
            title=random_title,
            description=random_description,
            completed=False
        )
        
        # Add to database
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        
        logger.info(f"Successfully added random task: {new_task.title} (ID: {new_task.id})")
        
        # Close the session
        db.close()
        
        return {
            "status": "success",
            "task_id": new_task.id,
            "title": new_task.title,
            "description": new_task.description,
            "message": f"Random task '{new_task.title}' added successfully"
        }
        
    except Exception as exc:
        logger.error(f"Failed to add random task: {exc}")
        if 'db' in locals():
            db.rollback()
            db.close()
        raise exc

@celery_app.task
def add_multiple_random_tasks(count: int = 5):
    """
    Celery task that adds multiple random tasks to the database
    
    Args:
        count (int): Number of random tasks to create (default: 5)
    """
    try:
        created_tasks = []
        
        for i in range(count):
            # Create a database session for each task
            db = SyncSessionLocal()
            
            # Generate random task data
            random_title = random.choice(RANDOM_TITLES)
            random_description = random.choice(RANDOM_DESCRIPTIONS)
            
            # Create a new task instance
            new_task = Task(
                title=f"{random_title} #{i+1}",
                description=random_description,
                completed=random.choice([True, False])  # Randomly set completion status
            )
            
            # Add to database
            db.add(new_task)
            db.commit()
            db.refresh(new_task)
            
            created_tasks.append({
                "id": new_task.id,
                "title": new_task.title,
                "completed": new_task.completed
            })
            
            db.close()
            
        logger.info(f"Successfully added {count} random tasks")
        
        return {
            "status": "success",
            "count": count,
            "tasks": created_tasks,
            "message": f"Successfully created {count} random tasks"
        }
        
    except Exception as exc:
        logger.error(f"Failed to add multiple random tasks: {exc}")
        raise exc

@celery_app.task
def periodic_add_random_task():
    """
    Periodic Celery task specifically designed for scheduled execution
    Adds a random task to the database every minute
    """
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Periodic task started at {current_time}")
        
        # Create a database session
        db = SyncSessionLocal()
        
        # Generate random task data with timestamp
        random_title = random.choice(RANDOM_TITLES)
        random_description = f"{random.choice(RANDOM_DESCRIPTIONS)} - Auto-generated at {current_time}"
        
        # Create a new task instance
        new_task = Task(
            title=f"[AUTO] {random_title}",
            description=random_description,
            completed=False
        )
        
        # Add to database
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        
        logger.info(f"Periodic task successfully added: {new_task.title} (ID: {new_task.id}) at {current_time}")
        
        # Close the session
        db.close()
        
        return {
            "status": "success",
            "task_id": new_task.id,
            "title": new_task.title,
            "description": new_task.description,
            "execution_time": current_time,
            "message": f"Periodic random task '{new_task.title}' added successfully at {current_time}"
        }
        
    except Exception as exc:
        logger.error(f"Periodic task failed at {datetime.now()}: {exc}")
        if 'db' in locals():
            db.rollback()
            db.close()
        raise exc


