from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.deps.auth import verify_supabase_jwt
from app.services import supabase_db
from app.services.gtm_plan_editor import edit_gtm_plan
from app.tasks.gtm import create_master_plan_task

router = APIRouter(prefix="/v1/companies", tags=["companies"])


class CreateCompanyBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    website_url: str | None = None
    industry: str | None = None
    target_customers: str | None = None
    geography: str | None = None
    business_model: str | None = None
    stage: str | None = None
    goals: list[str] = Field(default_factory=list)
    known_competitors: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    brand_voice: dict[str, Any] = Field(default_factory=dict)
    onboarding_completed: bool = False


class UpdateCompanyBody(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    website_url: str | None = None
    industry: str | None = None
    target_customers: str | None = None
    geography: str | None = None
    business_model: str | None = None
    stage: str | None = None
    goals: list[str] | None = None
    known_competitors: list[str] | None = None
    constraints: list[str] | None = None
    brand_voice: dict[str, Any] | None = None
    onboarding_completed: bool | None = None


class UploadGtmPlanBody(BaseModel):
    title: str = Field("GTM plan", min_length=1, max_length=200)
    content_markdown: str = Field(..., min_length=20, max_length=200000)
    content_json: dict[str, Any] = Field(default_factory=dict)


class GtmPlanMessageBody(BaseModel):
    content: str = Field(..., min_length=1, max_length=32000)


class MarketingBaselineBody(BaseModel):
    brand_voice_notes: str | None = Field(None, max_length=32000)
    design_notes: str | None = Field(None, max_length=32000)
    campaign_goals: str | None = Field(None, max_length=32000)
    channels: list[str] = Field(default_factory=list)


def _require_company(company_id: str, user_id: str) -> dict[str, Any]:
    row = supabase_db.get_company(company_id)
    if not row or row.get("user_id") != user_id:
        raise HTTPException(404, "Company not found")
    return row


def _profile_payload(body: CreateCompanyBody | UpdateCompanyBody) -> dict[str, Any]:
    data = body.model_dump(exclude_unset=True)
    if data.pop("onboarding_completed", False):
        from datetime import datetime, timezone

        data["onboarding_completed_at"] = datetime.now(timezone.utc).isoformat()
    return data


@router.post("")
def create_company(body: CreateCompanyBody, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    payload = _profile_payload(body)
    name = str(payload.pop("name"))
    description = payload.pop("description", None)
    brand_voice = payload.pop("brand_voice", None)
    cid = supabase_db.insert_company(user_id, name, description, brand_voice=brand_voice, **payload)
    return {"id": cid}


@router.get("")
def list_companies(user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    return {"companies": supabase_db.list_companies_for_user(user_id)}


@router.get("/{company_id}")
def get_company(company_id: str, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    return {"company": _require_company(company_id, user_id)}


@router.patch("/{company_id}")
def update_company(company_id: str, body: UpdateCompanyBody, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    _require_company(company_id, user_id)
    row = supabase_db.update_company_profile(company_id, **_profile_payload(body))
    return {"company": row}


@router.get("/{company_id}/summary")
def company_summary(company_id: str, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    company = _require_company(company_id, user_id)
    runs = supabase_db.list_gtm_runs_for_company(company_id, limit=20)
    chats = supabase_db.list_marketing_chats(company_id, limit=20)
    knowledge = supabase_db.list_knowledge_for_company(company_id, limit=50)
    plan = supabase_db.get_active_gtm_plan(company_id)
    artifacts = supabase_db.list_company_marketing_artifacts(company_id, limit=10)
    profile_fields = [
        "name",
        "description",
        "industry",
        "target_customers",
        "geography",
        "business_model",
        "stage",
    ]
    completed = sum(1 for key in profile_fields if company.get(key))
    return {
        "company": company,
        "stats": {
            "profile_completion": round(completed / len(profile_fields), 2),
            "gtm_runs": len(runs),
            "marketing_chats": len(chats),
            "knowledge_items": len(knowledge),
            "marketing_artifacts": len(artifacts),
        },
        "readiness": {
            "has_company_profile": bool(company.get("onboarding_completed_at")),
            "has_gtm_plan": bool(plan),
            "has_marketing_baseline": any(item.get("kind") in ("brand_decision", "channel", "positioning") for item in knowledge),
        },
        "recent": {
            "runs": runs[:5],
            "chats": chats[:5],
            "knowledge": knowledge[:8],
            "artifacts": artifacts[:5],
        },
        "gtm_plan": plan,
    }


@router.get("/{company_id}/knowledge")
def list_knowledge(
    company_id: str,
    user_id: str = Depends(verify_supabase_jwt),
    kind: str | None = None,
    q: str | None = None,
    limit: int = Query(50, ge=1, le=200),
) -> dict[str, Any]:
    _require_company(company_id, user_id)
    if q and q.strip():
        items = supabase_db.search_knowledge_text(company_id, q.strip(), kinds=[kind] if kind else None, limit=limit)
    else:
        items = supabase_db.list_knowledge_for_company(company_id, kind=kind, limit=limit)
    return {"items": items}


@router.get("/{company_id}/gtm-runs")
def list_company_gtm_runs(company_id: str, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    _require_company(company_id, user_id)
    return {"runs": supabase_db.list_gtm_runs_for_company(company_id)}


@router.post("/{company_id}/marketing-baseline")
def save_marketing_baseline(company_id: str, body: MarketingBaselineBody, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    company = _require_company(company_id, user_id)
    brand_voice = {
        **(company.get("brand_voice") or {}),
        "notes": body.brand_voice_notes or (company.get("brand_voice") or {}).get("notes") or "",
        "design_notes": body.design_notes or "",
        "campaign_goals": body.campaign_goals or "",
        "channels": body.channels,
    }
    updated = supabase_db.update_company_profile(company_id, brand_voice=brand_voice)
    content = "\n".join(
        part
        for part in [
            f"Brand voice: {body.brand_voice_notes}" if body.brand_voice_notes else "",
            f"Design notes: {body.design_notes}" if body.design_notes else "",
            f"Campaign goals: {body.campaign_goals}" if body.campaign_goals else "",
            f"Channels: {', '.join(body.channels)}" if body.channels else "",
        ]
        if part
    )
    if not content:
        content = f"Marketing foundation for {company.get('name')}: keep future campaign work aligned with the company profile."
    kid = supabase_db.insert_company_knowledge(
        company_id,
        kind="brand_decision",
        title="Marketing foundation",
        content=content,
        tags=["marketing", "baseline"],
        source_system="marketing",
    )
    return {"company": updated, "knowledge_id": kid}


@router.get("/{company_id}/gtm-plan")
def get_gtm_plan(company_id: str, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    _require_company(company_id, user_id)
    return {
        "plan": supabase_db.get_active_gtm_plan(company_id),
        "messages": supabase_db.list_gtm_plan_messages(company_id),
    }


@router.post("/{company_id}/gtm-plan/upload")
def upload_gtm_plan(company_id: str, body: UploadGtmPlanBody, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    _require_company(company_id, user_id)
    plan = supabase_db.upsert_company_gtm_plan(
        company_id,
        source="uploaded",
        title=body.title,
        content_markdown=body.content_markdown,
        content_json=body.content_json,
    )
    supabase_db.insert_gtm_plan_message(company_id, "system", "Uploaded an existing GTM plan.", plan_id=str(plan["id"]))
    return {"plan": plan}


@router.post("/{company_id}/gtm-plan/generate")
def generate_gtm_plan(company_id: str, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    company = _require_company(company_id, user_id)
    payload = {
        "product_name": company.get("name"),
        "product_description": company.get("description") or f"{company.get('name')} company workspace",
        "website_url": company.get("website_url"),
        "target_customers": company.get("target_customers"),
        "geography": company.get("geography"),
        "known_competitors": company.get("known_competitors") or [],
        "business_model": company.get("business_model"),
        "stage": company.get("stage"),
        "constraints": company.get("constraints") or [],
        "goals": company.get("goals") or [],
    }
    run_id = supabase_db.insert_run(user_id, payload, master_plan={}, status="planning", company_id=company_id)
    create_master_plan_task.delay(run_id, user_id)
    return {"run_id": run_id, "status": "planning"}


@router.post("/{company_id}/gtm-plan/messages")
def post_gtm_plan_message(company_id: str, body: GtmPlanMessageBody, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    company = _require_company(company_id, user_id)
    plan = supabase_db.get_active_gtm_plan(company_id)
    if not plan:
        raise HTTPException(409, "Create or upload a GTM plan first")
    plan_id = str(plan["id"])
    supabase_db.insert_gtm_plan_message(company_id, "user", body.content, plan_id=plan_id)
    messages = supabase_db.list_gtm_plan_messages(company_id)
    edited = edit_gtm_plan(company=company, plan=plan, messages=messages, user_message=body.content)
    updated_plan = supabase_db.update_company_gtm_plan(
        plan_id,
        content_markdown=edited["updated_markdown"],
        content_json=edited["updated_json"],
        title=edited.get("title"),
    )
    assistant_content = str(edited["assistant_reply"])
    assistant_id = supabase_db.insert_gtm_plan_message(
        company_id,
        "assistant",
        assistant_content,
        plan_id=plan_id,
        parts={"plan_id": plan_id},
    )
    return {
        "message_id": assistant_id,
        "assistant": {"role": "assistant", "content": assistant_content},
        "plan": updated_plan,
    }
