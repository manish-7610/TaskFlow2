"""
CRUD (Create, Read, Update, Delete) operations for TaskFlow2.
All functions use SQLAlchemy ORM and are designed to be reusable.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func

from .models import User, Project, Task, Priority, TaskStatus
from .schemas import UserCreate, ProjectCreate, TaskCreate, TaskUpdate


# ---------- User CRUD ----------
def create_user(db: Session, user_data: UserCreate) -> User:
    """
    Create a new user with a bcrypt-hashed password.

    Args:
        db: Database session.
        user_data: Pydantic schema with user creation data.

    Returns:
        User: The newly created User instance.
    """
    from .auth import hash_password  # local import avoids circular dependency at module load

    db_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    Retrieve a user by primary key.

    Args:
        db: Database session.
        user_id: ID of the user.

    Returns:
        Optional[User]: User if found, else None.
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Retrieve a user by email address.

    Args:
        db: Database session.
        email: Email address.

    Returns:
        Optional[User]: User if found, else None.
    """
    return db.query(User).filter(User.email == email).first()


def list_users(
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> List[User]:
    """
    List users with pagination.

    Args:
        db: Database session.
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        List[User]: List of users.
    """
    return db.query(User).offset(skip).limit(limit).all()


# ---------- Project CRUD ----------
def create_project(db: Session, project_data: ProjectCreate, owner_id: int) -> Project:
    """
    Create a new project owned by *owner_id*.

    owner_id is passed explicitly by the router (injected from the JWT),
    NOT taken from the request body.

    Args:
        db: Database session.
        project_data: Pydantic schema with project creation data (name + description).
        owner_id: ID of the authenticated user who will own this project.

    Returns:
        Project: The newly created Project instance.
    """
    db_project = Project(
        name=project_data.name,
        description=project_data.description,
        owner_id=owner_id,
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def get_project(db: Session, project_id: int) -> Optional[Project]:
    """
    Retrieve a project by primary key.

    Args:
        db: Database session.
        project_id: ID of the project.

    Returns:
        Optional[Project]: Project if found, else None.
    """
    return db.query(Project).filter(Project.id == project_id).first()


def update_project(db: Session, project_id: int, name: str, description: Optional[str]) -> Optional[Project]:
    """
    Update a project's name and description.

    Args:
        db: Database session.
        project_id: ID of the project to update.
        name: New project name.
        description: New project description (may be None).

    Returns:
        Optional[Project]: Updated project if found, else None.
    """
    db_project = get_project(db, project_id)
    if not db_project:
        return None
    db_project.name = name
    db_project.description = description
    db.commit()
    db.refresh(db_project)
    return db_project


def delete_project(db: Session, project_id: int) -> bool:
    """
    Delete a project (and all its tasks via cascade).

    Args:
        db: Database session.
        project_id: ID of the project to delete.

    Returns:
        bool: True if deleted, False if not found.
    """
    db_project = get_project(db, project_id)
    if not db_project:
        return False
    db.delete(db_project)
    db.commit()
    return True


def list_projects(
    db: Session,
    owner_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Project]:
    """
    List projects, optionally filtered by owner.

    Args:
        db: Database session.
        owner_id: If provided, filter projects by owner.
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        List[Project]: List of projects.
    """
    query = db.query(Project)
    if owner_id is not None:
        query = query.filter(Project.owner_id == owner_id)
    return query.offset(skip).limit(limit).all()


# ---------- Task CRUD ----------
def create_task(db: Session, task_data: TaskCreate) -> Task:
    """
    Create a new task.

    Args:
        db: Database session.
        task_data: Pydantic schema with task creation data.

    Returns:
        Task: The newly created Task instance.
    """
    # Map string priority to Enum
    priority_enum = Priority(task_data.priority)
    # Map string status to Enum (default todo)
    status_val = task_data.status if task_data.status else TaskStatus.TODO
    if isinstance(status_val, str):
        status_val = TaskStatus(status_val)
    db_task = Task(
        title=task_data.title,
        description=task_data.description,
        priority=priority_enum,
        status=status_val,
        due_date=task_data.due_date,
        project_id=task_data.project_id,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_task(db: Session, task_id: int) -> Optional[Task]:
    """
    Retrieve a task by primary key.

    Args:
        db: Database session.
        task_id: ID of the task.

    Returns:
        Optional[Task]: Task if found, else None.
    """
    return db.query(Task).filter(Task.id == task_id).first()


def list_tasks(
    db: Session,
    project_id: Optional[int] = None,
    priority: Optional[str] = None,
    owner_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Task]:
    """
    List tasks with optional filters and pagination.

    Args:
        db: Database session.
        project_id: Filter by project ID.
        priority: Filter by priority string.
        owner_id: If provided, restrict to tasks whose project is owned by this user.
                  This is the primary data-isolation mechanism.
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        List[Task]: List of tasks.
    """
    query = db.query(Task)

    # Data isolation: join through Project to filter by owner
    if owner_id is not None:
        query = query.join(Project, Task.project_id == Project.id).filter(
            Project.owner_id == owner_id
        )

    if project_id is not None:
        query = query.filter(Task.project_id == project_id)
    if priority is not None:
        try:
            priority_enum = Priority(priority)
            query = query.filter(Task.priority == priority_enum)
        except ValueError:
            # If invalid priority string, ignore filter
            pass
    return query.offset(skip).limit(limit).all()


def update_task(db: Session, task_id: int, task_update: TaskUpdate) -> Optional[Task]:
    """
    Update an existing task with the provided fields.

    Args:
        db: Database session.
        task_id: ID of the task to update.
        task_update: Pydantic schema with fields to update.

    Returns:
        Optional[Task]: Updated task if found, else None.
    """
    db_task = get_task(db, task_id)
    if not db_task:
        return None

    update_data = task_update.model_dump(exclude_unset=True)

    # Handle priority conversion if present
    if "priority" in update_data:
        update_data["priority"] = Priority(update_data["priority"])

    # Handle status conversion if present
    if "status" in update_data and update_data["status"] is not None:
        sv = update_data["status"]
        if isinstance(sv, str):
            update_data["status"] = TaskStatus(sv)

    # Update fields
    for key, value in update_data.items():
        setattr(db_task, key, value)

    # Manually set updated_at
    db_task.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: int) -> bool:
    """
    Delete a task by primary key.

    Args:
        db: Database session.
        task_id: ID of the task to delete.

    Returns:
        bool: True if the task was deleted, False if not found.
    """
    db_task = get_task(db, task_id)
    if not db_task:
        return False
    db.delete(db_task)
    db.commit()
    return True


# Additional utility functions for future phases (e.g., statistics, sorting, searching)

def count_tasks(db: Session, project_id: Optional[int] = None) -> int:
    """
    Count total tasks, optionally filtered by project.

    Args:
        db: Database session.
        project_id: Optional project filter.

    Returns:
        int: Number of tasks.
    """
    query = db.query(Task)
    if project_id is not None:
        query = query.filter(Task.project_id == project_id)
    return query.count()


def count_projects(db: Session, owner_id: Optional[int] = None) -> int:
    """
    Count total projects, optionally filtered by owner.

    Args:
        db: Database session.
        owner_id: Optional owner filter.

    Returns:
        int: Number of projects.
    """
    query = db.query(Project)
    if owner_id is not None:
        query = query.filter(Project.owner_id == owner_id)
    return query.count()


def count_users(db: Session) -> int:
    """
    Count total users.

    Args:
        db: Database session.

    Returns:
        int: Number of users.
    """
    return db.query(User).count()


def count_tasks_by_status(db: Session, owner_id: Optional[int] = None) -> dict:
    """
    Count tasks grouped by status, optionally filtered by project owner.

    Args:
        db: Database session.
        owner_id: If provided, count only tasks belonging to this user's projects.

    Returns:
        dict with keys 'todo', 'in_progress', 'completed'.
    """
    query = db.query(Task)
    if owner_id is not None:
        query = query.join(Project, Task.project_id == Project.id).filter(
            Project.owner_id == owner_id
        )
    counts = {"todo": 0, "in_progress": 0, "completed": 0}
    for task in query.all():
        sv = task.status.value if hasattr(task.status, "value") else str(task.status)
        if sv in counts:
            counts[sv] += 1
    return counts