import logging
from datetime import datetime, timezone

from fastapi import APIRouter

from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/health")
async def health():
    """Basic health check with DB connectivity."""
    settings = get_settings()
    result = {"status": "ok"}
    try:
        from supabase import create_client
        sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
        sb.table("profiles").select("id").limit(1).execute()
        result["db"] = "ok"
    except Exception:
        result["status"] = "degraded"
        result["db"] = "unreachable"
    return result


@router.get("/api/health/full")
async def health_full():
    """Full health check including worker heartbeat status."""
    settings = get_settings()
    result = {"api": "ok", "worker": "unknown", "db": "ok"}

    try:
        from supabase import create_client
        sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
        hb = sb.table("worker_heartbeats").select("*").eq("id", "main").maybe_single().execute()

        if hb.data:
            last_cycle = hb.data.get("last_cycle_at")
            status = hb.data.get("status", "unknown")
            result["worker"] = status
            result["worker_cycles"] = hb.data.get("cycle_count", 0)
            result["worker_error"] = hb.data.get("error_message")

            if last_cycle:
                last_dt = datetime.fromisoformat(last_cycle.replace("Z", "+00:00"))
                age_hours = (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600
                result["worker_last_cycle_hours_ago"] = round(age_hours, 1)
                if age_hours > 8:
                    result["worker"] = "stale"
        else:
            result["worker"] = "no_heartbeat"
    except Exception:
        result["db"] = "unreachable"
        result["worker"] = "check_failed"

    return result
