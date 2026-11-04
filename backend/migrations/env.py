"""How Alembic connects: the app's own database and table classes (database.py).

No logging setup here on purpose: the CLI and the API configure logging themselves.
"""

from alembic import context
from sqlmodel import SQLModel, create_engine

import database  # noqa: F401  (registers the table classes on SQLModel.metadata)

config = context.config
target_metadata = SQLModel.metadata


def run(connection) -> None:
    # render_as_batch: SQLite can't change a table in place (for example add a foreign key), so
    # Alembic copies the table instead; on Postgres it changes it directly.
    context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():  # alembic upgrade head --sql: print the SQL instead of running it
    context.configure(url=database.database_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
elif (connection := config.attributes.get("connection")) is not None:
    run(connection)  # called from database.migrate() with the app's connection
else:
    with create_engine(database.database_url()).begin() as connection:  # the alembic command
        run(connection)
