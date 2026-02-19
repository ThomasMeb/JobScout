import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import get_current_user_id
from app.db import get_supabase_admin
from app.models.job import JobFeedback, JobListResponse, JobRead


def _parse_list(val: object) -> list[str]:
    """Parse a value that may be a list or a JSON-encoded string."""
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
    return []

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    user_id: Annotated[str, Depends(get_current_user_id)],
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    min_score: float | None = None,
    status: str | None = None,
    source: str | None = None,
):
    """List scored jobs for the current user with pagination and filters."""
    sb = get_supabase_admin()
    offset = (page - 1) * per_page

    # Build query joining user_jobs with raw_jobs
    query = (
        sb.table("user_jobs")
        .select("*, raw_jobs(*)", count="exact")
        .eq("user_id", user_id)
        .order("match_score", desc=True)
    )

    if min_score is not None:
        query = query.gte("match_score", min_score)
    if status:
        query = query.eq("status", status)

    result = query.range(offset, offset + per_page - 1).execute()

    jobs = []
    for row in result.data:
        raw = row.get("raw_jobs", {})
        if source and raw.get("source") != source:
            continue
        jobs.append(JobRead(
            id=row["id"],
            raw_job_id=row["raw_job_id"],
            title=raw.get("title", ""),
            company=raw.get("company", ""),
            location=raw.get("location"),
            remote_type=raw.get("remote_type", "unknown"),
            salary_min=raw.get("salary_min"),
            salary_max=raw.get("salary_max"),
            salary_currency=raw.get("salary_currency", "EUR"),
            source=raw.get("source", ""),
            source_url=raw.get("source_url", ""),
            apply_url=raw.get("apply_url"),
            tags=_parse_list(raw.get("tags", [])),
            match_score=row.get("match_score"),
            match_reasoning=row.get("match_reasoning"),
            match_keywords=_parse_list(row.get("match_keywords", [])),
            missing_keywords=_parse_list(row.get("missing_keywords", [])),
            match_priority=row.get("match_priority", "low"),
            status=row.get("status", "new"),
            user_notes=row.get("user_notes"),
            posted_at=raw.get("posted_at"),
            scored_at=row.get("scored_at"),
        ))

    return JobListResponse(
        jobs=jobs,
        total=result.count or 0,
        page=page,
        per_page=per_page,
    )


@router.get("/{job_id}", response_model=JobRead)
async def get_job(
    job_id: int,
    user_id: Annotated[str, Depends(get_current_user_id)],
):
    """Get a single scored job detail."""
    sb = get_supabase_admin()
    result = (
        sb.table("user_jobs")
        .select("*, raw_jobs(*)")
        .eq("id", job_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Job not found")

    row = result.data[0]
    raw = row.get("raw_jobs", {})
    return JobRead(
        id=row["id"],
        raw_job_id=row["raw_job_id"],
        title=raw.get("title", ""),
        company=raw.get("company", ""),
        location=raw.get("location"),
        remote_type=raw.get("remote_type", "unknown"),
        salary_min=raw.get("salary_min"),
        salary_max=raw.get("salary_max"),
        salary_currency=raw.get("salary_currency", "EUR"),
        source=raw.get("source", ""),
        source_url=raw.get("source_url", ""),
        apply_url=raw.get("apply_url"),
        tags=_parse_list(raw.get("tags", [])),
        match_score=row.get("match_score"),
        match_reasoning=row.get("match_reasoning"),
        match_keywords=_parse_list(row.get("match_keywords", [])),
        missing_keywords=_parse_list(row.get("missing_keywords", [])),
        match_priority=row.get("match_priority", "low"),
        status=row.get("status", "new"),
        user_notes=row.get("user_notes"),
        posted_at=raw.get("posted_at"),
        scored_at=row.get("scored_at"),
    )


@router.patch("/{job_id}/feedback", response_model=JobRead)
async def update_feedback(
    job_id: int,
    feedback: JobFeedback,
    user_id: Annotated[str, Depends(get_current_user_id)],
):
    """Update job feedback (interested/rejected/applied)."""
    valid_statuses = {"interested", "rejected", "applied", "new"}
    if feedback.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid_statuses}",
        )

    sb = get_supabase_admin()
    data = {"status": feedback.status}
    if feedback.user_notes is not None:
        data["user_notes"] = feedback.user_notes

    result = (
        sb.table("user_jobs")
        .update(data)
        .eq("id", job_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Job not found")

    # Fetch full job with raw_jobs join for response
    return await get_job(job_id, user_id)
