"""The database connection: which database, connecting once, migrations, and sessions.

Which database comes from the DATABASE_URL environment variable:
  not set                          SQLite file expenses.db next to this file (on your Mac)
  postgresql://user:pass@host/db   Postgres (online, stage 13), through the psycopg driver

SQL_ECHO=1 prints every SQL statement SQLModel sends, to see what the query builder produces.

The table classes are in tables.py; the queries are in storage.py (expenses), reports.py
(totals), users.py (accounts) and budgets.py (budgets).

The tables are created and changed by Alembic migrations (migrations/versions/), which run by
themselves when the app connects, so an older expenses.db is upgraded on its first start.
"""

from __future__ import annotations

import functools
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, Engine, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, create_engine

DEFAULT_DB_PATH = Path(__file__).parent / "expenses.db"
MIGRATIONS_DIR = Path(__file__).parent / "migrations"
# The first migration creates the expenses table exactly as stage 8a's create_all() did.
FIRST_REVISION = "0001"


class StorageError(Exception):
    """Raised when the database can't be read or written, or holds invalid data."""


def database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        return f"sqlite:///{DEFAULT_DB_PATH}"
    # Hosts hand out "postgres://" or "postgresql://"; SQLAlchemy needs the driver named (psycopg 3).
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url.removeprefix(prefix)
    return url


@functools.lru_cache(maxsize=1)
def get_engine(url: str | None = None) -> Engine:
    """Connect to the database (once) and bring its tables up to date (Alembic migrations)."""
    url = url or database_url()
    # SQLite allows one thread per connection by default; the API (stage 9) uses several.
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    try:
        echo = os.environ.get("SQL_ECHO", "").strip() == "1"
        # pool_pre_ping: a hosted Postgres that sleeps when idle (Neon) closes our open
        # connections; check each one before use and reconnect instead of failing the request.
        engine = create_engine(url, connect_args=connect_args, echo=echo, pool_pre_ping=True)
        migrate(engine)
    except SQLAlchemyError as error:
        raise StorageError(f"Can't open the database: {_short(error)}") from error
    return engine


def alembic_config(connection: Connection | None = None) -> Config:
    """Alembic settings in code; migrations/env.py uses the connection passed here, if any."""
    config = Config(str(Path(__file__).parent / "alembic.ini"))
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.attributes["connection"] = connection
    return config


def migrate(engine: Engine) -> None:
    """Run the migrations this database hasn't had yet.

    A database made by stage 8a has the expenses table but no record of migrations
    (alembic_version), so it is first marked as being at the first migration.
    """
    with engine.begin() as connection:
        config = alembic_config(connection)
        tables = inspect(connection).get_table_names()
        if "expenses" in tables and "alembic_version" not in tables:
            command.stamp(config, FIRST_REVISION)
        command.upgrade(config, "head")


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
