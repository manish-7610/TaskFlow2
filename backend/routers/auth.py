"""
Authentication routes for TaskFlow2.

  POST /auth/register  – create account, returns JWT
  POST /auth/login     – exchange credentials for JWT
  GET  /auth/me        – return the currently authenticated user's profile
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..auth import authenticate_user, create_access_token, get_current_user
from ..crud import create_user, get_user_by_email
from ..dependencies import get_db
from ..models import User
from ..schemas import UserCreate, UserResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


# --------------------------------------------------------------------------
# POST /auth/register
# --------------------------------------------------------------------------
@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account.

    - Password is **always** stored as a bcrypt hash – never plaintext.
    - Returns a JWT `access_token` immediately so the caller is logged in.
    """
    if get_user_by_email(db, user_data.email):
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
            detail="User could not be created due to a duplicate email.",
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=access_token, token_type="bearer")


# --------------------------------------------------------------------------
# POST /auth/login
# --------------------------------------------------------------------------
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Obtain a JWT access token",
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Exchange **email + password** for a JWT access token.

    Swagger UI uses the OAuth2 *password* flow:
    - **username** field → your email address
    - **password** field → your password
    """
    user = authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=access_token, token_type="bearer")


# --------------------------------------------------------------------------
# GET /auth/me
# --------------------------------------------------------------------------
@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user",
)
def me(current_user: User = Depends(get_current_user)):
    """
    Returns the profile of the user whose Bearer token is in the
    `Authorization` header.
    """
    return current_user
