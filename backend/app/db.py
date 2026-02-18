from functools import lru_cache

from supabase import create_client, Client

from app.config import get_settings


@lru_cache
def get_supabase_admin() -> Client:
    """Supabase client with service_role key — bypasses RLS.

    Use for worker operations (insert raw_jobs, user_jobs, etc.).
    """
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


@lru_cache
def get_supabase_anon() -> Client:
    """Supabase client with anon key — respects RLS.

    Use for user-facing API calls where we set the auth header.
    """
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_anon_key)


def get_user_client(access_token: str) -> Client:
    """Create a Supabase client authenticated as a specific user.

    This client respects RLS policies scoped to the user.
    """
    settings = get_settings()
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    client.auth.set_session(access_token, "")
    return client
