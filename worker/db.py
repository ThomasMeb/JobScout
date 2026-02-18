"""Supabase client for the worker — uses service_role key (bypasses RLS)."""
from functools import lru_cache

from supabase import create_client, Client

from worker.config import get_settings


@lru_cache
def get_supabase() -> Client:
    """Supabase client with service_role key — full access for worker operations."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
