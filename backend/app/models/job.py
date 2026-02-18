from datetime import datetime
from pydantic import BaseModel


class JobRead(BaseModel):
    id: int
    raw_job_id: int
    title: str
    company: str
    location: str | None = None
    remote_type: str = "unknown"
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str = "EUR"
    source: str
    source_url: str
    apply_url: str | None = None
    tags: list[str] = []
    match_score: float | None = None
    match_reasoning: str | None = None
    match_keywords: list[str] = []
    missing_keywords: list[str] = []
    match_priority: str = "low"
    status: str = "new"
    user_notes: str | None = None
    posted_at: datetime | None = None
    scored_at: datetime | None = None


class JobFeedback(BaseModel):
    status: str  # interested, rejected, applied
    user_notes: str | None = None


class JobListResponse(BaseModel):
    jobs: list[JobRead]
    total: int
    page: int
    per_page: int
