"""
File: services/api/app/main.py
Layer: Application Source
Purpose: Implements main behavior for the application source.
Dependencies: FastAPI, Redis, stoa_core
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.deps.proxy_gate import ProxySecretMiddleware
from app.routers import auth_workflow, alignment, campaign_analysis, campaigns, competitive, content, conversations, dashboard, health, ingestion, integrations, intelligence, onboarding, orgs, roles, team, waitlist
from stoa_core.logging import setup_logging
from stoa_core.redis.security import validate_redis_security
from stoa_core.security.sanitize import UploadValidationError

setup_logging()

settings = get_settings()
validate_redis_security(settings)

if not settings.is_development and not settings.invite_token_pepper:
    raise RuntimeError("INVITE_TOKEN_PEPPER is required outside development")

if not settings.is_development and not settings.internal_proxy_secret:
    raise RuntimeError("INTERNAL_PROXY_SECRET is required outside development")

_openapi_url = None if settings.is_production else "/openapi.json"
_docs_url = None if settings.is_production else "/docs"
_redoc_url = None if settings.is_production else "/redoc"

app = FastAPI(
    title="Stoa Marketing Intelligence API",
    version="1.0.0",
    openapi_url=_openapi_url,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Manage SecurityHeadersMiddleware behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    async def dispatch(self, request: Request, call_next):
        """Asynchronously handles dispatch logic for the surrounding Stoa workflow.

        Args:
            request (Request): Input value used by this workflow step.
            call_next (Any): Input value used by this workflow step.

        Returns:
            Any: Result produced for the caller.
        """
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


app.add_middleware(ProxySecretMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Stoa-Client-IP", "X-Stoa-Proxy-Secret", "X-Org-Id"],
)

app.include_router(health.router)
app.include_router(auth_workflow.router)
app.include_router(onboarding.router)
app.include_router(orgs.router)
app.include_router(roles.router)
app.include_router(dashboard.router)
app.include_router(ingestion.router)
app.include_router(integrations.router)
app.include_router(intelligence.router)
app.include_router(conversations.router)
app.include_router(competitive.router)
app.include_router(campaigns.router)
app.include_router(campaign_analysis.router)
app.include_router(alignment.router)
app.include_router(content.router)
app.include_router(team.router)
app.include_router(waitlist.router)


@app.exception_handler(UploadValidationError)
async def upload_validation_handler(_request: Request, exc: UploadValidationError) -> JSONResponse:
    """Asynchronously handles upload validation handler logic for the surrounding Stoa workflow.

    Args:
        _request (Request): Input value used by this workflow step.
        exc (UploadValidationError): Input value used by this workflow step.

    Returns:
        JSONResponse: Result produced for the caller.
    """
    return JSONResponse(status_code=400, content={"detail": str(exc)})
