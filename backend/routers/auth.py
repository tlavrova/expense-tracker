"""Accounts: sign up, log in, and who am I.

Login follows the OAuth2 "password flow" from the FastAPI security tutorial: the email and
password go in as a form (fields username and password), the answer is a token. That is also what
the "Authorize" button on /docs uses.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

import security
import users
from schemas import SignupRequest, Token, UserOut
from security import CurrentUser

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=Token)
def signup(request: SignupRequest) -> Token:
    """Create an account and log it in straight away. 409 if the email has an account already."""
    try:
        user = users.create(request.email, security.hash_password(request.password))
    except users.EmailTakenError:
        raise HTTPException(status.HTTP_409_CONFLICT, "There is already an account with this email.") from None
    return Token(access_token=security.create_token(user))


@router.post("/login", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    """Email (in the form field "username") and password in, token out; 401 if they don't match."""
    user = security.authenticate(form.username, form.password)
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Wrong email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=security.create_token(user))


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> UserOut:
    assert user.id is not None
    return UserOut(id=user.id, email=user.email)
