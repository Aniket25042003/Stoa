"""
File: services/core/src/stoa_core/insights/__init__.py
Layer: Application Source
Purpose: Implements   init   behavior for the application source.
Dependencies: stoa_core
"""

from stoa_core.insights.common import COMMON_QUESTIONS, build_executive_summary, precompute_answers

__all__ = ["COMMON_QUESTIONS", "build_executive_summary", "precompute_answers"]
