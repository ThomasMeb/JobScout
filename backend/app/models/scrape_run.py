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
