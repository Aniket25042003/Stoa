"""
File: services/core/src/stoa_core/content/generate_image.py
Layer: Core Content Generation
Purpose: Handles image generation using Vertex AI Imagen 4.0 via google-genai client.
Dependencies: google-genai, stoa_core
"""

from __future__ import annotations

import logging

from google import genai
from google.genai import types

from stoa_core.config import get_settings

logger = logging.getLogger(__name__)


def _get_genai_client() -> genai.Client:
    """Initialize the Google GenAI Client with Vertex AI settings."""
    settings = get_settings()
    project = settings.resolved_vertex_project
    location = settings.resolved_vertex_location
    
    if not project:
        raise RuntimeError("GCP Project ID must be set for Vertex AI generation")
        
    logger.info("Initializing google-genai client for project=%s, location=%s", project, location)
    return genai.Client(
        vertexai=True,
        project=project,
        location=location,
    )


def generate_images(
    prompt: str,
    *,
    enriched_prompt: str | None = None,
    aspect_ratio: str = "1:1",
    number_of_images: int = 1,
    mime_type: str = "image/png",
    model: str | None = None,
) -> list[bytes]:
    """Generate images via Vertex AI Imagen.

    Uses the enriched prompt (KB-grounded) if available, falling back to the raw prompt.
    Returns list of raw image bytes.
    """
    settings = get_settings()
    model_to_use = model or settings.content_image_model
    prompt_to_use = enriched_prompt or prompt
    
    # Map aspect ratios: google-genai supports "1:1", "3:4", "4:3", "9:16", "16:9"
    # Ensure aspect ratio format is clean.
    ratio = aspect_ratio.strip()
    
    logger.info(
        "Generating %d image(s) using model=%s, ratio=%s, mime=%s",
        number_of_images,
        model_to_use,
        ratio,
        mime_type,
    )
    
    client = _get_genai_client()
    
    try:
        response = client.models.generate_images(
            model=model_to_use,
            prompt=prompt_to_use,
            config=types.GenerateImagesConfig(
                number_of_images=number_of_images,
                aspect_ratio=ratio,
                output_mime_type=mime_type,
                person_generation="ALLOW_ADULT",
            ),
        )
        
        image_bytes_list: list[bytes] = []
        if response and response.generated_images:
            for idx, gen_img in enumerate(response.generated_images):
                if hasattr(gen_img, "image") and hasattr(gen_img.image, "image_bytes"):
                    image_bytes_list.append(gen_img.image.image_bytes)
                else:
                    logger.warning("Generated image at index %d has no image_bytes", idx)
        
        if not image_bytes_list:
            raise RuntimeError("No image bytes returned from Imagen API")
            
        logger.info("Successfully generated %d image(s)", len(image_bytes_list))
        return image_bytes_list
        
    except Exception as e:
        logger.error("Failed to generate images: %s", e)
        raise RuntimeError(f"Imagen generation failed: {e}") from e
