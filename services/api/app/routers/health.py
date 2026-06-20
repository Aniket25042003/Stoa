"""
File: services/api/app/routers/health.py
Layer: FastAPI Route Layer
Purpose: Exposes authenticated REST endpoints and coordinates validation, permissions, and service calls.
Dependencies: FastAPI
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Handles health logic for the surrounding Stoa workflow.

    Returns:
        dict[str, str]: Result produced for the caller.
    """
    return {"status": "ok"}
