import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from supabase import Client

from app.auth import get_current_user_id, get_rls_supabase
from app.models.scrape_run import ScrapeRun, ScraperHealthMetrics

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scrape-runs", tags=["scrape_runs"])


@router.get("/", response_model=list[ScrapeRun])
async def list_scrape_runs(
    _user_id: Annotated[str, Depends(get_current_user_id)],
    sb: Annotated[Client, Depends(get_rls_supabase)],
    limit: int = Query(20, ge=1, le=100),
):
    """List recent scrape runs (most recent first)."""
    result = (
        sb.table("scrape_runs")
        .select("*")
        .order("started_at", desc=True)
        .limit(limit)
        .execute()
    )
    return [ScrapeRun(**row) for row in result.data]


@router.get("/health", response_model=list[ScraperHealthMetrics])
async def scraper_health(
    _user_id: Annotated[str, Depends(get_current_user_id)],
    sb: Annotated[Client, Depends(get_rls_supabase)],
    days: int = Query(7, ge=1, le=30),
):
    """Per-scraper health metrics over the last N days."""
    from datetime import datetime, timedelta, timezone
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    result = (
        sb.table("scrape_runs")
        .select("source, status, jobs_found, duration_seconds, error_message, started_at")
        .gte("started_at", cutoff)
        .order("started_at", desc=True)
        .limit(500)
        .execute()
    )

    # Aggregate per source
    sources: dict[str, dict] = {}
    for row in (result.data or []):
        src = row["source"]
        if src not in sources:
            sources[src] = {
                "source": src, "total_runs": 0, "successful_runs": 0,
                "failed_runs": 0, "durations": [], "jobs_found_list": [],
                "last_run_at": None, "last_error": None,
            }
        s = sources[src]
        s["total_runs"] += 1
        if row["status"] == "success":
            s["successful_runs"] += 1
        else:
            s["failed_runs"] += 1
            if not s["last_error"]:
                s["last_error"] = row.get("error_message")
        if row.get("duration_seconds") is not None:
            s["durations"].append(row["duration_seconds"])
        s["jobs_found_list"].append(row.get("jobs_found") or 0)
        if not s["last_run_at"]:
            s["last_run_at"] = row.get("started_at")

    metrics = []
    for s in sources.values():
        total = s["total_runs"]
        durations = s["durations"]
        metrics.append(ScraperHealthMetrics(
            source=s["source"],
            total_runs=total,
            successful_runs=s["successful_runs"],
            failed_runs=s["failed_runs"],
            success_rate=round(s["successful_runs"] / total * 100, 1) if total else 0,
            avg_duration_seconds=round(sum(durations) / len(durations), 2) if durations else None,
            avg_jobs_found=round(sum(s["jobs_found_list"]) / total, 1) if total else 0,
            last_run_at=s["last_run_at"],
            last_error=s["last_error"],
        ))

    metrics.sort(key=lambda m: m.source)
    return metrics
