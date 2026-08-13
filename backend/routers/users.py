"""
User routes.

POST /users  – legacy create-user endpoint (passwords are now properly hashed).
              Prefer POST /auth/register which also returns a JWT.
GET  /users  – public list endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..dependencies import get_db
from ..crud import create_user, list_users, get_user_by_email
from ..schemas import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user (legacy – prefer /auth/register)",
)
def create_new_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account.

    > **Note:** This endpoint does not return a JWT.
    > Use **POST /auth/register** to create an account *and* receive a token.

    Passwords are stored as bcrypt hashes – never in plaintext.
    """
    existing = get_user_by_email(db, user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )
    try:
        user = create_user(db, user_data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User could not be created due to duplicate email.",
        )
    return user


@router.get(
    "/",
    response_model=list[UserResponse],
    summary="List all users",
)
def list_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Return a paginated list of all users.
    """
    return list_users(db, skip=skip, limit=limit)
