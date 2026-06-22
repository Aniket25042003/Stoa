"""
File: services/core/src/stoa_core/content/enrich.py
Layer: Core Content Generation
Purpose: Ground and enrich generation prompts with brand, ICP, and campaign context.
Dependencies: stoa_core
"""

from __future__ import annotations

import logging
from typing import Any

from stoa_core.db.supabase import get_supabase_admin
from stoa_core.llm.router import invoke_text
from stoa_core.rag.retrieve import retrieve_context

logger = logging.getLogger(__name__)

CONTENT_ENRICH_SYSTEM = """You are an expert creative director and copywriter.
Your task is to enrich a user's prompt for AI {asset_type} generation (Imagen/Veo)
using the provided brand, ICP, and campaign context.

The user wants to generate a: {asset_type}
Their original prompt/brief: "{user_prompt}"

Based on the brand identity, target audience (ICP), competitive positioning, and
campaign goals provided below, synthesize a highly detailed, descriptive prompt
suitable for a generative model.
- Keep the core concept from the user's brief.
- Incorporate specific visual style, mood, colors, and tone consistent with the brand.
- If targeting a specific ICP, detail visual elements that appeal to that demographic.
- For images: describe subject, lighting, composition, style (e.g. realistic,
  illustration, flat design), and medium.
- For videos: describe the subject, camera movement, motion speed, transitions,
  and pacing (5-second clip).
- Do not mention the names of real persons, and do not use trademarked company
  names in the final prompt.
- The output MUST only be the enriched prompt itself. Do not include any intro,
  explanations, or quotes. Just output the final enriched prompt text."""


def enrich_content_prompt(
    org_id: str,
    user_prompt: str,
    *,
    campaign_id: str | None = None,
    asset_type: str = "image",
) -> tuple[str, list[dict[str, Any]]]:
    """Enrich a user's generation prompt with KB context.

    1. Retrieves relevant context from the unified KB (ICP, brand voice,
       competitive data, past content assets).
    2. If linked to a campaign, loads campaign details from the DB.
    3. Uses a standard LLM call to synthesize an enriched prompt.
    4. Returns (enriched_prompt, context_refs) for provenance tracking.
    """
    logger.info(
        "Enriching prompt for org_id=%s, type=%s, campaign=%s",
        org_id,
        asset_type,
        campaign_id,
    )

    # 1. Retrieve context from Knowledge Base
    kinds = [
        "company_profile",
        "icp_profile",
        "campaign_asset",
        "competitive_snapshot",
        "document",
        "content_asset",
    ]
    
    # Retrieve relevant context items
    kb_items = retrieve_context(org_id, query=user_prompt, kinds=kinds)
    
    context_text_blocks = []
    context_refs = []
    
    for item in kb_items:
        ref = item.get("ref")
        kind = item.get("kind")
        text = item.get("text")
        title = item.get("item_title") or ""
        
        context_refs.append({
            "ref": ref,
            "kind": kind,
            "title": title,
        })
        context_text_blocks.append(f"[Source: {kind} - {title}]\n{text}")

    # 2. Add Linked Campaign context if provided
    campaign_brief = ""
    campaign_voice = ""
    if campaign_id:
        try:
            sb = get_supabase_admin()
            res = sb.table("campaigns").select("*").eq("id", campaign_id).execute()
            if res.data:
                campaign = res.data[0]
                campaign_brief = campaign.get("brief") or ""
                campaign_voice = campaign.get("brand_voice") or ""
                logger.info("Retrieved linked campaign context: %s", campaign.get("id"))
                context_text_blocks.append(
                    f"[Linked Campaign Brief]\n{campaign_brief}\n\n[Brand Voice]\n{campaign_voice}"
                )
        except Exception as e:
            logger.warning("Failed to retrieve linked campaign context: %s", e)

    # 3. Build Prompt for LLM Router
    kb_context_summary = "\n\n".join(context_text_blocks)
    
    user_message = f"""Here is the context for the enrichment:

--- KNOWLEDGE BASE & BRAND CONTEXT ---
{kb_context_summary}

--- USER REQUEST ---
Brief: {user_prompt}
Asset Type: {asset_type}

Enriched Prompt:"""

    system_message = CONTENT_ENRICH_SYSTEM.format(asset_type=asset_type, user_prompt=user_prompt)

    try:
        enriched_prompt, _ = invoke_text(
            system=system_message,
            user=user_message,
            task_name="content_enrich",
        )
        
        if not enriched_prompt:
            logger.warning("LLM returned empty enriched prompt, falling back to original prompt")
            enriched_prompt = user_prompt
            
        enriched_prompt = enriched_prompt.strip().strip('"').strip("'")
        logger.info("Prompt enriched successfully: '%s...'", enriched_prompt[:60])
        return enriched_prompt, context_refs
        
    except Exception as e:
        logger.error("Failed to enrich prompt via LLM: %s", e)
        # Fall back to original user prompt with empty references
        return user_prompt, context_refs
