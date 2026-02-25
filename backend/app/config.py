from pathlib import Path

from pydantic_settings import BaseSettings
from functools import lru_cache

_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env.saas"


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_jwt_secret: str

    # DeepSeek LLM
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    # Scraper API keys
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""
    france_travail_client_id: str = ""
    france_travail_client_secret: str = ""

    # Observability
    sentry_dsn: str = ""

    # Stripe billing
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_pro_price_id: str = ""
    frontend_url: str = "http://localhost:3000"

    # App
    environment: str = "development"
    cors_origins: str = "http://localhost:3000"

    model_config = {"env_file": str(_ENV_FILE), "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    missing = []
    if not s.supabase_url:
        missing.append("SUPABASE_URL")
    if not s.supabase_anon_key:
        missing.append("SUPABASE_ANON_KEY")
    if not s.supabase_service_role_key:
        missing.append("SUPABASE_SERVICE_ROLE_KEY")
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
    return s
