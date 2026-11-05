"""Accounts: sign up, log in, who am I, and change the password.

Login follows the OAuth2 "password flow" from the FastAPI security tutorial: the email and
password go in as a form (fields username and password), the answer is a token. That is also what
the "Authorize" button on /docs uses.

Guessing passwords is slowed down (rate_limit.py), answering 429 "Too many attempts":
- at most 5 failed logins per email and IP address within 15 minutes (a success starts over);
  a wrong current password when changing it counts as a failed login too;
- at most 30 login and sign-up attempts per IP address within 15 minutes, against scripts
  that try many emails.
The visitor's address and the 429 answer come from limits.py (shared with routers/ai.py).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

import security
import users
from limits import check, client_ip
from rate_limit import RateLimit
from schemas import PasswordChange, SignupRequest, Token, UserOut
from security import CurrentUser

router = APIRouter(prefix="/auth", tags=["auth"])

WINDOW = 15 * 60  # seconds
failed_logins = RateLimit(limit=5, window=WINDOW)  # key: (IP address, email)
attempts_per_ip = RateLimit(limit=30, window=WINDOW)  # key: IP address


def _count_attempt(ip: str) -> None:
    """Every login or sign-up counts towards the per-IP limit; 429 once it is reached."""
    check(attempts_per_ip, ip)
    attempts_per_ip.hit(ip)


@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=Token)
def signup(request: SignupRequest, http: Request) -> Token:
    """Create an account and log it in straight away. 409 if the email has an account already."""
    _count_attempt(client_ip(http))
    try:
        user = users.create(request.email, security.hash_password(request.password))
    except users.EmailTakenError:
        raise HTTPException(status.HTTP_409_CONFLICT, "There is already an account with this email.") from None
    return Token(access_token=security.create_token(user))


@router.post("/login", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], http: Request) -> Token:
    """Email (in the form field "username") and password in, token out; 401 if they don't match."""
    ip = client_ip(http)
    _count_attempt(ip)
    key = (ip, users.normalize_email(form.username))
    check(failed_logins, key)  # checked before the password, so guessing stops right here
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


@router.post("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(change: PasswordChange, user: CurrentUser, http: Request) -> Response:
    """Change your password; the current one must be right (400 if not, 429 after too many tries).

    400 rather than 401: the login itself is fine, and a 401 would log the browser out.
    Logins on other devices stay valid until their token expires (7 days).
    """
    ip = client_ip(http)
    key = (ip, user.email)  # the same count as failed logins for this email
    check(failed_logins, key)
    if security.authenticate(user.email, change.current_password) is None:
        failed_logins.hit(key)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Your current password is wrong.")
    assert user.id is not None
    users.set_password_hash(user.id, security.hash_password(change.new_password))
    failed_logins.reset(key)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
