"""
SQLAlchemy ORM models for TaskFlow2.
"""
import enum
from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Priority(enum.Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(enum.Enum):
    """Task workflow status."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # Relationships
    projects: Mapped[List["Project"]] = relationship(
        "Project", back_populates="owner", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="projects")
    tasks: Mapped[List["Task"]] = relationship(
        "Task", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name}, owner_id={self.owner_id})>"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    priority: Mapped[Priority] = mapped_column(
        Enum(Priority), nullable=False, default=Priority.MEDIUM
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False, default=TaskStatus.TODO, server_default="todo"
    )
    due_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title={self.title}, project_id={self.project_id})>"    