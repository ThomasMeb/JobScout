import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Paths
PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
DB_PATH = DATA_DIR / "jobs.db"
APPLICATIONS_DIR = DATA_DIR / "applications"
TEMPLATES_DIR = PROJECT_DIR / "templates"
CONFIG_PATH = PROJECT_DIR / "config.yaml"

# Load .env
load_dotenv(PROJECT_DIR / ".env")

# Environment variables
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
ADZUNA_APP_ID = os.environ.get("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.environ.get("ADZUNA_APP_KEY", "")
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "")
NOTION_COMPANIES_DB_ID = os.environ.get("NOTION_COMPANIES_DB_ID", "")


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def load_profile_text() -> str:
    """Load the full profile document for LLM scoring."""
    cfg = load_config()
    profile_path = Path(cfg["profile"]["profile_doc"])
    return profile_path.read_text(encoding="utf-8")


def load_cv(language: str = "fr") -> str:
    """Load CV master in the specified language."""
    cfg = load_config()
    key = f"cv_{language}"
    cv_path = Path(cfg["profile"][key])
    return cv_path.read_text(encoding="utf-8")
