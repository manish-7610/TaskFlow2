from datetime import datetime
from typing import Optional, Literal
from .models import Priority, TaskStatus

from pydantic import BaseModel, EmailStr, Field, field_validator


# ---------- Auth Schemas ----------
class TokenResponse(BaseModel):
    """Returned by /auth/login and /auth/register."""
    access_token: str
    token_type: str = "bearer"

# ---------- User Schemas ----------
class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name")
    password: str = Field(..., min_length=8, description="Plain password (will be hashed)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "alice@example.com",
                "full_name": "Alice Smith",
                "password": "securepassword123"
            }
        }
    }


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- Project Schemas ----------
class ProjectCreate(BaseModel):
    """
    Request body for creating a project.
    owner_id is NOT accepted here – it is injected server-side from the
    authenticated user's JWT.
    """
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, max_length=1000, description="Optional description")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Q4 Marketing Campaign",
                "description": "All tasks related to Q4 marketing",
            }
        }
    }


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- Task Schemas ----------
class TaskCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    priority: Priority = Field(default=Priority.MEDIUM)
    status: TaskStatus = Field(default=TaskStatus.TODO)
    due_date: Optional[str] = Field(None, max_length=50)
    project_id: int

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str):
        v = v.strip()
        if not v:
            raise ValueError("Task title cannot be empty")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Design landing page",
                "description": "Create mockups",
                "priority": "high",
                "status": "todo",
                "due_date": "2026-12-01",
                "project_id": 1,
            }
        }
    }


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[str] = None
    project_id: Optional[int] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Task title cannot be empty")
        return v


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    priority: Priority
    status: TaskStatus
    due_date: Optional[str]
    project_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


# ---------- AI Quick Add Schemas ----------
class QuickAddRequest(BaseModel):
    text: str = Field(..., min_length=1)
    project_id: int

    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Quick add text cannot be empty")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "Create a new project called Website Redesign with high priority tasks for frontend and backend"
            }
        }
    }


# ---------- AI Improve Task Schemas ----------
class ImproveTaskRequest(BaseModel):
    """Request body for improving an existing task via AI."""
    title: str = Field(..., min_length=1, max_length=255, description="Current task title to improve")
    description: Optional[str] = Field(None, max_length=1000, description="Existing description (preserved if improvement adds nothing)")
    priority: Optional[str] = Field(None, description="Existing priority – returned unchanged if no suggestion")
    due_date: Optional[str] = Field(None, description="Existing due date – returned unchanged if not inferable")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str):
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "react padhna hai",
                "description": None,
                "priority": "medium",
                "due_date": None,
            }
        }
    }


class ImproveTaskResponse(BaseModel):
    """Improved task fields returned by the AI."""
    title: str
    description: Optional[str]
    priority: str
    due_date: Optional[str]


# ---------- Status Update Schema ----------
class TaskStatusUpdate(BaseModel):
    """Used for the dedicated PATCH /tasks/{id}/status endpoint."""
    status: TaskStatus