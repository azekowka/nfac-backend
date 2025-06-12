from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import NoResultFound
from fastapi import HTTPException
from tasks.schema import Task
from tasks.models import TaskCreate, TaskUpdate


class TaskCRUD:
    @staticmethod
    async def create_task(db: AsyncSession, task: TaskCreate):
        """Create a new task"""
        db_task = Task(
            title=task.title,
            description=task.description,
            completed=False
        )
        db.add(db_task)
        await db.commit()
        await db.refresh(db_task)
        return db_task

    @staticmethod
    async def get_task(db: AsyncSession, task_id: int):
        """Get a task by ID"""
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    @staticmethod
    async def get_tasks(db: AsyncSession, skip: int = 0, limit: int = 100):
        """Get all tasks with pagination"""
        result = await db.execute(select(Task).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def update_task(db: AsyncSession, task_id: int, task_update: TaskUpdate):
        """Update a task"""
        # Check if task exists
        result = await db.execute(select(Task).where(Task.id == task_id))
        existing_task = result.scalar_one_or_none()
        if not existing_task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Update only provided fields
        update_data = task_update.model_dump(exclude_unset=True)
        if update_data:
            await db.execute(
                update(Task).where(Task.id == task_id).values(**update_data)
            )
            await db.commit()
            await db.refresh(existing_task)
        
        return existing_task

    @staticmethod
    async def delete_task(db: AsyncSession, task_id: int):
        """Delete a task"""
        # Check if task exists
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        await db.execute(delete(Task).where(Task.id == task_id))
        await db.commit()
        return {"message": "Task deleted successfully"}