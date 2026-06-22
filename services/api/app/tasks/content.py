"""
File: services/api/app/tasks/content.py
Layer: Celery Task Layer
Purpose: Background worker tasks for content asset generation (Imagen and Veo).
Dependencies: Supabase, Celery, Redis, stoa_core
"""

from __future__ import annotations

import logging
import time

from app.celery_app import celery_app
from app.services.task_context import verify_content_asset
from stoa_core.config import get_settings
from stoa_core.content.enrich import enrich_content_prompt
from stoa_core.content.generate_image import generate_images
from stoa_core.content.generate_video import generate_video
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.rag.ingest import ingest_knowledge
from stoa_core.redis.client import publish_event

logger = logging.getLogger(__name__)


@celery_app.task(name="content.generate_asset", bind=True, max_retries=2)
def generate_content_asset(self, asset_id: str) -> None:
    """Background task for content asset generation.

    Flow:
    1. Load asset record from DB
    2. Enrich prompt via KB retrieval + LLM
    3. Call Vertex AI generation (image or video)
    4. Upload result to Supabase Storage (content-assets bucket)
    5. Update asset record with file URLs & metadata
    6. Ingest asset metadata into KB as kind="content_asset"
    7. Publish SSE completion event
    """
    sb = get_supabase_admin()
    settings = get_settings()
    
    try:
        asset = verify_content_asset(asset_id)
    except ValueError as exc:
        logger.warning("Rejected content asset generation %s: %s", asset_id, exc)
        return

    org_id = asset["org_id"]
    campaign_id = asset.get("campaign_id")
    asset_type = asset["asset_type"]
    prompt = asset["prompt"]
    config = asset.get("config") or {}
    
    logger.info("Starting asset generation for asset_id=%s, type=%s", asset_id, asset_type)
    
    # 1. Update status to generating
    sb.table("content_assets").update({"status": "generating"}).eq("id", asset_id).execute()
    publish_event("content", asset_id, {"status": "generating"})
    
    start_time = time.time()
    
    try:
        # 2. Enrich prompt via RAG context
        enriched_prompt, context_refs = enrich_content_prompt(
            org_id,
            prompt,
            campaign_id=campaign_id,
            asset_type=asset_type,
        )
        
        # Save enriched prompt immediately in case of down-stream failure
        sb.table("content_assets").update({"enriched_prompt": enriched_prompt}).eq("id", asset_id).execute()
        
        files_list = []
        model_used = ""
        
        # 3. Perform generation and upload
        if asset_type == "image":
            use_fast = config.get("use_fast_model", False)
            model_used = settings.content_image_model_fast if use_fast else settings.content_image_model
            ratio = config.get("aspect_ratio", "1:1")
            num_images = min(max(1, config.get("number_of_images", 1)), settings.content_max_images_per_request)
            
            logger.info("Invoking Imagen for asset_id=%s with model=%s", asset_id, model_used)
            images_bytes = generate_images(
                prompt=prompt,
                enriched_prompt=enriched_prompt,
                aspect_ratio=ratio,
                number_of_images=num_images,
                mime_type="image/png",
                model=model_used,
            )
            
            for idx, img_bytes in enumerate(images_bytes):
                storage_path = f"{org_id}/{asset_id}/{idx}.png"
                logger.info("Uploading image to storage path: %s", storage_path)
                
                sb.storage.from_(settings.content_storage_bucket).upload(
                    path=storage_path,
                    file=img_bytes,
                    file_options={"content-type": "image/png"},
                )
                
                files_list.append({
                    "storage_path": storage_path,
                    "mime_type": "image/png",
                    "size_bytes": len(img_bytes),
                    "width": None,  # Optional image metadata
                    "height": None,
                })
                
        elif asset_type == "video":
            use_fast = config.get("use_fast_model", False)
            model_used = settings.content_video_model_fast if use_fast else settings.content_video_model
            ratio = config.get("aspect_ratio", "16:9")
            res = config.get("resolution", "720p")
            
            ref_image_bytes = None
            ref_asset_id = asset.get("reference_asset_id")
            
            if ref_asset_id:
                logger.info("Loading reference image for image-to-video from asset: %s", ref_asset_id)
                ref_asset = verify_content_asset(ref_asset_id)
                ref_files = ref_asset.get("files") or []
                if ref_files:
                    ref_path = ref_files[0]["storage_path"]
                    logger.info("Downloading reference image from: %s", ref_path)
                    ref_image_bytes = sb.storage.from_(settings.content_storage_bucket).download(ref_path)
                else:
                    logger.warning("Reference asset %s has no generated files", ref_asset_id)
            
            logger.info("Invoking Veo for asset_id=%s with model=%s", asset_id, model_used)
            video_bytes = generate_video(
                prompt=prompt,
                enriched_prompt=enriched_prompt,
                aspect_ratio=ratio,
                resolution=res,
                reference_image_bytes=ref_image_bytes,
                model=model_used,
            )
            
            storage_path = f"{org_id}/{asset_id}/video.mp4"
            logger.info("Uploading video to storage path: %s", storage_path)
            
            sb.storage.from_(settings.content_storage_bucket).upload(
                path=storage_path,
                file=video_bytes,
                file_options={"content-type": "video/mp4"},
            )
            
            files_list.append({
                "storage_path": storage_path,
                "mime_type": "video/mp4",
                "size_bytes": len(video_bytes),
                "duration_seconds": 5, # standard Veo clip duration
            })
        else:
            raise ValueError(f"Unsupported asset type: {asset_type}")
            
        generation_time = time.time() - start_time
        logger.info("Generation completed in %.2fs. Updating DB...", generation_time)
        
        # 4. Save results to DB
        metadata = {
            "model_used": model_used,
            "generation_time_seconds": round(generation_time, 2),
            "kb_context_refs": context_refs,
        }
        
        sb.table("content_assets").update({
            "status": "completed",
            "files": files_list,
            "generation_metadata": metadata,
            "error": None,
        }).eq("id", asset_id).execute()
        
        # 5. Ingest into unified Knowledge Base
        kb_text = (
            f"Content Asset: {asset_type}\n"
            f"Prompt: {prompt}\n"
            f"Enriched Prompt: {enriched_prompt}\n"
            f"Campaign ID: {campaign_id or 'none'}\n"
            f"Config: {config}\n"
            f"Model: {model_used}\n"
            f"Files: {len(files_list)} files generated"
        )
        
        ingest_knowledge(
            org_id,
            kind="content_asset",
            title=f"Generated {asset_type.title()}: {prompt[:80]}",
            text=kb_text,
            feature_origin="content",
            uri=f"content:{asset_id}",
            metadata={"asset_id": asset_id, "asset_type": asset_type, "campaign_id": campaign_id},
        )
        
        # 6. Publish SSE event
        publish_event("content", asset_id, {"status": "completed"})
        logger.info("Asset %s generation background task finished successfully", asset_id)
        
    except Exception as exc:
        logger.exception("Content asset generation failed for asset_id=%s", asset_id)
        # Update state to failed
        error_msg = str(exc)
        sb.table("content_assets").update({
            "status": "failed",
            "error": error_msg[:1000],
        }).eq("id", asset_id).execute()
        
        publish_event("content", asset_id, {"status": "failed", "error": error_msg})
        
        # Retry with countdown
        raise self.retry(exc=exc, countdown=30) from exc
