from __future__ import annotations

import asyncio
import io
import json
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from app.deps.auth import verify_supabase_jwt
from app.services import supabase_db
from app.services.redis_events import read_events_since
from app.tasks.gtm import run_pipeline_task

router = APIRouter(prefix="/v1/runs", tags=["runs"])


class CreateRunBody(BaseModel):
    product_description: str = Field(..., min_length=10)
    product_name: str | None = None
    website_url: str | None = None
    target_customers: str | None = None
    geography: str | None = None
    known_competitors: list[str] | None = None
    business_model: str | None = None
    stage: str | None = None
    constraints: list[str] | None = None
    horizon_days: int | None = 90


@router.post("")
def create_run(body: CreateRunBody, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    payload = body.model_dump()
    run_id = supabase_db.insert_run(user_id, payload)
    run_pipeline_task.delay(run_id, user_id)
    return {"id": run_id, "status": "queued"}


@router.get("")
def list_runs(user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    runs = supabase_db.list_runs_for_user(user_id)
    return {"runs": runs}


@router.get("/{run_id}")
def get_run(run_id: str, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    row = supabase_db.get_run(run_id)
    if not row or row.get("user_id") != user_id:
        raise HTTPException(404, "Run not found")
    return {"run": row}


@router.get("/{run_id}/report")
def get_report(run_id: str, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    row = supabase_db.get_run(run_id)
    if not row or row.get("user_id") != user_id:
        raise HTTPException(404, "Run not found")
    rep = supabase_db.get_latest_report(run_id)
    if not rep:
        return {"markdown": None}
    return {"markdown": rep.get("markdown"), "report_id": rep.get("id")}


@router.get("/{run_id}/sources")
def get_sources(run_id: str, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    row = supabase_db.get_run(run_id)
    if not row or row.get("user_id") != user_id:
        raise HTTPException(404, "Run not found")
    return {"sources": supabase_db.list_research_sources(run_id)}


@router.get("/{run_id}/report.pdf")
def get_report_pdf(run_id: str, user_id: str = Depends(verify_supabase_jwt)) -> Response:
    row = supabase_db.get_run(run_id)
    if not row or row.get("user_id") != user_id:
        raise HTTPException(404, "Run not found")
    rep = supabase_db.get_latest_report(run_id)
    if not rep or not rep.get("markdown"):
        raise HTTPException(404, "Report not ready")

    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, title=f"GTM Report {run_id}")
    styles = getSampleStyleSheet()
    story = []
    for raw_line in str(rep["markdown"]).splitlines():
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 8))
            continue
        if line.startswith("# "):
            story.append(Paragraph(line[2:], styles["Title"]))
        elif line.startswith("## "):
            story.append(Paragraph(line[3:], styles["Heading2"]))
        elif line.startswith("- "):
            story.append(Paragraph(f"- {line[2:]}", styles["BodyText"]))
        elif line.startswith("```"):
            continue
        else:
            story.append(Paragraph(line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), styles["BodyText"]))
    doc.build(story)
    return Response(
        content=buf.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="gtm-report-{run_id}.pdf"'},
    )


async def _sse_gen(run_id: str, user_id: str) -> AsyncGenerator[bytes, None]:
    row = supabase_db.get_run(run_id)
    if not row or row.get("user_id") != user_id:
        yield f"event: error\ndata: {json.dumps({'message': 'not found'})}\n\n".encode()
        return

    # Replay persisted events first
    try:
        for ev in supabase_db.list_run_events(run_id, limit=200):
            yield f"event: progress\ndata: {json.dumps(ev.get('payload') or {})}\n\n".encode()
    except Exception:
        yield b": persisted-event replay unavailable\n\n"

    # Only new Redis stream messages after replay (avoid duplicates)
    last_id: str | None = "$"
    try:
        async for msg_id, data in read_events_since(run_id, last_id):
            if msg_id == "heartbeat":
                yield b": heartbeat\n\n"
                continue
            last_id = msg_id
            yield f"event: progress\ndata: {json.dumps(data)}\n\n".encode()
            if data.get("message") == "Pipeline completed":
                return
            if "Failed" in str(data.get("message", "")) and (data.get("detail") or {}).get("error"):
                return
    except asyncio.CancelledError:
        raise
    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n".encode()


@router.get("/{run_id}/events")
async def stream_events(run_id: str, user_id: str = Depends(verify_supabase_jwt)) -> StreamingResponse:
    return StreamingResponse(
        _sse_gen(run_id, user_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )
