from pydantic import BaseModel


class ProfileRead(BaseModel):
    id: str
    name: str | None = None
    cv_text: str | None = None
    profile_summary: str | None = None
    search_queries: list[str] = []
    search_locations: list[str] = []
    remote_accepted: bool = True
    min_salary: int | None = None
    bonus_keywords: list[str] = []
    penalty_keywords: list[str] = []
    min_score_notify: int = 70
    telegram_chat_id: str | None = None
    notification_email: str | None = None
    monthly_budget_usd: float = 5.0
    onboarding_completed: bool = False


class ProfileUpdate(BaseModel):
    name: str | None = None
    cv_text: str | None = None
    profile_summary: str | None = None
    search_queries: list[str] | None = None
    search_locations: list[str] | None = None
    remote_accepted: bool | None = None
    min_salary: int | None = None
    bonus_keywords: list[str] | None = None
    penalty_keywords: list[str] | None = None
    min_score_notify: int | None = None
    telegram_chat_id: str | None = None
    notification_email: str | None = None
    monthly_budget_usd: float | None = None
    onboarding_completed: bool | None = None
