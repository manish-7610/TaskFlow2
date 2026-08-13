"""
FastAPI application entry point for TaskFlow2.
"""
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import engine, Base
from .middleware import LoggingMiddleware
from .routers import users, projects, tasks
from .routers import auth as auth_router

# Create all database tables on startup (idempotent)
Base.metadata.create_all(bind=engine)

# ── Safe migration: add 'status' column if it doesn't exist ─────────────────
def _migrate_add_status_column():
    """
    Backward-compatible migration.
    For SQLite: uses PRAGMA to detect missing column.
    For MySQL:  uses INFORMATION_SCHEMA to detect missing column.
    Falls through silently if the column already exists or the table
    doesn't exist yet (create_all handles that case).
    """
    import sqlalchemy
    url = str(settings.DATABASE_URL).lower()
    with engine.connect() as conn:
        try:
            if "sqlite" in url:
                result = conn.execute(sqlalchemy.text("PRAGMA table_info(tasks)"))
                columns = [row[1] for row in result.fetchall()]
                if "status" not in columns:
                    conn.execute(sqlalchemy.text(
                        "ALTER TABLE tasks ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'todo'"
                    ))
                    conn.commit()
            else:
                # MySQL / PostgreSQL – check information_schema
                result = conn.execute(sqlalchemy.text(
                    "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                    "WHERE TABLE_SCHEMA = DATABASE() "
                    "AND TABLE_NAME = 'tasks' "
                    "AND COLUMN_NAME = 'status'"
                ))
                if result.fetchone() is None:
                    conn.execute(sqlalchemy.text(
                        "ALTER TABLE tasks ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'todo'"
                    ))
                    conn.commit()
        except Exception:
            # Table doesn't exist yet – create_all will build it fresh
            pass

_migrate_add_status_column()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    swagger_ui_parameters={"persistAuthorization": True},
)

# ── Middleware ──────────────────────────────────────────────────────────────
app.add_middleware(LoggingMiddleware)

# CORS: open to all origins in DEBUG mode, restricted in production
if settings.cors_allow_all:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,   # credentials=False required when allow_origins=["*"]
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ── Routers ─────────────────────────────────────────────────────────────────
app.include_router(auth_router.router)   # /auth/register, /auth/login, /auth/me
app.include_router(users.router)         # /users
app.include_router(projects.router)      # /projects
app.include_router(tasks.router)         # /tasks


# ── Root / Health ────────────────────────────────────────────────────────────
@app.get("/", status_code=status.HTTP_200_OK, tags=["health"])
def root():
    return {"message": "Welcome to TaskFlow2 API", "version": settings.APP_VERSION}


@app.get("/health", status_code=status.HTTP_200_OK, tags=["health"])
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
    }
