"""
File: services/core/src/stoa_core/intelligence/__init__.py
Layer: Core Intelligence Pipeline
Purpose: Implements   init   behavior for the core intelligence pipeline.
Dependencies: stoa_core
"""

from stoa_core.intelligence.icp import build_icp_profile

__all__ = ["build_icp_profile"]
