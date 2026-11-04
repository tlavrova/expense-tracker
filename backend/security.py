"""Passwords and login tokens for the API.

- Passwords are hashed with argon2 (pwdlib), so the database never holds a password, only a hash
  that can check one.
- After login the browser gets a token (a JWT): it says which user this is and until when, and
  it is signed with JWT_SECRET, so nobody can make or change one without that secret.
- current_user() is the FastAPI dependency every protected endpoint uses.

JWT_SECRET comes from the environment, never from the code (see README). The API refuses to start
without it; the command-line app doesn't need it.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

import users
from database import UserRow

ALGORITHM = "HS256"
TOKEN_LIFETIME = timedelta(days=7)  # then the user logs in again
MIN_SECRET_LENGTH = 32

password_hash = PasswordHash.recommended()  # argon2
# Compared against when the email is unknown, so a wrong email takes as long as a wrong password
# and the timing doesn't reveal which emails have accounts.
_DUMMY_HASH = password_hash.hash("not a real password")

# Where /docs' "Authorize" button sends the email and password.
# auto_error=False: a missing token gets our own "Please log in." instead of FastAPI's wording.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


class MissingSecretError(RuntimeError):
    """JWT_SECRET is not set, or too short to be safe."""


def jwt_secret() -> str:
    secret = os.environ.get("JWT_SECRET", "").strip()
    if len(secret) < MIN_SECRET_LENGTH:
        raise MissingSecretError(
            f"JWT_SECRET must be set to a random value of at least {MIN_SECRET_LENGTH} characters. "
            'Make one with: python -c "import secrets; print(secrets.token_urlsafe(32))"'
        )
    return secret


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def authenticate(email: str, password: str) -> UserRow | None:
    """The user, if the email and password match; otherwise None (without saying which was wrong)."""
    user = users.find_by_email(email)
    if user is None:
        password_hash.verify(password, _DUMMY_HASH)
        return None
    return user if password_hash.verify(password, user.password_hash) else None


def create_token(user: UserRow, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    claims = {"sub": str(user.id), "iat": now, "exp": now + TOKEN_LIFETIME}
    return jwt.encode(claims, jwt_secret(), algorithm=ALGORITHM)


def _not_logged_in(detail: str) -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED, detail, headers={"WWW-Authenticate": "Bearer"}
    )


def current_user(token: Annotated[str | None, Depends(oauth2_scheme)]) -> UserRow:
    """The logged-in user from the request's "Authorization: Bearer <token>" header; else 401."""
    if not token:
        raise _not_logged_in("Please log in.")
    try:
        claims = jwt.decode(token, jwt_secret(), algorithms=[ALGORITHM], options={"require": ["exp", "sub"]})
        user_id = int(claims["sub"])
    except jwt.ExpiredSignatureError:
        raise _not_logged_in("Your login has expired. Please log in again.") from None
    except (jwt.InvalidTokenError, ValueError):
        raise _not_logged_in("Please log in.") from None
    user = users.get(user_id)
    if user is None or user.id is None:  # the account was deleted
        raise _not_logged_in("Please log in.")
    # Never None from here on: storage treats owner=None as the command-line app's expenses.
    return user


CurrentUser = Annotated[UserRow, Depends(current_user)]
"""Use as a parameter type in an endpoint to require login and get the user."""
