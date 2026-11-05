"""Migrations: new databases, databases from stage 8a, and the old expenses.json import."""

import json
import sqlite3

import pytest
from alembic import command
from sqlalchemy import create_engine, inspect, text

import database
import json_import
import storage
from models import Expense


def test_a_new_database_gets_every_table_at_the_latest_migration(tmp_path):
    engine = database.get_engine(f"sqlite:///{tmp_path / 'new.db'}")
    assert set(inspect(engine).get_table_names()) == {"alembic_version", "expenses", "users"}
    with engine.connect() as connection:
        assert connection.execute(text("select version_num from alembic_version")).scalar() == "0002"


def test_a_stage_8a_database_is_upgraded_and_keeps_its_expenses(tmp_path):
    path = tmp_path / "old.db"
    with sqlite3.connect(path) as old:  # what stage 8a's create_all() made: no alembic_version
        old.executescript(
            """
            CREATE TABLE expenses (id INTEGER PRIMARY KEY, amount FLOAT NOT NULL,
              category VARCHAR NOT NULL, description VARCHAR NOT NULL, date DATE NOT NULL,
              frequency VARCHAR);
            CREATE INDEX ix_expenses_category ON expenses (category);
            CREATE INDEX ix_expenses_date ON expenses (date);
            INSERT INTO expenses VALUES (1, 12, 'food', 'Lunch', '2026-11-02', NULL);
            INSERT INTO expenses VALUES (2, 900, 'housing', 'Rent', '2026-10-01', 'monthly');
            """
        )
    engine = database.get_engine(f"sqlite:///{path}")
    columns = [c["name"] for c in inspect(engine).get_columns("expenses")]
    assert "user_id" in columns
    kept = storage.load(owner=storage.LOCAL, engine=engine)
    assert [e.description for e in kept.expenses] == ["Lunch", "Rent"]  # now the CLI's own


def test_the_migrations_match_the_table_classes(tmp_path):
    engine = database.get_engine(f"sqlite:///{tmp_path / 'check.db'}")
    with engine.begin() as connection:
        command.check(database.alembic_config(connection))  # raises if a table class has changed


def test_downgrade_and_upgrade_again(tmp_path):
    engine = database.get_engine(f"sqlite:///{tmp_path / 'down.db'}")
    with engine.begin() as connection:
        command.downgrade(database.alembic_config(connection), "0001")
    assert "users" not in inspect(create_engine(engine.url)).get_table_names()
    database.migrate(engine)
    assert "users" in inspect(create_engine(engine.url)).get_table_names()


def write_json(path, items):
    path.write_text(json.dumps(items), encoding="utf-8")
    return path


def test_json_is_imported_once_into_an_empty_database(tmp_path):
    path = write_json(
        tmp_path / "expenses.json",
        [{"amount": 12.5, "category": "Food", "description": "lunch", "date": "2025-12-30"},
         {"amount": 800, "category": "housing", "description": "rent", "date": "2026-01-01", "frequency": "monthly"}],
    )
    assert json_import.import_json(path) == 2
    assert not path.exists() and (tmp_path / "expenses.json.imported").exists()
    assert [e.category for e in storage.load(owner=storage.LOCAL).expenses] == ["food", "housing"]


def test_json_is_not_imported_into_a_database_with_expenses(tmp_path):
    storage.add(Expense(3, "food", "Coffee", "2026-11-01"), owner=storage.LOCAL)
    path = write_json(tmp_path / "expenses.json", [{"amount": 1, "category": "x", "description": "y", "date": "2026-01-01"}])
    assert json_import.import_json(path) == 0
    assert path.exists()
    assert len(storage.load(owner=storage.LOCAL)) == 1


def test_a_broken_json_file_is_reported(tmp_path):
    path = tmp_path / "expenses.json"
    path.write_text("[not json", encoding="utf-8")
    with pytest.raises(storage.StorageError, match="Can't read"):
        json_import.import_json(path)


@pytest.mark.parametrize("given", ["postgres://u:p@host/db", "postgresql://u:p@host/db"])
def test_a_postgres_url_uses_the_psycopg_driver(monkeypatch, given):
    monkeypatch.setenv("DATABASE_URL", given)
    assert database.database_url() == "postgresql+psycopg://u:p@host/db"


def test_a_url_that_names_its_driver_is_kept(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@host/db")
    assert database.database_url() == "postgresql+psycopg://u:p@host/db"
