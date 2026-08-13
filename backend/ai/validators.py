"""
Validation of parsed task data before insertion.
"""
from typing import Dict, Any

from pydantic import ValidationError

from ..schemas import TaskCreate
from ..crud import get_project


def validate_parsed_task(parsed: Dict[str, Any], project_id: int, db, original_text: str = "") -> TaskCreate:
    """
    Validate parsed data and ensure the target project exists.

    Args:
        parsed:        Dict returned by the AI parser with keys
                       ``title``, ``priority``, ``due_date_hint``.
        project_id:    ID of the project the task will belong to.
        db:            Active SQLAlchemy session.
        original_text: The raw user input – stored as the task description so the
                       generated task shows what the user typed instead of "No description".

    Returns:
        TaskCreate: ready to pass into ``crud.create_task()``.

    Raises:
        ValueError: if the project is not found or the parsed data is invalid.
    """
    project = get_project(db, project_id)
    if not project:
        raise ValueError("Project not found")

    title = parsed.get("title", "Untitled task")
    priority = parsed.get("priority", "medium")
    due_date_hint = parsed.get("due_date_hint")  # str or None

    # Prefer the AI-generated description; fall back to the raw user input
    generated_desc = parsed.get("description")
    if generated_desc and generated_desc.strip():
        description = generated_desc.strip()
    elif original_text and original_text.strip():
        description = original_text.strip()
    else:
        description = None

    try:
        task_data = TaskCreate(
            title=title,
            description=description,
            priority=priority,
            due_date=due_date_hint,
            project_id=project_id,
        )
    except ValidationError as exc:
        raise ValueError(f"Invalid task data: {exc}") from exc

    return task_data
