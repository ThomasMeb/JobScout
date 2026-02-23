"""Worker configuration — reads from environment variables (.env.saas)."""
from functools import lru_cache

from pydantic_settings import BaseSettings


class WorkerSettings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_service_role_key: str

    # DeepSeek LLM
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # Scraper API keys
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""
    france_travail_client_id: str = ""
    france_travail_client_secret: str = ""

    # Email notifications (Resend)
    resend_api_key: str = ""
    notification_from_email: str = "JobScout <noreply@jobscout.app>"

    # Telegram notifications
    telegram_bot_token: str = ""

    # Worker
    cycle_interval_hours: int = 4
    scoring_max_tokens: int = 512
    scoring_temperature: float = 0.2
    max_jobs_per_user_per_cycle: int = 100
    job_lookback_days: int = 7

    # Candidature
    tailoring_max_tokens: int = 2048
    tailoring_temperature: float = 0.3
    cover_letter_max_tokens: int = 1024
    cv_template: str = "classic"

    # Notion
    notion_token: str = ""
    notion_jobs_db_id: str = ""
    notion_companies_db_id: str = ""

    model_config = {"env_file": ".env.saas", "extra": "ignore"}


@lru_cache
def get_settings() -> WorkerSettings:
    return WorkerSettings()


# Default scraper configs (replaces config.yaml sources section)
SCRAPER_CONFIGS = {
    "wttj": {
        "enabled": True,
        "max_results_per_query": 50,
        "delay_between_requests": 5,
    },
    "remoteok": {
        "enabled": True,
        "filter_tags": ["python", "machine-learning", "data-science", "ai", "data"],
    },
    "adzuna": {
        "enabled": True,
        "country": "fr",
        "distance_km": 100,
    },
    "indeed_rss": {
        "enabled": False,
    },
    "francetravail": {
        "enabled": True,
        "contract_types": "CDI",
    },
    "jobspy": {
        "enabled": True,
        "sites": ["indeed", "linkedin"],
        "results_per_query": 25,
        "country": "France",
    },
    "hellowork": {"enabled": False},
    "apec": {"enabled": False},
    "freework": {"enabled": False},
    "welovedevs": {"enabled": False},
}
