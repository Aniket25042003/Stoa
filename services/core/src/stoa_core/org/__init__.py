"""
File: services/core/src/stoa_core/org/__init__.py
Layer: Application Source
Purpose: Implements   init   behavior for the application source.
Dependencies: stoa_core
"""

from stoa_core.org.completeness import compute_completeness

__all__ = ["compute_completeness"]
