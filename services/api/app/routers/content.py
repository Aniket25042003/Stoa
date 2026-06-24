"""
File: services/api/app/routers/content.py
Layer: FastAPI Route Layer
Purpose: Exposes authenticated REST endpoints for AI content generation, library retrieval, and deletion.
Dependencies: FastAPI, Supabase, Pydantic, Redis, stoa_core
"""

from __future__ import annotations

import logging
from typing import Any, Literal
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.deps.org_scope import require_onboarded_scope
from app.deps.rate_limit import check_rate_limit
from app.services.audit import write_audit
from app.services.org_context import OrgScope, require_permission
from app.tasks.content import generate_content_asset
from stoa_core.config import get_settings
from stoa_core.db.resource_scope import verify_org_resource
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.redis.sse import read_events_since
from stoa_core.security.sanitize import sanitize_user_content

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/content", tags=["content"])


class ContentConfig(BaseModel):
    aspect_ratio: str = "1:1"                # 1:1, 16:9, 9:16, 4:3, etc.
    number_of_images: int = 1                # 1-4 for images
    resolution: str = "720p"                 # 720p or 1080p for video
    use_fast_model: bool = False             # Use fast/cheaper model


class ContentGenerateRequest(BaseModel):
    """Request model for enqueuing a new AI content generation job."""
    prompt: str = Field(min_length=5, max_length=2000)
    asset_type: Literal["image", "video"]
    campaign_id: str | None = None
    reference_asset_id: str | None = None
    config: ContentConfig | None = None


def _validate_content_cross_refs(
    org_id: str,
    *,
    campaign_id: str | None = None,
    reference_asset_id: str | None = None,
) -> None:
    """Ensure linked campaign and reference assets belong to the active org."""
    if campaign_id:
        try:
            verify_org_resource("campaigns", campaign_id, org_id, select="id")
        except ValueError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Campaign not found") from exc
    if reference_asset_id:
        try:
            verify_org_resource("content_assets", reference_asset_id, org_id, select="id")
        except ValueError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Reference asset not found") from exc


class ContentAssetUpdate(BaseModel):
    """Request model for updating an existing content asset (e.g. linking campaign)."""
    campaign_id: str | None = None
    prompt: str | None = None


def _sign_asset_files(assets: list[dict[str, Any]], sb: Any, bucket: str) -> None:
    """Helper to dynamically generate temporary signed URLs for private storage files."""
    for asset in assets:
        files = asset.get("files") or []
        for file_info in files:
            storage_path = file_info.get("storage_path")
            if storage_path:
                try:
                    # Generate signed URL valid for 3600 seconds (1 hour)
                    signed_res = sb.storage.from_(bucket).create_signed_url(storage_path, 3600)
                    # Handle return types containing signedURL or signedUrl
                    url = getattr(signed_res, "signedURL", None) or getattr(signed_res, "signedUrl", None)
                    if isinstance(signed_res, dict):
                        url = url or signed_res.get("signedURL") or signed_res.get("signedUrl")
                    
                    if url:
                        file_info["public_url"] = url
                except Exception as e:
                    logger.warning("Failed to generate signed URL for path %s: %s", storage_path, e)


@router.get("")
def list_content_assets(
    asset_type: Literal["image", "video"] | None = None,
    campaign_id: str | None = None,
    scope: OrgScope = Depends(require_onboarded_scope),
) -> dict[str, Any]:
    """List all content assets for the active organization with dynamic pre-signed URLs."""
    require_permission(scope, "content:read")
    
    sb = get_supabase_admin()
    query = sb.table("content_assets").select("*").eq("org_id", scope.org_id)
    
    if asset_type:
        query = query.eq("asset_type", asset_type)
    if campaign_id:
        query = query.eq("campaign_id", campaign_id)
        
    res = query.order("created_at", desc=True).execute()
    assets = res.data or []
    
    # Sign private files so they can be viewed securely in browser
    bucket = get_settings().content_storage_bucket
    _sign_asset_files(assets, sb, bucket)
    
    return {"assets": assets}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_content_generation(
    body: ContentGenerateRequest,
    scope: OrgScope = Depends(require_onboarded_scope),
) -> dict[str, Any]:
    """Enqueue a new visual content generation background task (Imagen or Veo)."""
    require_permission(scope, "content:create")
    
    # Enforce safe rate limiting for expensive generation tasks
    check_rate_limit(scope.user_id, limit_per_minute=5, scope="content_generation")
    
    sb = get_supabase_admin()
    prompt = sanitize_user_content(body.prompt)
    config = (body.config or ContentConfig()).model_dump()
    _validate_content_cross_refs(
        scope.org_id,
        campaign_id=body.campaign_id,
        reference_asset_id=body.reference_asset_id,
    )

    # 1. Insert queued record into public.content_assets
    res = (
        sb.table("content_assets")
        .insert({
            "org_id": scope.org_id,
            "campaign_id": body.campaign_id,
            "asset_type": body.asset_type,
            "prompt": prompt,
            "reference_asset_id": body.reference_asset_id,
            "config": config,
            "status": "queued",
            "created_by": scope.user_id,
        })
        .execute()
    )
    
    asset = (res.data or [None])[0]
    if not asset:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to create content asset record")
        
    # 2. Dispatch Celery background task
    generate_content_asset.delay(asset["id"])
    write_audit(scope.org_id, scope.user_id, "content.queued", "content_asset", asset["id"])
    
    return {"asset": asset}


@router.get("/{asset_id}")
def get_content_asset(
    asset_id: str,
    scope: OrgScope = Depends(require_onboarded_scope),
) -> dict[str, Any]:
    """Get detailed state of a single content asset."""
    require_permission(scope, "content:read")
    
    sb = get_supabase_admin()
    res = (
        sb.table("content_assets")
        .select("*")
        .eq("id", asset_id)
        .eq("org_id", scope.org_id)
        .limit(1)
        .execute()
    )
    
    if not res.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Content asset not found")
        
    asset = res.data[0]
    bucket = get_settings().content_storage_bucket
    _sign_asset_files([asset], sb, bucket)
    
    return {"asset": asset}


@router.patch("/{asset_id}")
def update_content_asset(
    asset_id: str,
    body: ContentAssetUpdate,
    scope: OrgScope = Depends(require_onboarded_scope),
) -> dict[str, Any]:
    """Update metadata fields of a content asset (e.g. link/unlink from campaign)."""
    require_permission(scope, "content:write")
    
    sb = get_supabase_admin()
    # Check resource belongs to org
    check_res = sb.table("content_assets").select("id").eq("id", asset_id).eq("org_id", scope.org_id).limit(1).execute()
    if not check_res.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Content asset not found")
        
    updates: dict[str, Any] = {}
    if body.campaign_id is not None:
        if body.campaign_id:
            _validate_content_cross_refs(scope.org_id, campaign_id=body.campaign_id)
        updates["campaign_id"] = body.campaign_id or None
    if body.prompt is not None:
        updates["prompt"] = sanitize_user_content(body.prompt)
        
    if not updates:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No fields to update provided")
        
    res_update = sb.table("content_assets").update(updates).eq("id", asset_id).eq("org_id", scope.org_id).execute()
    asset = res_update.data[0]
    
    write_audit(scope.org_id, scope.user_id, "content.updated", "content_asset", asset_id)
    return {"asset": asset}


@router.delete("/{asset_id}")
def delete_content_asset(
    asset_id: str,
    scope: OrgScope = Depends(require_onboarded_scope),
) -> dict[str, str]:
    """Delete a content asset, removing its storage objects and knowledge base memory."""
    require_permission(scope, "content:delete")
    
    sb = get_supabase_admin()
    # Retrieve asset details to find file paths
    res = sb.table("content_assets").select("files").eq("id", asset_id).eq("org_id", scope.org_id).limit(1).execute()
    if not res.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Content asset not found")
        
    asset = res.data[0]
    bucket = get_settings().content_storage_bucket
    files = asset.get("files") or []
    
    # 1. Delete associated media files from storage
    storage_paths = [f["storage_path"] for f in files if f.get("storage_path")]
    if storage_paths:
        try:
            sb.storage.from_(bucket).remove(storage_paths)
            logger.info("Removed files from storage for asset_id=%s: %s", asset_id, storage_paths)
        except Exception as e:
            logger.warning("Failed to remove files from storage bucket: %s", e)
            
    # 2. Delete entry from public.knowledge_chunks / items
    try:
        sb.table("knowledge_items").delete().eq("org_id", scope.org_id).eq("uri", f"content:{asset_id}").execute()
    except Exception as e:
        logger.warning("Failed to remove content asset from KB: %s", e)
        
    # 3. Delete database record
    sb.table("content_assets").delete().eq("id", asset_id).eq("org_id", scope.org_id).execute()
    write_audit(scope.org_id, scope.user_id, "content.deleted", "content_asset", asset_id)
    
    return {"status": "deleted"}


@router.get("/{asset_id}/events")
async def content_generation_events(
    asset_id: str,
    request: Request,
    scope: OrgScope = Depends(require_onboarded_scope),
) -> StreamingResponse:
    """SSE endpoint to stream real-time progress of visual asset generation."""
    require_permission(scope, "content:read")
    sb = get_supabase_admin()
    asset = (
        sb.table("content_assets")
        .select("id")
        .eq("id", asset_id)
        .eq("org_id", scope.org_id)
        .limit(1)
        .execute()
    )
    if not asset.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Content asset not found")

    async def _gen():
        last_id = request.headers.get("Last-Event-ID", "0-0")
        async for msg_id, data in read_events_since("content", asset_id, last_id):
            yield f"id: {msg_id}\ndata: {__import__('json').dumps(data)}\n\n"
            
    return StreamingResponse(_gen(), media_type="text/event-stream")
