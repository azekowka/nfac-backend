from fastapi import APIRouter, Depends, Body, Path, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from database import get_async_db
from tasks.models import TaskCreate, TaskUpdate, Task as TaskResponse
from tasks.crud import TaskCRUD

router = APIRouter()

@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    task: TaskCreate = Body(...),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new task"""
    return await TaskCRUD.create_task(db, task)

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int = Path(..., description="The ID of the task to retrieve"),
    db: AsyncSession = Depends(get_async_db)
):
    """Get a specific task by ID"""
    return await TaskCRUD.get_task(db, task_id)

@router.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(
    skip: int = Query(0, ge=0, description="Number of tasks to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of tasks to return"),
    db: AsyncSession = Depends(get_async_db)
):
    """Get all tasks with pagination"""
    return await TaskCRUD.get_tasks(db, skip=skip, limit=limit)

@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int = Path(..., description="The ID of the task to update"),
    task: TaskUpdate = Body(...),
    db: AsyncSession = Depends(get_async_db)
):
    """Update a specific task"""
    return await TaskCRUD.update_task(db, task_id, task)

@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int = Path(..., description="The ID of the task to delete"),
    db: AsyncSession = Depends(get_async_db)
):
    """Delete a specific task"""
    return await TaskCRUD.delete_task(db, task_id)
