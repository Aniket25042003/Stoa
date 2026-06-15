from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from app.deps.client_ip import trusted_client_ip
from app.deps.rate_limit import check_public_rate_limit
from stoa_core.db.supabase import get_supabase_admin

router = APIRouter(prefix="/v1/waitlist", tags=["waitlist"])


class WaitlistBody(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=320)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        email = value.strip().lower()
        if not re.fullmatch(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
            raise ValueError("Invalid email")
        return email

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return value.strip()


@router.post("")
def join_waitlist(body: WaitlistBody, request: Request) -> dict[str, str]:
    check_public_rate_limit(
        trusted_client_ip(request),
        email=body.email,
        scope="waitlist",
    )

    sb = get_supabase_admin()
    existing = (
        sb.table("waitlist")
        .select("id")
        .eq("email", body.email)
        .limit(1)
        .execute()
    )
    if existing.data:
        return {"status": "already_registered"}

    try:
        sb.table("waitlist").insert({"name": body.name, "email": body.email}).execute()
        return {"status": "registered"}
    except Exception as exc:
        message = str(exc).lower()
        if "23505" in message or "duplicate" in message or "unique" in message:
            return {"status": "already_registered"}
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Registration failed") from exc
