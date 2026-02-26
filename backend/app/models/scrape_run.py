from pydantic import BaseModel


class ScrapeRun(BaseModel):
    id: int
    source: str
    jobs_found: int = 0
    jobs_new: int = 0
    status: str = "running"
    error_message: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    duration_seconds: float | None = None


class ScraperHealthMetrics(BaseModel):
    source: str
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    success_rate: float = 0.0
    avg_duration_seconds: float | None = None
    avg_jobs_found: float = 0.0
    last_run_at: str | None = None
    last_error: str | None = None
