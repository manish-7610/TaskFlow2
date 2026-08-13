"""
Task routes.

ALL endpoints require a valid JWT.
Every query is scoped to the authenticated user's own projects/tasks.
No user can ever read, modify, or delete another user's tasks.

Route order matters in FastAPI – all fixed-path routes must come BEFORE
parameterised routes like /{task_id}.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..dependencies import get_db
from ..models import User
from ..crud import (
    create_task,
    get_task,
    list_tasks,
    update_task,
    delete_task,
    get_project,
    count_tasks_by_status,
)
from ..schemas import (
    TaskCreate, TaskUpdate, TaskResponse, QuickAddRequest,
    ImproveTaskRequest, ImproveTaskResponse, TaskStatusUpdate,
)

from backend.algorithms.sorting import insertion_sort
from backend.algorithms.searching import binary_search, linear_search
from backend.ai.parser import parse_task_description
from backend.ai.validators import validate_parsed_task

router = APIRouter(prefix="/tasks", tags=["Tasks"])


# ──────────────────────────────────────────────────────────────
# Internal helper – ownership guard
# ──────────────────────────────────────────────────────────────
def _require_project_ownership(
    project_id: int,
    current_user: User,
    db: Session,
) -> None:
    """
    Raises HTTP 404 if the project does not exist.
    Raises HTTP 403 if the project does not belong to *current_user*.
    """
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this project.",
        )


# ──────────────────────────────────────────────────────────────
# CREATE TASK  (protected)
# ──────────────────────────────────────────────────────────────
@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task inside one of your projects (auth required)",
)
def create_new_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_project_ownership(task_data.project_id, current_user, db)
    return create_task(db, task_data)


# ──────────────────────────────────────────────────────────────
# LIST TASKS  (protected – returns ONLY the current user's tasks)
# ──────────────────────────────────────────────────────────────
@router.get(
    "/",
    response_model=list[TaskResponse],
    summary="List your tasks (auth required)",
)
def list_all_tasks(
    project_id: int | None = None,
    priority: str | None = Query(None, pattern="^(low|medium|high)$"),
    skip: int = 0,
    limit: int = 100,
    sort: str | None = Query(None, pattern="^priority$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns tasks that belong to the authenticated user's projects only.
    Optionally filter by project_id or priority. Optionally sort by priority.
    """
    if project_id is not None:
        _require_project_ownership(project_id, current_user, db)

    tasks = list_tasks(
        db,
        project_id=project_id,
        priority=priority,
        owner_id=current_user.id,
        skip=skip,
        limit=limit,
    )

    if sort == "priority":
        priority_map = {"low": 1, "medium": 2, "high": 3}
        task_dicts = []
        for task in tasks:
            priority_value = (
                task.priority.value if hasattr(task.priority, "value") else task.priority
            )
            status_value = (
                task.status.value if hasattr(task.status, "value") else (task.status or "todo")
            )
            task_dicts.append(
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "priority": priority_value,
                    "status": status_value,
                    "priority_num": priority_map[priority_value],
                    "due_date": task.due_date,
                    "project_id": task.project_id,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at,
                }
            )
        insertion_sort(task_dicts, "priority_num")
        for item in task_dicts:
            item.pop("priority_num")
        return task_dicts

    return tasks


# ──────────────────────────────────────────────────────────────
# SEARCH  – fixed path, must be BEFORE /{task_id}
# ──────────────────────────────────────────────────────────────
@router.get(
    "/search",
    summary="Search your tasks by title (auth required)",
)
def search_task(
    title: str = Query(..., max_length=255),
    algo: str = Query("binary", pattern="^(binary|linear)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Searches only the authenticated user's own tasks.
    Supports binary search (requires sorted data) and linear search.
    """
    tasks = list_tasks(db, owner_id=current_user.id, limit=100_000)
    index = [{"id": t.id, "title": t.title} for t in tasks]

    if not index:
        raise HTTPException(status_code=404, detail="No tasks found")

    if algo == "binary":
        insertion_sort(index, "title")
        pos = binary_search(index, "title", title)
    else:
        pos = linear_search(index, "title", title)

    if pos == -1:
        raise HTTPException(status_code=404, detail="Task not found")

    return index[pos]


# ──────────────────────────────────────────────────────────────
# STATUS COUNTS  – fixed path, must be BEFORE /{task_id}
# ──────────────────────────────────────────────────────────────
@router.get(
    "/status-counts",
    summary="Get todo/in_progress/completed counts for current user (auth required)",
)
def get_status_counts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns task counts grouped by status for the authenticated user."""
    return count_tasks_by_status(db, owner_id=current_user.id)


# ──────────────────────────────────────────────────────────────
# AI QUICK ADD  – fixed path, must be BEFORE /{task_id}
# ──────────────────────────────────────────────────────────────
@router.post(
    "/quick-add",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="AI quick-add a task (auth required)",
)
def quick_add_task(
    request: QuickAddRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Parse a natural-language description and create the task automatically.
    The target project must belong to the authenticated user.
    """
    _require_project_ownership(request.project_id, current_user, db)

    parsed = parse_task_description(request.text)
    try:
        task_data = validate_parsed_task(parsed, request.project_id, db, original_text=request.text)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return create_task(db, task_data)


# ──────────────────────────────────────────────────────────────
# AI IMPROVE TASK  – fixed path, must be BEFORE /{task_id}
# ──────────────────────────────────────────────────────────────
@router.post(
    "/improve",
    response_model=ImproveTaskResponse,
    summary="AI-improve an existing task's title/description/priority (auth required)",
)
def improve_task(
    request: ImproveTaskRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Reuses the existing mock_parser to generate a better title, description,
    and priority suggestion for an existing task.  Does NOT write to the DB —
    the caller decides whether to apply the suggestions via PUT /{task_id}.
    """
    # Build input: combine title + description for richer context
    input_text = request.title.strip()
    if request.description and request.description.strip():
        input_text = f"{input_text}. {request.description.strip()}"

    parsed = parse_task_description(input_text)

    # Priority: use parsed suggestion; fall back to existing priority
    suggested_priority = parsed.get("priority") or request.priority or "medium"

    # Due date: use parsed hint if found; otherwise preserve the existing one
    suggested_due = parsed.get("due_date_hint") or request.due_date

    return ImproveTaskResponse(
        title=parsed.get("title") or request.title,
        description=parsed.get("description"),
        priority=suggested_priority,
        due_date=suggested_due,
    )


# ──────────────────────────────────────────────────────────────
# GET SINGLE TASK  – parameterised, must come AFTER all fixed paths
# ──────────────────────────────────────────────────────────────
@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a specific task (auth required)",
)
def get_task_by_id(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    _require_project_ownership(task.project_id, current_user, db)
    return task


# ──────────────────────────────────────────────────────────────
# UPDATE  (protected – ownership verified)
# ──────────────────────────────────────────────────────────────
@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update a task (auth required)",
)
def update_existing_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Only the owner of the project this task belongs to may update it.
    If project_id is changing, the new project must also be owned by the user.
    """
    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    _require_project_ownership(task.project_id, current_user, db)

    if task_update.project_id is not None and task_update.project_id != task.project_id:
        _require_project_ownership(task_update.project_id, current_user, db)

    return update_task(db, task_id, task_update)


# ──────────────────────────────────────────────────────────────
# PATCH STATUS  (protected – ownership verified)
# ──────────────────────────────────────────────────────────────
@router.patch(
    "/{task_id}/status",
    response_model=TaskResponse,
    summary="Update only the status of a task (auth required)",
)
def patch_task_status(
    task_id: int,
    status_update: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lightweight endpoint to change just the task status.
    Only the project owner may update it.
    """
    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    _require_project_ownership(task.project_id, current_user, db)
    return update_task(db, task_id, TaskUpdate(status=status_update.status))


# ──────────────────────────────────────────────────────────────
# DELETE  (protected – ownership verified)
# ──────────────────────────────────────────────────────────────
@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task (auth required)",
)
def delete_existing_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Only the owner of the project this task belongs to may delete it.
    """
    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    _require_project_ownership(task.project_id, current_user, db)

    delete_task(db, task_id)
    return None
