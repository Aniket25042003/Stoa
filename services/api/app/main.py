from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.routers import campaigns, competitive, conversations, dashboard, health, ingestion, intelligence, orgs
from stoa_core.logging import setup_logging
from stoa_core.redis.security import validate_redis_security
from stoa_core.security.sanitize import UploadValidationError

setup_logging()

app = FastAPI(title="Stoa Marketing Intelligence API", version="1.0.0")
settings = get_settings()
validate_redis_security(settings)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.include_router(health.router)
app.include_router(orgs.router)
app.include_router(dashboard.router)
app.include_router(ingestion.router)
app.include_router(intelligence.router)
app.include_router(conversations.router)
app.include_router(competitive.router)
app.include_router(campaigns.router)


@app.exception_handler(UploadValidationError)
async def upload_validation_handler(_request: Request, exc: UploadValidationError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})
