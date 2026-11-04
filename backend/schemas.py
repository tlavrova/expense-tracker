"""The JSON shapes the API accepts and returns (Pydantic models).

They match the TypeScript types in frontend/src/app/expenses/expense.model.ts.
"""

from __future__ import annotations

import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic.alias_generators import to_camel


class NewExpense(BaseModel):
    """What the frontend sends to add an expense (NewExpense in expense.model.ts)."""

    amount: float
    category: str
    description: str
    date: datetime.date  # "YYYY-MM-DD" in JSON
    frequency: str | None = None  # weekly/monthly/yearly; empty for a one-off expense


class ExpenseOut(NewExpense):
    """A saved expense (Expense in expense.model.ts)."""

    id: int


class Summary(BaseModel):
    """Summary in expense.model.ts; the JSON keys are camelCase, as TypeScript expects."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    totals_by_category: dict[str, float]
    total: float


class SuggestionRequest(BaseModel):
    description: str = Field(min_length=1)


class Suggestion(BaseModel):
    category: str


class SignupRequest(BaseModel):
    """A new account; the email is checked to look like one (pydantic[email])."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class Token(BaseModel):
    """What sign-up and login return; the browser sends access_token back as "Bearer <token>"."""

    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    """The logged-in user (never the password hash)."""

    id: int
    email: str
