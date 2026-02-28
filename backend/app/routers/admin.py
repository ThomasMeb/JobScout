"""Admin endpoints — user management, scraper health, business metrics."""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from supabase import create_client

from app.auth import get_current_user_id
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])


def _get_admin_sb():
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def _require_admin(user_id: Annotated[str, Depends(get_current_user_id)]) -> str:
    """Check is_admin flag in profiles table."""
    sb = _get_admin_sb()
    row = sb.table("profiles").select("is_admin").eq("id", user_id).maybe_single().execute()
    if not row.data or not row.data.get("is_admin"):
        raise HTTPException(status_code=403, detail="Accès administrateur requis")
    return user_id


@router.get("/users")
async def list_users(admin_id: Annotated[str, Depends(_require_admin)]):
    """List all users with plan and usage info."""
    sb = _get_admin_sb()
    profiles = (
        sb.table("profiles")
        .select("id, name, notification_email, plan, onboarding_completed, created_at, updated_at")
        .order("created_at", desc=True)
        .execute()
    )

    users = []
    for p in profiles.data or []:
        # Count user jobs
        jobs_count = (
            sb.table("user_jobs")
            .select("id", count="exact")
            .eq("user_id", p["id"])
            .execute()
        )
        users.append({
            **p,
            "total_jobs": jobs_count.count or 0,
        })

    return {"users": users, "total": len(users)}


@router.get("/scrapers")
async def scraper_health(admin_id: Annotated[str, Depends(_require_admin)]):
    """Get scraper health metrics from recent runs."""
    sb = _get_admin_sb()
    runs = (
        sb.table("scrape_runs")
        .select("source, status, jobs_found, jobs_new, error_message, started_at, finished_at")
        .order("started_at", desc=True)
        .limit(50)
        .execute()
    )

    # Aggregate per source
    sources: dict = {}
    for run in runs.data or []:
        src = run.get("source", "unknown")
        if src not in sources:
            sources[src] = {
                "source": src,
                "total_runs": 0,
                "success_runs": 0,
                "total_jobs_found": 0,
                "total_jobs_new": 0,
                "last_run": None,
                "last_error": None,
            }
        s = sources[src]
        s["total_runs"] += 1
        if run.get("status") == "success":
            s["success_runs"] += 1
        s["total_jobs_found"] += run.get("jobs_found") or 0
        s["total_jobs_new"] += run.get("jobs_new") or 0
        if not s["last_run"]:
            s["last_run"] = run.get("started_at")
        if run.get("error_message") and not s["last_error"]:
            s["last_error"] = run["error_message"]

    for s in sources.values():
        s["success_rate"] = round(s["success_runs"] / s["total_runs"] * 100) if s["total_runs"] > 0 else 0

    return {"scrapers": list(sources.values())}


@router.get("/metrics")
async def business_metrics(admin_id: Annotated[str, Depends(_require_admin)]):
    """Get business metrics: users, plans, jobs."""
    sb = _get_admin_sb()

    total_users = sb.table("profiles").select("id", count="exact").execute()
    pro_users = sb.table("profiles").select("id", count="exact").eq("plan", "pro").execute()
    total_jobs = sb.table("raw_jobs").select("id", count="exact").execute()
    total_scored = sb.table("user_jobs").select("id", count="exact").execute()

    # Worker heartbeat
    hb = sb.table("worker_heartbeats").select("*").eq("id", "main").maybe_single().execute()

    return {
        "total_users": total_users.count or 0,
        "pro_users": pro_users.count or 0,
        "total_raw_jobs": total_jobs.count or 0,
        "total_scored_jobs": total_scored.count or 0,
        "worker_status": (hb.data or {}).get("status", "unknown"),
        "worker_cycles": (hb.data or {}).get("cycle_count", 0),
        "worker_last_cycle": (hb.data or {}).get("last_cycle_at"),
    }
