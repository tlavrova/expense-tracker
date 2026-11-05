"""Rate limits for the API endpoints: who is asking, and the 429 answer.

The counting itself is in rate_limit.py (no HTTP there); this is the part the routers share.

The visitor's address: behind a hosting service's proxy, the connection comes from the proxy, and
X-Forwarded-For can't be trusted on Render (it keeps whatever the visitor sends, so the limits could
be dodged with made-up addresses). Online, CLIENT_IP_HEADER names a header the host's proxy always
overwrites with the real address: True-Client-IP on Render (set by Cloudflare in front of it).
"""

from __future__ import annotations

import math
import os
from typing import Hashable

from fastapi import HTTPException, Request, status

from rate_limit import RateLimit, TooManyAttempts


def client_ip(request: Request) -> str:
    """The visitor's address: from CLIENT_IP_HEADER if set (online), else from the connection."""
    header = os.environ.get("CLIENT_IP_HEADER", "").strip()
    if header and request.headers.get(header, "").strip():
        return request.headers[header].strip()
    return request.client.host if request.client else "unknown"


def too_many(error: TooManyAttempts, what: str = "attempts") -> HTTPException:
    """429 "Too many <what>. Try again in N minutes." with a Retry-After header (seconds)."""
    minutes = math.ceil(error.retry_after / 60)
    return HTTPException(
        status.HTTP_429_TOO_MANY_REQUESTS,
        f"Too many {what}. Try again in {minutes} minute{'s' if minutes != 1 else ''}.",
        headers={"Retry-After": str(error.retry_after)},
    )


def check(limit: RateLimit, key: Hashable, what: str = "attempts") -> None:
    """429 "Too many <what>" if this key has used up the limit."""
    try:
        limit.check(key)
    except TooManyAttempts as error:
        raise too_many(error, what) from None
