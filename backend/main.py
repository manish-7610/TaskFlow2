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


# ─────────────────────────────────────────────────────────────────────────────
# Create all database tables on startup
# ─────────────────────────────────────────────────────────────────────────────

Base.metadata.create_all(bind=engine)


# ─────────────────────────────────────────────────────────────────────────────
# Safe migration: add 'status' column if it doesn't exist
# ─────────────────────────────────────────────────────────────────────────────

def _migrate_add_status_column():
    """
    Backward-compatible migration.

    SQLite:
        Uses PRAGMA to detect the missing column.

    MySQL / PostgreSQL:
        Attempts to detect the missing column.

    If the table or column already exists, nothing is changed.
    """

    import sqlalchemy

    url = str(settings.DATABASE_URL).lower()

    with engine.connect() as conn:
        try:

            if "sqlite" in url:

                result = conn.execute(
                    sqlalchemy.text("PRAGMA table_info(tasks)")
                )

                columns = [
                    row[1]
                    for row in result.fetchall()
                ]

                if "status" not in columns:

                    conn.execute(
                        sqlalchemy.text(
                            "ALTER TABLE tasks "
                            "ADD COLUMN status VARCHAR(20) "
                            "NOT NULL DEFAULT 'todo'"
                        )
                    )

                    conn.commit()

            else:

                # MySQL / PostgreSQL compatibility check
                result = conn.execute(
                    sqlalchemy.text(
                        "SELECT COLUMN_NAME "
                        "FROM INFORMATION_SCHEMA.COLUMNS "
                        "WHERE TABLE_SCHEMA = DATABASE() "
                        "AND TABLE_NAME = 'tasks' "
                        "AND COLUMN_NAME = 'status'"
                    )
                )

                if result.fetchone() is None:

                    conn.execute(
                        sqlalchemy.text(
                            "ALTER TABLE tasks "
                            "ADD COLUMN status VARCHAR(20) "
                            "NOT NULL DEFAULT 'todo'"
                        )
                    )

                    conn.commit()

        except Exception:
            # create_all() will handle a fresh database/table.
            pass


_migrate_add_status_column()


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI application
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    swagger_ui_parameters={
        "persistAuthorization": True
    },
)


# ─────────────────────────────────────────────────────────────────────────────
# Logging Middleware
# ─────────────────────────────────────────────────────────────────────────────

app.add_middleware(LoggingMiddleware)


# ─────────────────────────────────────────────────────────────────────────────
# CORS Configuration
# ─────────────────────────────────────────────────────────────────────────────

# Local development + production Netlify frontend
ALLOWED_ORIGINS = [
    # Local development
    "http://localhost:3000",
    "http://127.0.0.1:3000",

    "http://localhost:5500",
    "http://127.0.0.1:5500",

    "http://localhost:5173",
    "http://127.0.0.1:5173",

    "http://localhost:8000",
    "http://127.0.0.1:8000",

    # Production frontend
    "https://taskflow2-manish.netlify.app",
]


# In DEBUG mode, keep the existing development behavior.
if settings.cors_allow_all:

    app.add_middleware(
        CORSMiddleware,

        allow_origins=["*"],

        allow_credentials=False,

        allow_methods=["*"],

        allow_headers=["*"],
    )

else:

    app.add_middleware(
        CORSMiddleware,

        allow_origins=ALLOWED_ORIGINS,

        allow_credentials=True,

        allow_methods=["*"],

        allow_headers=["*"],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Routers
# ─────────────────────────────────────────────────────────────────────────────

app.include_router(
    auth_router.router
)

app.include_router(
    users.router
)

app.include_router(
    projects.router
)

app.include_router(
    tasks.router
)


# ─────────────────────────────────────────────────────────────────────────────
# Root / Health
# ─────────────────────────────────────────────────────────────────────────────

@app.get(
    "/",
    status_code=status.HTTP_200_OK,
    tags=["health"]
)
def root():

    return {
        "message": "Welcome to TaskFlow2 API",
        "version": settings.APP_VERSION,
    }


@app.get(
    "/health",
    status_code=status.HTTP_200_OK,
    tags=["health"]
)
def health_check():

    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
    }