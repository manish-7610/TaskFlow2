"""
Project routes.

ALL endpoints require a valid JWT.
Every query is scoped to the currently authenticated user's projects —
no user can ever see or affect another user's data.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from ..auth import get_current_user
from ..dependencies import get_db
from ..crud import create_project, get_project, list_projects, update_project, delete_project
from ..models import Project, Task, Priority, User
from ..schemas import ProjectCreate, ProjectResponse

router = APIRouter(prefix="/projects", tags=["projects"])


# ──────────────────────────────────────────────────────────────
# CREATE PROJECT  (protected – owner injected from JWT)
# ──────────────────────────────────────────────────────────────
@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project (auth required)",
)
def create_new_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a project owned by the currently authenticated user.
    `owner_id` is never accepted from the request body.
    """
    return create_project(db, project_data, owner_id=current_user.id)


# ──────────────────────────────────────────────────────────────
# LIST PROJECTS  (protected – returns ONLY current user's projects)
# ──────────────────────────────────────────────────────────────
@router.get(
    "/",
    response_model=list[ProjectResponse],
    summary="List the current user's projects (auth required)",
)
def list_all_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns only the projects that belong to the authenticated user.
    No other user's projects are ever exposed.
    """
    return list_projects(db, owner_id=current_user.id, skip=skip, limit=limit)


# ──────────────────────────────────────────────────────────────
# PROJECT STATISTICS  (protected – scoped to current user)
# ──────────────────────────────────────────────────────────────
@router.get(
    "/statistics",
    summary="Task counts for the current user's projects (auth required)",
)
def get_project_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns each of the authenticated user's projects with task counts
    broken down by priority.  Never includes other users' data.
    """
    results = (
        db.query(
            Project.id.label("project_id"),
            Project.name.label("project_name"),
            func.count(Task.id).label("total_tasks"),
            func.coalesce(
                func.sum(case((Task.priority == Priority.LOW, 1), else_=0)), 0
            ).label("low_count"),
            func.coalesce(
                func.sum(case((Task.priority == Priority.MEDIUM, 1), else_=0)), 0
            ).label("medium_count"),
            func.coalesce(
                func.sum(case((Task.priority == Priority.HIGH, 1), else_=0)), 0
            ).label("high_count"),
        )
        .filter(Project.owner_id == current_user.id)   # ← data isolation
        .outerjoin(Task, Task.project_id == Project.id)
        .group_by(Project.id, Project.name)
        .all()
    )

    return [
        {
            "project_id": row.project_id,
            "project_name": row.project_name,
            "total_tasks": row.total_tasks,
            "priority_counts": {
                "low": row.low_count,
                "medium": row.medium_count,
                "high": row.high_count,
            },
        }
        for row in results
    ]


# ──────────────────────────────────────────────────────────────
# UPDATE PROJECT  (protected – owner only)
# ──────────────────────────────────────────────────────────────
@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update a project (auth required, owner only)",
)
def update_existing_project(
    project_id: int,
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update the name and description of a project.
    Only the owner may update their own project.
    """
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this project.")

    updated = update_project(db, project_id, name=project_data.name, description=project_data.description)
    return updated


# ──────────────────────────────────────────────────────────────
# DELETE PROJECT  (protected – owner only)
# ──────────────────────────────────────────────────────────────
@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project and all its tasks (auth required, owner only)",
)
def delete_existing_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Permanently delete a project and all tasks it contains (cascade).
    Only the owner may delete their own project.
    """
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this project.")

    delete_project(db, project_id)
    return None
