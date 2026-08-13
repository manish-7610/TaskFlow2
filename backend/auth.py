"""
Authentication utilities for TaskFlow2.

Provides:
  - hash_password()        – bcrypt hash a plain password
  - verify_password()      – check plain against hash
  - authenticate_user()    – look up user and verify password
  - create_access_token()  – mint a signed JWT
  - get_current_user()     – FastAPI dependency: decode JWT → User

NOTE: Uses bcrypt directly (not passlib) because passlib 1.7.4 is incompatible
      with bcrypt 4.x / 5.x due to a breaking API change in the bcrypt library.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .config import settings
from .dependencies import get_db
from .models import User


# ---------------------------------------------------------------------------
# Password hashing  (bcrypt directly – no passlib)
# ---------------------------------------------------------------------------

def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password with bcrypt and return the hash as a string.

    bcrypt.hashpw expects bytes; we encode and decode around it.
    """
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Return True if plain_password matches the stored bcrypt hash.

    Never call verify(hash, hash) – always pass the raw password first.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Mint a signed JWT.

    Args:
        data: Payload to encode. Typically ``{"sub": str(user_id)}``.
        expires_delta: Token lifetime. Defaults to
            ``settings.ACCESS_TOKEN_EXPIRE_MINUTES``.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


# ---------------------------------------------------------------------------
# User authentication
# ---------------------------------------------------------------------------

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Return the User if email exists and password is correct, else None.

    Args:
        db:       Active database session.
        email:    The user's email address.
        password: The plain-text password entered by the user.
    """
    from .crud import get_user_by_email  # local import avoids circular deps

    user = get_user_by_email(db, email)
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# ---------------------------------------------------------------------------
# FastAPI dependency – resolve the current user from a Bearer JWT
# ---------------------------------------------------------------------------
_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(_oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency. Decodes the Bearer JWT and returns the matching User.

    Raises HTTP 401 if the token is missing, invalid, or the user no longer
    exists in the database.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id_str: Optional[str] = payload.get("sub")
        if user_id_str is None:
            raise _CREDENTIALS_EXCEPTION
    except JWTError:
        raise _CREDENTIALS_EXCEPTION

    from .crud import get_user_by_id  # local import avoids circular deps

    user = get_user_by_id(db, int(user_id_str))
    if user is None:
        raise _CREDENTIALS_EXCEPTION
    return user
