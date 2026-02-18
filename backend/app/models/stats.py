from pydantic import BaseModel


class UserStats(BaseModel):
    total_jobs: int = 0
    new_jobs: int = 0
    interested: int = 0
    applied: int = 0
    rejected: int = 0
    avg_score: float | None = None
    monthly_cost_usd: float = 0.0
    budget_remaining_usd: float = 0.0
