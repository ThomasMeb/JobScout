from datetime import datetime, timezone

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter()


@router.get("/api/health")
async def health():
    """Basic health check."""
    return {"status": "ok"}


@router.get("/api/health/full")
async def health_full():
    """Full health check including worker heartbeat status."""
    settings = get_settings()
    result = {"api": "ok", "worker": "unknown"}

    try:
        from supabase import create_client
        sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
        hb = sb.table("worker_heartbeats").select("*").eq("id", "main").maybe_single().execute()

        if hb.data:
            last_cycle = hb.data.get("last_cycle_at")
            status = hb.data.get("status", "unknown")
            result["worker"] = status
            result["worker_cycles"] = hb.data.get("cycle_count", 0)

            if last_cycle:
                last_dt = datetime.fromisoformat(last_cycle.replace("Z", "+00:00"))
                age_hours = (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600
                result["worker_last_cycle_hours_ago"] = round(age_hours, 1)
                # Stale if no cycle in 8+ hours (2x default 4h interval)
                if age_hours > 8:
                    result["worker"] = "stale"
        else:
            result["worker"] = "no_heartbeat"
    except Exception:
        result["worker"] = "check_failed"

    return result
