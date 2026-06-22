"""
File: services/core/src/stoa_core/content/generate_video.py
Layer: Core Content Generation
Purpose: Handles video generation using Vertex AI Veo 3.1 via google-genai client.
Dependencies: google-genai, stoa_core
"""

from __future__ import annotations

import logging
import time

from google.genai import types

from stoa_core.config import get_settings
from stoa_core.content.generate_image import _get_genai_client

logger = logging.getLogger(__name__)


def generate_video(
    prompt: str,
    *,
    enriched_prompt: str | None = None,
    aspect_ratio: str = "16:9",
    resolution: str = "720p",
    reference_image_bytes: bytes | None = None,
    model: str | None = None,
) -> bytes:
    """Generate a video via Vertex AI Veo.

    Supports optional reference image for image-to-video generation.
    Polls the long-running operation until completion.
    Returns raw video bytes.
    """
    settings = get_settings()
    model_to_use = model or settings.content_video_model
    prompt_to_use = enriched_prompt or prompt
    timeout = settings.content_video_timeout_seconds
    
    # Supported ratios are 16:9 and 9:16. Ensure format.
    ratio = aspect_ratio.strip()
    res = resolution.strip()
    
    logger.info(
        "Generating video using model=%s, ratio=%s, resolution=%s, timeout=%ds (has_ref_image=%s)",
        model_to_use,
        ratio,
        res,
        timeout,
        reference_image_bytes is not None,
    )
    
    client = _get_genai_client()
    
    # Build configuration
    config_args: dict = {
        "aspect_ratio": ratio,
        "resolution": res,
        "person_generation": "ALLOW_ADULT",
        "duration_seconds": 5, # Veo default/fast generates 5s clips
    }
    
    if reference_image_bytes is not None:
        logger.info("Configuring reference image for image-to-video generation")
        ref_image = types.VideoGenerationReferenceImage(
            image=types.Image(image_bytes=reference_image_bytes, mime_type="image/png"),
            reference_type="ASSET",
        )
        config_args["reference_images"] = [ref_image]
        
    config = types.GenerateVideosConfig(**config_args)
    
    try:
        operation = client.models.generate_videos(
            model=model_to_use,
            prompt=prompt_to_use,
            config=config,
        )
        
        operation_id = getattr(operation, "name", "unknown")
        logger.info("Enqueued video generation operation: %s. Starting polling...", operation_id)
        
        # Poll with exponential backoff
        start_time = time.time()
        delay = 10.0  # Initial delay
        max_delay = 30.0
        
        while not operation.done:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                logger.error(
                    "Video generation operation %s timed out after %ds",
                    operation_id,
                    timeout,
                )
                raise TimeoutError(f"Video generation timed out after {timeout} seconds")
                
            logger.info(
                "Polling operation status (elapsed: %ds, next poll in %ds)...",
                int(elapsed),
                int(delay),
            )
            time.sleep(delay)
            
            # Refresh operation status
            operation = client.operations.get(operation)
            
            # Increase delay exponentially
            delay = min(delay * 1.5, max_delay)
            
        logger.info("Video generation operation %s completed.", operation_id)
        
        # Verify operation succeeded
        if getattr(operation, "error", None):
            error_msg = getattr(operation.error, "message", str(operation.error))
            raise RuntimeError(f"Video generation operation failed: {error_msg}")
            
        if not operation.response or not operation.response.generated_videos:
            raise RuntimeError("No generated videos returned from the operation response")
            
        generated_video = operation.response.generated_videos[0].video
        logger.info("Downloading generated video from file service...")
        
        video_file = client.files.download(file=generated_video)
        video_bytes = video_file.content
        
        if not video_bytes:
            raise RuntimeError("Video file download returned empty content")
            
        logger.info("Successfully downloaded generated video (%d bytes)", len(video_bytes))
        return video_bytes
        
    except Exception as e:
        logger.error("Failed to generate video: %s", e)
        raise RuntimeError(f"Veo generation failed: {e}") from e
