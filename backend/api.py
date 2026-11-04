"""REST API for the Angular frontend (stage 9): the same data and rules as the command-line app.

Run it from backend/:  uvicorn api:app --reload   (docs at http://localhost:8000/docs)

Every request reads the database through storage.py; nothing is kept in memory between
requests. The amount, date and frequency rules live in models.py, so the API and the CLI accept
exactly the same expenses. The Gemini key stays here on the server and never reaches the browser.
Every error answer has the same shape, {"detail": "a readable message"}, so the frontend can show it.
uvicorn logs each request, so the endpoints don't use @log_action.
"""

from __future__ import annotations

import datetime
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

import ai_helper
import storage
from models import Expense, ExpenseTracker, RecurringExpense

# Where the Angular dev server runs (npm start). The deployed site is added in stage 13.
ALLOWED_ORIGINS = ["http://localhost:4200"]


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    storage.import_json()  # the same one-time move of expenses.json as the CLI; opens the database
    yield


app = FastAPI(title="Expense Tracker API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(storage.StorageError)
def storage_error(request: Request, error: storage.StorageError) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": str(error)})


@app.exception_handler(RequestValidationError)
def validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
    """FastAPI's own checks (types, query patterns) as one readable string, like our own errors."""
    messages = [f"{problem['loc'][-1]}: {problem['msg']}" for problem in error.errors()]
    return JSONResponse(status_code=422, content={"detail": "; ".join(messages)})


def to_out(expense: Expense) -> ExpenseOut:
    assert expense.id is not None  # everything here came from the database
    return ExpenseOut(
        id=expense.id,
        amount=expense.amount,
        category=expense.category,
        description=expense.description,
        date=expense.date,
        frequency=getattr(expense, "frequency", None),
    )


@app.get("/expenses", response_model=list[ExpenseOut], response_model_exclude_none=True)
def list_expenses(
    category: str | None = None,
    month: str | None = Query(None, description="YYYY-MM", examples=["2026-11"]),
    sort: Literal["amount", "date"] | None = None,
) -> list[ExpenseOut]:
    """All expenses in the order added; optionally only one category and/or month, and sorted."""
    tracker = storage.load()
    if category:
        tracker = ExpenseTracker(tracker.filter_by_category(category))
    if month:
        try:
            first_day = datetime.datetime.strptime(month, "%Y-%m")
        except ValueError:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, "month must be YYYY-MM, for example 2026-11."
            ) from None
        tracker = ExpenseTracker(list(tracker.expenses_in_month(first_day.year, first_day.month)))
    return [to_out(expense) for expense in tracker.sorted_by(sort)]


@app.post(
    "/expenses",
    status_code=status.HTTP_201_CREATED,
    response_model=ExpenseOut,
    response_model_exclude_none=True,
)
def add_expense(new: NewExpense) -> ExpenseOut:
    """Save an expense. The same rules as the CLI apply; breaking one gives 422 with the reason."""
    try:
        if new.frequency:
            expense: Expense = RecurringExpense(
                new.amount, new.category, new.description, new.date, new.frequency.strip().lower()
            )
        else:
            expense = Expense(new.amount, new.category, new.description, new.date)
    except ValueError as error:  # InvalidAmountError is a ValueError too
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from None
    return to_out(storage.add(expense))


@app.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int) -> Response:
    if not storage.delete(expense_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No expense with id {expense_id}.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/summary", response_model=Summary, response_model_by_alias=True)
def summary() -> Summary:
    """Totals per category (added up by the database) and the overall total."""
    totals = storage.totals_by_category()
    return Summary(totals_by_category=totals, total=sum(totals.values()))


@app.post("/suggest-category", response_model=Suggestion)
def suggest_category(request: SuggestionRequest) -> Suggestion:
    """Gemini's category for a description; 503 with the reason when the AI isn't available."""
    try:
        return Suggestion(category=ai_helper.suggest_category(request.description))
    except ai_helper.AIUnavailableError as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from None
