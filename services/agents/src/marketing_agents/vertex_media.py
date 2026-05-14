"""Vertex Imagen / Veo + optional Supabase Storage upload."""

from __future__ import annotations

import logging
import os
import re
import uuid
from typing import Any

logger = logging.getLogger(__name__)

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _bucket() -> str:
    return (os.getenv("MKT_STORAGE_BUCKET") or "marketing-assets").strip()


def _safe_uuid_segment(value: str, *, label: str) -> str:
    """Only allow canonical UUID strings in storage paths (avoid path traversal)."""
    s = (value or "").strip()
    if _UUID_RE.match(s):
        return s
    logger.warning("vertex_media: invalid %s for storage path, using placeholder", label)
    return "00000000-0000-0000-0000-000000000000"


def generate_image(
    *,
    company_id: str,
    chat_id: str,
    prompt: str,
    aspect_ratio: str = "1:1",
) -> dict[str, Any]:
    """Generate image via Vertex Imagen; upload bytes to Supabase Storage if configured."""
    out: dict[str, Any] = {"ok": False, "storage_path": None, "mime_type": "image/png", "metadata": {}}
    safe_company = _safe_uuid_segment(company_id, label="company_id")
    safe_chat = _safe_uuid_segment(chat_id, label="chat_id")
    model = (os.getenv("MKT_IMAGEN_MODEL") or "imagen-3.0-generate-002").strip()
    project = (os.getenv("GTM_VERTEX_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT") or "").strip()
    location = (os.getenv("GTM_VERTEX_LOCATION") or "us-central1").strip()
    if not project:
        logger.warning("generate_image: missing project")
        out["error"] = "missing_vertex_project"
        return out

    try:
        import vertexai
        from vertexai.preview.vision_models import ImageGenerationModel

        vertexai.init(project=project, location=location)
        gen = ImageGenerationModel.from_pretrained(model)
        resp = gen.generate_images(
            prompt=prompt[:480],
            number_of_images=1,
            aspect_ratio=aspect_ratio,
            safety_filter_level="block_few",
            person_generation="allow_adult",
        )
        images = getattr(resp, "images", None) or []
        if not images:
            out["error"] = "no_images"
            return out
        raw = getattr(images[0], "_image_bytes", None) or getattr(images[0], "data", None)
        if raw is None and hasattr(images[0], "save"):
            import io

            buf = io.BytesIO()
            images[0].save(buf, format="PNG")
            raw = buf.getvalue()
        if not raw:
            out["error"] = "empty_bytes"
            return out

        path = f"{safe_company}/images/{safe_chat}/{uuid.uuid4().hex}.png"
        url = (os.getenv("SUPABASE_URL") or "").strip()
        key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
        if not url or not key:
            out["error"] = "supabase_not_configured"
            out["metadata"]["note"] = "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to upload generated images."
            return out

        try:
            import httpx

            # Path segments are UUID-only after sanitization; safe for URL path.
            up = f"{url.rstrip('/')}/storage/v1/object/{_bucket()}/{path}"
            r = httpx.post(
                up,
                headers={
                    "Authorization": f"Bearer {key}",
                    "apikey": key,
                    "Content-Type": "image/png",
                    "x-upsert": "true",
                },
                content=raw if isinstance(raw, bytes) else bytes(raw),
                timeout=120.0,
            )
            if r.status_code not in (200, 201):
                logger.warning("Storage upload failed: %s %s", r.status_code, r.text[:200])
                out["error"] = f"upload_{r.status_code}"
                return out
        except Exception as exc:
            logger.warning("Storage upload exception: %s", exc)
            out["error"] = str(exc)
            return out

        out["ok"] = True
        out["storage_path"] = path
        out["metadata"] = {"model": model, "aspect_ratio": aspect_ratio, "prompt_excerpt": prompt[:120]}
        return out
    except Exception as exc:
        logger.warning("generate_image failed: %s", exc)
        out["error"] = str(exc)
        return out


def generate_video(
    *,
    company_id: str,
    chat_id: str,
    prompt: str,
    duration_s: int = 6,
) -> dict[str, Any]:
    """Start or stub Veo generation. Full async poll should be handled by Celery; this returns op metadata."""
    safe_company = _safe_uuid_segment(company_id, label="company_id")
    safe_chat = _safe_uuid_segment(chat_id, label="chat_id")
    model = (os.getenv("MKT_VEO_MODEL") or "veo-2.0-generate-001").strip()
    project = (os.getenv("GTM_VERTEX_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT") or "").strip()
    location = (os.getenv("GTM_VERTEX_LOCATION") or "us-central1").strip()
    out: dict[str, Any] = {
        "ok": False,
        "storage_path": None,
        "mime_type": "video/mp4",
        "metadata": {"model": model, "prompt_excerpt": prompt[:120], "duration_s": duration_s},
    }
    if not project:
        out["error"] = "missing_vertex_project"
        return out

    try:
        from google.cloud import aiplatform

        aiplatform.init(project=project, location=location)
        out["ok"] = True
        out["metadata"]["status"] = "queued_stub"
        out["metadata"]["note"] = (
            "Wire your Veo long-running op here (MKT_VEO_MODEL). "
            "Bucket: " + _bucket()
        )
        out["storage_path"] = f"{safe_company}/videos/{safe_chat}/{uuid.uuid4().hex}.mp4.pending"
        return out
    except Exception as exc:
        logger.warning("generate_video failed: %s", exc)
        out["error"] = str(exc)
        return out
