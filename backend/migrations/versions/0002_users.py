"""Accounts for the website (stage 12): the users table, and the account each expense belongs to.

Existing expenses keep an empty user_id: they stay the command-line app's own expenses.

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    with op.batch_alter_table("expenses") as batch:
        batch.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_expenses_user_id_users", "users", ["user_id"], ["id"])
        batch.create_index("ix_expenses_user_id", ["user_id"])


def downgrade() -> None:
    with op.batch_alter_table("expenses") as batch:
        batch.drop_index("ix_expenses_user_id")
        batch.drop_constraint("fk_expenses_user_id_users", type_="foreignkey")
        batch.drop_column("user_id")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
