"""
File: services/core/src/stoa_core/db/supabase.py
Layer: Core Database Access
Purpose: Implements supabase behavior for the core database access.
Dependencies: Supabase, stoa_core
"""


from __future__ import annotations

from functools import lru_cache

from supabase import Client, create_client

from stoa_core.config import get_settings


@lru_cache
def get_supabase_admin() -> Client:
    """Handles get supabase admin logic for the surrounding Stoa workflow.

    Returns:
        Client: Result produced for the caller.
    """
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required")
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


@lru_cache
def get_supabase_anon() -> Client:
    """Handles get supabase anon logic for the surrounding Stoa workflow.

    Returns:
        Client: Result produced for the caller.
    """
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_ANON_KEY required")
    return create_client(settings.supabase_url, settings.supabase_anon_key)
