"""Supabase client and shared DB helpers for the worker."""
from datetime import datetime, timezone
from functools import lru_cache

from supabase import create_client, Client

from worker.config import get_settings


@lru_cache
def get_supabase() -> Client:
    """Supabase client with service_role key — full access for worker operations."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def get_user_monthly_cost(sb: Client, user_id: str) -> float:
    """Get total LLM cost for a user this month."""
    month_start = datetime.now(timezone.utc).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    ).isoformat()
    result = (
        sb.table("llm_usage")
        .select("cost_usd")
        .eq("user_id", user_id)
        .gte("created_at", month_start)
        .execute()
    )
    return sum(row.get("cost_usd", 0) for row in (result.data or []))
