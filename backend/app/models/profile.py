from pydantic import BaseModel, Field


class ProfileRead(BaseModel):
    id: str
    name: str | None = None
    cv_text: str | None = None
    profile_summary: str | None = None
    search_queries: list[str] = []
    search_locations: list[str] = []
    remote_accepted: bool = True
    min_salary: int | None = Field(default=None, ge=0, le=500_000)
    bonus_keywords: list[str] = []
    penalty_keywords: list[str] = []
    min_score_notify: int = Field(default=70, ge=0, le=100)
    telegram_chat_id: str | None = None
    notification_email: str | None = None
    monthly_budget_usd: float = Field(default=5.0, ge=0.0, le=100.0)
    onboarding_completed: bool = False
    plan: str = "free"


class ProfileUpdate(BaseModel):
    name: str | None = None
    cv_text: str | None = None
    profile_summary: str | None = None
    search_queries: list[str] | None = None
    search_locations: list[str] | None = None
    remote_accepted: bool | None = None
    min_salary: int | None = Field(default=None, ge=0, le=500_000)
    bonus_keywords: list[str] | None = None
    penalty_keywords: list[str] | None = None
    min_score_notify: int | None = Field(default=None, ge=0, le=100)
    telegram_chat_id: str | None = None
    notification_email: str | None = None
    monthly_budget_usd: float | None = Field(default=None, ge=0.0, le=100.0)
    onboarding_completed: bool | None = None
