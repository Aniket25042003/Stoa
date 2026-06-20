"""
File: services/core/src/stoa_core/competitive/__init__.py
Layer: Core Competitive Intelligence
Purpose: Implements   init   behavior for the core competitive intelligence.
Dependencies: stoa_core
"""

from stoa_core.competitive.monitor import detect_changes, fetch_page_text

__all__ = ["detect_changes", "fetch_page_text"]
