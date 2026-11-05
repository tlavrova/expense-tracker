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


class BudgetAmount(BaseModel):
    """What the frontend sends to set a budget: PUT /budgets/{category}."""

    amount: float


class Budget(BudgetAmount):
    """A category's monthly budget (Budget in expense.model.ts)."""

    category: str


class MonthRow(BaseModel):
    """One category in a month: what was spent, and its budget if it has one."""

    category: str
    spent: float
    budget: float | None = None


class MonthReport(BaseModel):
    """GET /reports/month: every category with a budget or with spending that month (MonthReport in expense.model.ts)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    month: str  # YYYY-MM
    rows: list[MonthRow]
    total_spent: float
    total_budget: float


class SuggestionRequest(BaseModel):
    description: str = Field(min_length=1)


class Suggestion(BaseModel):
    category: str


class SignupRequest(BaseModel):
    """A new account; the email is checked to look like one (pydantic[email])."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class PasswordChange(BaseModel):
    """Changing the password while logged in: the current one proves it's really you."""

    current_password: str
    new_password: str = Field(min_length=8, max_length=128)  # the same rule as SignupRequest


class Token(BaseModel):
    """What sign-up and login return; the browser sends access_token back as "Bearer <token>"."""

    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    """The logged-in user (never the password hash)."""

    id: int
    email: str
