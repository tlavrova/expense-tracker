"""The database connection and its tables (SQLModel).

Which database comes from the DATABASE_URL environment variable:
  not set                          SQLite file expenses.db next to this file (on your Mac)
  postgresql://user:pass@host/db   Postgres (online, stage 13; needs a Postgres driver then)

SQL_ECHO=1 prints every SQL statement SQLModel sends, to see what the query builder produces.

Only the connection and the table classes live here (Alembic will read the tables from this
module); the queries are in storage.py.
"""

from __future__ import annotations

import functools
import os
from contextlib import contextmanager
from datetime import date as Date
from pathlib import Path
from typing import Iterator

from sqlalchemy import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Field, Session, SQLModel, create_engine

DEFAULT_DB_PATH = Path(__file__).parent / "expenses.db"


class StorageError(Exception):
    """Raised when the database can't be read or written, or holds invalid data."""


class ExpenseRow(SQLModel, table=True):
    """One expense in the "expenses" table. frequency is empty for one-off expenses."""

    __tablename__ = "expenses"

    id: int | None = Field(default=None, primary_key=True)
    amount: float
    category: str = Field(index=True)
    description: str
    date: Date = Field(index=True)
    frequency: str | None = None


def database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        return f"sqlite:///{DEFAULT_DB_PATH}"
    # Some hosts hand out "postgres://", which SQLAlchemy doesn't accept.
    if url.startswith("postgres://"):
        url = "postgresql://" + url.removeprefix("postgres://")
    return url


@functools.lru_cache(maxsize=1)
def get_engine(url: str | None = None) -> Engine:
    """Connect to the database (once) and create the table if it isn't there yet."""
    url = url or database_url()
    # SQLite allows one thread per connection by default; the API (stage 9) uses several.
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    try:
        echo = os.environ.get("SQL_ECHO", "").strip() == "1"
        engine = create_engine(url, connect_args=connect_args, echo=echo)
        SQLModel.metadata.create_all(engine)
    except SQLAlchemyError as error:
        raise StorageError(f"Can't open the database: {_short(error)}") from error
    return engine


@contextmanager
def open_session(action: str, engine: Engine | None = None) -> Iterator[Session]:
    """A database session; any database error becomes StorageError("Can't <action>: ...").

    ValueError counts too: it means a row holds data the models reject.
    """
    try:
        with Session(engine or get_engine()) as session:
            yield session
    except (SQLAlchemyError, ValueError) as error:
        raise StorageError(f"Can't {action}: {_short(error)}") from error


def _short(error: Exception) -> str:
    """First line only: SQLAlchemy adds the SQL and its values below it (the log keeps it all)."""
    return str(error).splitlines()[0]
