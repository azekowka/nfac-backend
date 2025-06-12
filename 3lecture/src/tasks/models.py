from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class TaskCreate(BaseModel):
    """Schema for creating a new task"""
    title: str = Field(..., min_length=1, max_length=200, description="The title of the task")
    description: Optional[str] = Field(None, max_length=1000, description="The description of the task")


class TaskUpdate(BaseModel):
    """Schema for updating an existing task"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="The title of the task")
    description: Optional[str] = Field(None, max_length=1000, description="The description of the task")
    completed: Optional[bool] = Field(None, description="Whether the task is completed")


class Task(BaseModel):
    """Schema for task responses"""
    id: int
    title: str
    description: Optional[str] = None
    completed: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class TaskDelete(BaseModel):
    """Schema for task deletion confirmation"""
    id: int
    message: str
