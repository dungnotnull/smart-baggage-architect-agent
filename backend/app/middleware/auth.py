"""Authentication middleware — bearer token or API key."""

import os

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc", "/docs/oauth2-redirect"}


class AuthMiddleware(BaseHTTPMiddleware):
    """Validate bearer token or API key on non-public endpoints.

    If AUTH_DISABLED=true in dev mode, all requests pass through.
    If AUTH_API_KEY is set, requests must include
      Authorization: Bearer <key>  or  X-API-Key: <key>
    """

    async def dispatch(self, request: Request, call_next):
        auth_disabled = os.getenv("AUTH_DISABLED", "false").lower() == "true"
        if auth_disabled:
            return await call_next(request)

        path = request.url.path
        if path in PUBLIC_PATHS or path.startswith("/docs"):
            return await call_next(request)

        api_key = os.getenv("AUTH_API_KEY", "")
        if not api_key:
            return await call_next(request)

        bearer = request.headers.get("Authorization", "")
        if bearer.startswith("Bearer "):
            token = bearer[7:].strip()
            if token == api_key:
                return await call_next(request)

        header_key = request.headers.get("X-API-Key", "")
        if header_key == api_key:
            return await call_next(request)

        raise HTTPException(status_code=401, detail="Invalid or missing API key")
