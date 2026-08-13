"""
FastAPI dependencies for the TaskFlow2 application.
"""
from typing import Generator

from .database import SessionLocal


def get_db() -> Generator:
    """
    Dependency that provides a SQLAlchemy database session.

    Yields:
        Session: A SQLAlchemy session that will be closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()