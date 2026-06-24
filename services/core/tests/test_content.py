"""
File: services/core/tests/test_content.py
Layer: Core Unit Tests
Purpose: Verifies business logic for prompt enrichment and AI asset generation wrappers.
Dependencies: pytest, unittest.mock, stoa_core
"""

from __future__ import annotations

from unittest.mock import ANY, MagicMock, patch

from stoa_core.content.enrich import enrich_content_prompt
from stoa_core.content.generate_image import generate_images
from stoa_core.content.generate_video import generate_video


def test_enrich_content_prompt_basic() -> None:
    """Verifies that enrich_content_prompt retrieves context and synthesizes using LLM."""
    mock_kb_items = [
        {
            "ref": "kb:icp_profile:123:abc",
            "kind": "icp_profile",
            "text": "Target audience B2B marketers.",
            "item_title": "B2B ICP"
        },
        {
            "ref": "kb:company_profile:123:xyz",
            "kind": "company_profile",
            "text": "Brand is professional and bold.",
            "item_title": "Brand Guidelines"
        }
    ]
    
    mock_campaign = {
        "id": "camp-1",
        "brief": "Launch SaaS feature",
        "brand_voice": "energetic",
    }

    with (
        patch("stoa_core.content.enrich.retrieve_context", return_value=mock_kb_items) as mock_ret,
        patch("stoa_core.content.enrich.verify_org_resource", return_value=mock_campaign),
        patch(
            "stoa_core.content.enrich.invoke_text",
            return_value=("A sleek, professional banner for B2B marketers.", "vertex"),
        ) as mock_invoke,
    ):
         
        enriched, refs = enrich_content_prompt(
            org_id="org-1",
            user_prompt="Hero banner for SaaS feature",
            campaign_id="camp-1",
            asset_type="image"
        )
        
        assert enriched == "A sleek, professional banner for B2B marketers."
        assert len(refs) == 2
        assert refs[0]["kind"] == "icp_profile"
        assert refs[1]["kind"] == "company_profile"
        mock_ret.assert_called_once_with(
            "org-1",
            query="Hero banner for SaaS feature",
            kinds=ANY
        )
        mock_invoke.assert_called_once()


def test_generate_images_success() -> None:
    """Verifies that generate_images calls Vertex AI client and extracts image bytes."""
    mock_image_bytes = b"mock-png-data"
    
    # Mock Response structure for google-genai
    mock_image_obj = MagicMock()
    mock_image_obj.image.image_bytes = mock_image_bytes
    
    mock_response = MagicMock()
    mock_response.generated_images = [mock_image_obj]
    
    mock_client = MagicMock()
    mock_client.models.generate_images.return_value = mock_response
    
    with patch("stoa_core.content.generate_image._get_genai_client", return_value=mock_client):
        res = generate_images(
            prompt="A futuristic city in obsidian and silver theme",
            aspect_ratio="16:9",
            number_of_images=1
        )
        
        assert len(res) == 1
        assert res[0] == mock_image_bytes
        mock_client.models.generate_images.assert_called_once()


def test_generate_video_success() -> None:
    """Verifies that generate_video enqueues Veo operation, polls status, and downloads bytes."""
    mock_video_bytes = b"mock-mp4-data"
    
    # Mock operation polling
    mock_operation = MagicMock()
    mock_operation.done = True
    mock_operation.name = "op-123"
    mock_operation.error = None
    
    # Mock video file download
    mock_video_file_ref = MagicMock()
    mock_video_obj = MagicMock()
    mock_video_obj.video = mock_video_file_ref
    
    mock_operation.response.generated_videos = [mock_video_obj]
    
    mock_download_res = MagicMock()
    mock_download_res.content = mock_video_bytes
    
    mock_client = MagicMock()
    mock_client.models.generate_videos.return_value = mock_operation
    mock_client.operations.get.return_value = mock_operation
    mock_client.files.download.return_value = mock_download_res
    
    with patch("stoa_core.content.generate_video._get_genai_client", return_value=mock_client):
        res = generate_video(
            prompt="Cinematic camera pan around futuristic office",
            aspect_ratio="16:9",
            resolution="720p"
        )
        
        assert res == mock_video_bytes
        mock_client.models.generate_videos.assert_called_once()
        mock_client.files.download.assert_called_once_with(file=mock_video_file_ref)
