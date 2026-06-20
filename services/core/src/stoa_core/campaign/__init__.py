"""
File: services/core/src/stoa_core/campaign/__init__.py
Layer: Core Campaign Generation
Purpose: Implements   init   behavior for the core campaign generation.
Dependencies: stoa_core
"""

from stoa_core.campaign.generate import generate_campaign_assets

__all__ = ["generate_campaign_assets"]
