"""The AI endpoint: Gemini's category suggestion for an expense description (ai_helper.py).

Login is required, so strangers can't use up the Gemini free-tier quota.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

import ai_helper
from schemas import Suggestion, SuggestionRequest
from security import CurrentUser

router = APIRouter(tags=["ai"])


@router.post("/suggest-category", response_model=Suggestion)
def suggest_category(request: SuggestionRequest, user: CurrentUser) -> Suggestion:
    """Gemini's category for a description; 503 with the reason when the AI isn't available."""
    try:
        return Suggestion(category=ai_helper.suggest_category(request.description))
    except ai_helper.AIUnavailableError as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from None
