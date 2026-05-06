from __future__ import annotations

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

from config.settings import settings


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if settings.api_key and request.url.path not in {"/health", "/docs", "/openapi.json"}:
            header = request.headers.get("authorization", "")
            if header != f"Bearer {settings.api_key}":
                raise HTTPException(status_code=401, detail="Invalid API key")
        return await call_next(request)

