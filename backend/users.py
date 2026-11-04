"""Accounts for the website: create one, and find one by email or id.

Passwords never reach the database: only security.hash_password()'s hash is stored.
"""

from __future__ import annotations

from sqlalchemy import Engine
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

import database
from database import UserRow


class EmailTakenError(Exception):
    """An account with this email exists already."""


def normalize_email(email: str) -> str:
    """Emails are matched without regard to case or surrounding spaces."""
    return email.strip().lower()


def create(email: str, password_hash: str, engine: Engine | None = None) -> UserRow:
    """Save a new account. Raises EmailTakenError if the email is in use."""
    row = UserRow(email=normalize_email(email), password_hash=password_hash)
    try:
        with database.open_session("create the account", engine) as session:
            session.add(row)
            session.commit()
            session.refresh(row)
    except database.StorageError as error:
        if isinstance(error.__cause__, IntegrityError):  # the unique index on email
            raise EmailTakenError(email) from None
        raise
    return row


def find_by_email(email: str, engine: Engine | None = None) -> UserRow | None:
    with database.open_session("read the account", engine) as session:
        statement = select(UserRow).where(UserRow.email == normalize_email(email))
        return session.exec(statement).first()


def get(user_id: int, engine: Engine | None = None) -> UserRow | None:
    with database.open_session("read the account", engine) as session:
        return session.get(UserRow, user_id)
