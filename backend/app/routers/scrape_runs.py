import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from supabase import Client

from app.auth import get_current_user_id, get_rls_supabase
from app.models.scrape_run import ScrapeRun

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
