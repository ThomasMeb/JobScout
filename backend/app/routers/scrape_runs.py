import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.auth import get_current_user_id
from app.db import get_supabase_admin
from app.models.scrape_run import ScrapeRun

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scrape-runs", tags=["scrape_runs"])


@router.get("/", response_model=list[ScrapeRun])
async def list_scrape_runs(
    _user_id: Annotated[str, Depends(get_current_user_id)],
    limit: int = Query(20, ge=1, le=100),
):
    """List recent scrape runs (most recent first)."""
    sb = get_supabase_admin()
    result = (
        sb.table("scrape_runs")
        .select("*")
        .order("started_at", desc=True)
        .limit(limit)
        .execute()
    )
    return [ScrapeRun(**row) for row in result.data]
