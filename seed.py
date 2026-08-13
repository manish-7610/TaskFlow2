"""
Seed the database with sample users, projects, and tasks.
"""
import random
from datetime import datetime
from sqlalchemy.orm import Session

from backend.database import SessionLocal, engine, Base
from backend.models import User, Project, Task, Priority
from backend.crud import create_user, create_task
from backend.schemas import UserCreate, TaskCreate

# Sample data
USERS = [
    {"email": "alice@example.com", "full_name": "Alice Smith", "password": "alice123"},
    {"email": "bob@example.com", "full_name": "Bob Johnson", "password": "bob123"},
    {"email": "carol@example.com", "full_name": "Carol Williams", "password": "carol123"},
]

PROJECTS = [
    {"name": "Website Redesign", "description": "Redesign company website"},
    {"name": "Mobile App", "description": "Develop mobile application"},
    {"name": "Marketing Campaign", "description": "Q4 marketing"},
    {"name": "Data Migration", "description": "Migrate data to new system"},
    {"name": "API Development", "description": "Build public API"},
]

TASKS_TEMPLATES = [
    {"title": "Design mockups", "description": "Create wireframes", "priority": "high"},
    {"title": "Write documentation", "description": "Update API docs", "priority": "medium"},
    {"title": "Code review", "description": "Review pull requests", "priority": "low"},
    {"title": "Setup CI/CD", "description": "Configure deployment pipeline", "priority": "high"},
    {"title": "Write tests", "description": "Add unit tests", "priority": "medium"},
    {"title": "Fix bugs", "description": "Resolve reported issues", "priority": "high"},
    {"title": "Update dependencies", "description": "Bump versions", "priority": "low"},
    {"title": "Plan sprint", "description": "Plan next sprint tasks", "priority": "medium"},
    {"title": "Conduct user interviews", "description": "Gather feedback", "priority": "low"},
    {"title": "Prepare presentation", "description": "For stakeholder meeting", "priority": "high"},
]


def seed_db():
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Create users
        created_users = []
        for user_data in USERS:
            user_create = UserCreate(**user_data)
            user = create_user(db, user_create)
            created_users.append(user)
            print(f"Created user: {user.email}")

        # Create projects for each user
        created_projects = []
        for user in created_users:
            # Each user gets a subset of projects
            for proj in PROJECTS:
                project_create = ProjectCreate(
                    name=proj["name"],
                    description=proj["description"],
                    # owner_id is now injected server-side via JWT;
                    # in seed.py we write directly to the ORM
                )
                db_project = Project(
                    name=project_create.name,
                    description=project_create.description,
                    owner_id=user.id,
                )
                db.add(db_project)
                db.commit()
                db.refresh(db_project)
                project = db_project
                created_projects.append(project)
                print(f"Created project: {project.name} (owner: {user.email})")

        # Create tasks for each project
        for project in created_projects:
            # Randomly pick 3-6 tasks per project
            num_tasks = random.randint(3, 6)
            selected_templates = random.sample(TASKS_TEMPLATES, num_tasks)
            for template in selected_templates:
                due_date = None
                if random.choice([True, False]):
                    # Random due date in the future
                    day = random.randint(1, 30)
                    due_date = f"2026-{random.randint(1,12):02d}-{day:02d}"
                task_create = TaskCreate(
                    title=template["title"],
                    description=template["description"],
                    priority=template["priority"],
                    due_date=due_date,
                    project_id=project.id,
                )
                task = create_task(db, task_create)
                print(f"Created task: {task.title} (project: {project.name})")

        db.commit()
        print("Database seeding complete!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_db()