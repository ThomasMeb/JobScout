import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth import get_current_user_id
from app.db import get_supabase_admin
from app.models.stats import UserStats

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/", response_model=UserStats)
async def get_stats(
    user_id: Annotated[str, Depends(get_current_user_id)],
):
    """Get KPI stats for the current user."""
    sb = get_supabase_admin()

    # Count by status
    all_jobs = (
        sb.table("user_jobs")
        .select("status, match_score", count="exact")
        .eq("user_id", user_id)
        .execute()
    )
    total = all_jobs.count or 0

    counts = {"new": 0, "interested": 0, "applied": 0, "rejected": 0}
    scores = []
    for row in all_jobs.data:
        s = row.get("status", "new")
        if s in counts:
            counts[s] += 1
        if row.get("match_score") is not None:
            scores.append(row["match_score"])

    avg_score = sum(scores) / len(scores) if scores else None

    # Monthly LLM cost
    month_start = datetime.now(timezone.utc).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    ).isoformat()
    cost_result = (
        sb.table("llm_usage")
        .select("cost_usd")
        .eq("user_id", user_id)
        .gte("created_at", month_start)
        .execute()
    )
    monthly_cost = sum(row.get("cost_usd", 0) for row in cost_result.data)

    # Get budget from profile
    profile = sb.table("profiles").select("monthly_budget_usd").eq("id", user_id).execute()
    budget = float(profile.data[0]["monthly_budget_usd"]) if profile.data else 5.0

    return UserStats(
        total_jobs=total,
        new_jobs=counts["new"],
        interested=counts["interested"],
        applied=counts["applied"],
        rejected=counts["rejected"],
        avg_score=round(avg_score, 1) if avg_score else None,
        monthly_cost_usd=round(monthly_cost, 4),
        budget_remaining_usd=round(max(0, budget - monthly_cost), 4),
    )
