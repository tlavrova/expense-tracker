"""Accounts: sign up, log in, and who am I.

Login follows the OAuth2 "password flow" from the FastAPI security tutorial: the email and
password go in as a form (fields username and password), the answer is a token. That is also what
the "Authorize" button on /docs uses.

Guessing passwords is slowed down (rate_limit.py), answering 429 "Too many attempts":
- at most 5 failed logins per email and IP address within 15 minutes (a success starts over);
- at most 30 login and sign-up attempts per IP address within 15 minutes, against scripts
  that try many emails.
Behind a hosting service's proxy, uvicorn must be told which addresses are that proxy
(FORWARDED_ALLOW_IPS, see the README); otherwise every visitor looks like the proxy. Never "*":
then uvicorn believes the first X-Forwarded-For entry, which the visitor can make up.
"""

from __future__ import annotations

import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

import security
import users
from rate_limit import RateLimit, TooManyAttempts
from schemas import SignupRequest, Token, UserOut
from security import CurrentUser

router = APIRouter(prefix="/auth", tags=["auth"])

WINDOW = 15 * 60  # seconds
failed_logins = RateLimit(limit=5, window=WINDOW)  # key: (IP address, email)
attempts_per_ip = RateLimit(limit=30, window=WINDOW)  # key: IP address


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _too_many(error: TooManyAttempts) -> HTTPException:
    minutes = math.ceil(error.retry_after / 60)
    return HTTPException(
        status.HTTP_429_TOO_MANY_REQUESTS,
        f"Too many attempts. Try again in {minutes} minute{'s' if minutes != 1 else ''}.",
        headers={"Retry-After": str(error.retry_after)},
    )


def _count_attempt(ip: str) -> None:
    """Every login or sign-up counts towards the per-IP limit; 429 once it is reached."""
    try:
        attempts_per_ip.check(ip)
    except TooManyAttempts as error:
        raise _too_many(error) from None
    attempts_per_ip.hit(ip)


@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=Token)
def signup(request: SignupRequest, http: Request) -> Token:
    """Create an account and log it in straight away. 409 if the email has an account already."""
    _count_attempt(_client_ip(http))
    try:
        user = users.create(request.email, security.hash_password(request.password))
    except users.EmailTakenError:
        raise HTTPException(status.HTTP_409_CONFLICT, "There is already an account with this email.") from None
    return Token(access_token=security.create_token(user))


@router.post("/login", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], http: Request) -> Token:
    """Email (in the form field "username") and password in, token out; 401 if they don't match."""
    ip = _client_ip(http)
    _count_attempt(ip)
    key = (ip, users.normalize_email(form.username))
    try:
        failed_logins.check(key)  # checked before the password, so guessing stops right here
    except TooManyAttempts as error:
        raise _too_many(error) from None
    user = security.authenticate(form.username, form.password)
    if user is None:
        failed_logins.hit(key)
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Wrong email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    failed_logins.reset(key)
    return Token(access_token=security.create_token(user))


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> UserOut:
    assert user.id is not None
    return UserOut(id=user.id, email=user.email)
