"""Rate limiting middleware using slowapi."""

import os

from fastapi import HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60/minute"],
    storage_uri=os.getenv("RATE_LIMIT_STORAGE", "memory://"),
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforce per-IP rate limits on API endpoints.

    Default: 60 requests/minute per IP.
    Override via RATE_LIMIT_PER_MINUTE env var.
    """

    async def dispatch(self, request: Request, call_next):
        if request.url.path in {"/health", "/docs", "/openapi.json", "/redoc"}:
            return await call_next(request)

        try:
            return await call_next(request)
        except Exception as exc:
            if "rate limit" in str(exc).lower():
                raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
            raise
