"""The AI endpoint: Gemini's category suggestion for an expense description (ai_helper.py).

Login is required, so strangers can't use up the Gemini free-tier quota, and each account may ask
at most 20 times an hour (429 "Too many AI suggestions" above that), so one account can't use it
up for everyone. The count is kept in memory (rate_limit.py): it starts over when the API restarts.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

import ai_helper
from limits import check
from rate_limit import RateLimit
from schemas import Suggestion, SuggestionRequest
from security import CurrentUser

router = APIRouter(tags=["ai"])

suggestions_per_user = RateLimit(limit=20, window=60 * 60)  # key: user id


@router.post("/suggest-category", response_model=Suggestion)
def suggest_category(request: SuggestionRequest, user: CurrentUser) -> Suggestion:
    """Gemini's category for a description; 503 with the reason when the AI isn't available."""
    check(suggestions_per_user, user.id, "AI suggestions")
    suggestions_per_user.hit(user.id)  # every question counts, answered or not: each one asks Gemini
    try:
        return Suggestion(category=ai_helper.suggest_category(request.description))
    except ai_helper.AIUnavailableError as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from None
