from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.deps.auth import verify_supabase_jwt
from app.services import supabase_db

router = APIRouter(prefix="/v1/companies", tags=["companies"])


class CreateCompanyBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None


@router.post("")
def create_company(body: CreateCompanyBody, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    cid = supabase_db.insert_company(user_id, body.name, body.description)
    return {"id": cid}


@router.get("")
def list_companies(user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    return {"companies": supabase_db.list_companies_for_user(user_id)}


@router.get("/{company_id}")
def get_company(company_id: str, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    row = supabase_db.get_company(company_id)
    if not row or row.get("user_id") != user_id:
        raise HTTPException(404, "Company not found")
    return {"company": row}


@router.get("/{company_id}/knowledge")
def list_knowledge(
    company_id: str,
    user_id: str = Depends(verify_supabase_jwt),
    kind: str | None = None,
    q: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    row = supabase_db.get_company(company_id)
    if not row or row.get("user_id") != user_id:
        raise HTTPException(404, "Company not found")
    if q and q.strip():
        items = supabase_db.search_knowledge_text(company_id, q.strip(), kinds=[kind] if kind else None, limit=limit)
    else:
        items = supabase_db.list_knowledge_for_company(company_id, kind=kind, limit=limit)
    return {"items": items}


@router.get("/{company_id}/gtm-runs")
def list_company_gtm_runs(company_id: str, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    row = supabase_db.get_company(company_id)
    if not row or row.get("user_id") != user_id:
        raise HTTPException(404, "Company not found")
    return {"runs": supabase_db.list_gtm_runs_for_company(company_id)}
