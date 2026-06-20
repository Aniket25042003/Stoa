"""
File: services/core/src/stoa_core/db/__init__.py
Layer: Core Database Access
Purpose: Implements   init   behavior for the core database access.
Dependencies: Supabase, stoa_core
"""

from stoa_core.db.supabase import get_supabase_admin

__all__ = ["get_supabase_admin"]
