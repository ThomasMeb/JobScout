import csv
import io
import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from supabase import Client

from app.auth import get_current_user_id, get_rls_supabase
from app.models.job import BulkFeedback, JobFeedback, JobListResponse, JobRead
from app.rate_limit import limiter


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
    sb: Annotated[Client, Depends(get_rls_supabase)],
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    min_score: float | None = Query(default=None, ge=0, le=100),
    status: str | None = Query(default=None, pattern="^(new|interested|rejected|applied)$"),
    source: str | None = None,
    search: str | None = Query(default=None, max_length=200),
):
    """List scored jobs for the current user with pagination and filters."""
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
    if source:
        query = query.eq("raw_jobs.source", source)
    if search:
        # Full-text search on title and company via PostgREST ilike
        query = query.or_(
            f"raw_jobs.title.ilike.%{search}%,raw_jobs.company.ilike.%{search}%"
        )

    result = query.range(offset, offset + per_page - 1).execute()

    jobs = []
    for row in result.data:
        raw = row.get("raw_jobs", {})
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
    sb: Annotated[Client, Depends(get_rls_supabase)],
):
    """Get a single scored job detail."""
    result = (
        sb.table("user_jobs")
        .select("*, raw_jobs(*)")
        .eq("id", job_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Offre non trouvée")

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
    sb: Annotated[Client, Depends(get_rls_supabase)],
):
    """Update job feedback (interested/rejected/applied)."""
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
        raise HTTPException(status_code=404, detail="Offre non trouvée")

    # Fetch full job with raw_jobs join for response
    return await get_job(job_id, user_id, sb)


@router.patch("/bulk/feedback")
async def bulk_feedback(
    payload: BulkFeedback,
    user_id: Annotated[str, Depends(get_current_user_id)],
    sb: Annotated[Client, Depends(get_rls_supabase)],
):
    """Update status for multiple jobs at once."""
    if len(payload.job_ids) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 offres par opération groupée")

    updated = 0
    for job_id in payload.job_ids:
        result = (
            sb.table("user_jobs")
            .update({"status": payload.status})
            .eq("id", job_id)
            .eq("user_id", user_id)
            .execute()
        )
        if result.data:
            updated += 1

    return {"updated": updated}


@router.get("/export/csv")
@limiter.limit("5/minute")
async def export_jobs_csv(
    request: Request,
    user_id: Annotated[str, Depends(get_current_user_id)],
    sb: Annotated[Client, Depends(get_rls_supabase)],
    min_score: float | None = Query(default=None, ge=0, le=100),
    status: str | None = Query(default=None, pattern="^(new|interested|rejected|applied)$"),
):
    """Export all scored jobs as CSV."""
    query = (
        sb.table("user_jobs")
        .select("match_score, match_priority, match_keywords, missing_keywords, "
                "match_reasoning, status, user_notes, scored_at, "
                "raw_jobs(title, company, location, remote_type, salary_min, "
                "salary_max, salary_currency, source, source_url, apply_url)")
        .eq("user_id", user_id)
        .order("match_score", desc=True)
        .limit(1000)
    )
    if min_score is not None:
        query = query.gte("match_score", min_score)
    if status:
        query = query.eq("status", status)

    result = query.execute()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Titre", "Entreprise", "Lieu", "Télétravail", "Score", "Priorité",
        "Statut", "Source", "URL", "URL candidature",
        "Salaire min", "Salaire max", "Devise",
        "Mots-clés correspondants", "Mots-clés manquants", "Analyse", "Notes", "Évalué le",
    ])

    for row in result.data or []:
        raw = row.get("raw_jobs") or {}
        writer.writerow([
            raw.get("title", ""),
            raw.get("company", ""),
            raw.get("location", ""),
            raw.get("remote_type", ""),
            row.get("match_score", ""),
            row.get("match_priority", ""),
            row.get("status", ""),
            raw.get("source", ""),
            raw.get("source_url", ""),
            raw.get("apply_url", ""),
            raw.get("salary_min", ""),
            raw.get("salary_max", ""),
            raw.get("salary_currency", ""),
            ", ".join(_parse_list(row.get("match_keywords", []))),
            ", ".join(_parse_list(row.get("missing_keywords", []))),
            row.get("match_reasoning", ""),
            row.get("user_notes", ""),
            row.get("scored_at", ""),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=jobscout-export.csv"},
    )
