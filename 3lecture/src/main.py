from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from auth.api import router as auth_router
from database import get_async_db
from tasks.api import router as tasks_router
from celery_tasks import example_task, send_notification, process_data
from redis_client import test_redis_connection

app = FastAPI()

app.include_router(auth_router, tags=["auth"])
app.include_router(tasks_router, tags=["tasks"])


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


@app.get("/health")
async def check_health(db: AsyncSession = Depends(get_async_db)):
    try:
        await db.execute(text("SELECT 1"))
    except OperationalError:
        raise HTTPException(
            status_code=500, detail="Database connection failed"
        )

    # Check Redis connection
    redis_status = "connected" if test_redis_connection() else "disconnected"

    return {
        "status": "ok", 
        "database": "connected",
        "redis": redis_status
    }


@app.post("/tasks/example")
async def run_example_task(name: str):
    """Run an example Celery task"""
    task = example_task.delay(name)
    return {
        "task_id": task.id,
        "status": "Task queued",
        "message": f"Example task queued for {name}"
    }


@app.post("/tasks/notification")
async def send_notification_task(message: str, recipient: str):
    """Send a notification using Celery"""
    task = send_notification.delay(message, recipient)
    return {
        "task_id": task.id,
        "status": "Task queued",
        "message": f"Notification task queued for {recipient}"
    }


@app.post("/tasks/process")
async def process_data_task(data: dict):
    """Process data using Celery"""
    task = process_data.delay(data)
    return {
        "task_id": task.id,
        "status": "Task queued",
        "message": "Data processing task queued"
    }


@app.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """Get the status of a Celery task"""
    from celery.result import AsyncResult
    from celery_app import celery_app
    
    result = AsyncResult(task_id, app=celery_app)
    
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None
    }
