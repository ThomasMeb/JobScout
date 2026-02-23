"""Notion CRM sync — push jobs and companies to Notion databases.

Adapted from legacy/job_agent/notion_sync.py for multi-tenant SaaS (Supabase).
"""

import json
import logging

import httpx

from worker.config import get_settings
from worker.db import get_supabase

logger = logging.getLogger(__name__)

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _headers() -> dict:
    settings = get_settings()
    return {
        "Authorization": f"Bearer {settings.notion_token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _notion_request(method: str, path: str, body: dict | None = None) -> dict | None:
    settings = get_settings()
    if not settings.notion_token:
        return None

    url = f"{NOTION_API}/{path}"
    try:
        with httpx.Client(timeout=30) as client:
            if method == "GET":
                resp = client.get(url, headers=_headers())
            elif method == "POST":
                resp = client.post(url, headers=_headers(), json=body or {})
            elif method == "PATCH":
                resp = client.patch(url, headers=_headers(), json=body or {})
            else:
                return None
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.error(f"Notion API error ({method} {path}): {e}")
        return None


def setup_databases():
    """Create all required properties in the Jobs and Companies Notion databases."""
    settings = get_settings()
    jobs_db = settings.notion_jobs_db_id
    companies_db = settings.notion_companies_db_id

    success = True
    if jobs_db:
        result = _notion_request("PATCH", f"databases/{jobs_db}", {
            "properties": {
                "Titre": {"title": {}},
                "Entreprise": {"rich_text": {}},
                "Score": {"number": {"format": "number"}},
                "Statut": {"select": {"options": [
                    {"name": "Nouveau", "color": "blue"},
                    {"name": "Notifié", "color": "yellow"},
                    {"name": "Intéressé", "color": "green"},
                    {"name": "Rejeté", "color": "red"},
                    {"name": "Postulé", "color": "purple"},
                ]}},
                "Source": {"select": {"options": [
                    {"name": "wttj", "color": "yellow"},
                    {"name": "adzuna", "color": "blue"},
                    {"name": "francetravail", "color": "red"},
                    {"name": "remoteok", "color": "green"},
                    {"name": "jobspy_indeed", "color": "orange"},
                ]}},
                "Localisation": {"rich_text": {}},
                "Lien offre": {"url": {}},
                "Remote": {"select": {"options": [
                    {"name": "full", "color": "green"},
                    {"name": "hybrid", "color": "yellow"},
                    {"name": "onsite", "color": "red"},
                ]}},
                "Keywords": {"rich_text": {}},
                "Reasoning": {"rich_text": {}},
                "Priorité": {"select": {"options": [
                    {"name": "high", "color": "red"},
                    {"name": "medium", "color": "yellow"},
                    {"name": "low", "color": "gray"},
                ]}},
                "Salaire": {"rich_text": {}},
                "Date scrape": {"date": {}},
            },
        })
        if result:
            logger.info("Notion Jobs database properties created")
        else:
            success = False

    if companies_db:
        result = _notion_request("PATCH", f"databases/{companies_db}", {
            "properties": {
                "Nom": {"title": {}},
                "Statut": {"select": {"options": [
                    {"name": "En attente", "color": "blue"},
                    {"name": "Préparé", "color": "yellow"},
                    {"name": "Envoyé", "color": "green"},
                    {"name": "Rejeté", "color": "red"},
                ]}},
                "Source": {"select": {"options": [
                    {"name": "manual", "color": "blue"},
                    {"name": "labonneboite", "color": "green"},
                ]}},
                "Site": {"url": {}},
                "Localisation": {"rich_text": {}},
                "Secteur": {"rich_text": {}},
                "Score": {"number": {"format": "number"}},
            },
        })
        if result:
            logger.info("Notion Companies database properties created")
        else:
            success = False

    return success


async def sync_jobs_to_notion(user_id: str) -> int:
    """Push high-scoring jobs without a notion_page_id to Notion. Returns count synced."""
    settings = get_settings()
    if not settings.notion_token or not settings.notion_jobs_db_id:
        return 0

    sb = get_supabase()

    # Get user's min_score_notify as threshold
    profile = sb.table("profiles").select("min_score_notify").eq("id", user_id).single().execute()
    min_score = (profile.data or {}).get("min_score_notify") or 70

    # Get unsynced jobs
    jobs = (
        sb.table("user_jobs")
        .select("id, match_score, match_priority, match_keywords, match_reasoning, status, "
                "raw_jobs(title, company, location, source, source_url, remote_type, "
                "salary_min, salary_max, salary_currency, scraped_at)")
        .eq("user_id", user_id)
        .gte("match_score", min_score)
        .is_("notion_page_id", "null")
        .order("match_score", desc=True)
        .limit(50)
        .execute()
    )

    if not jobs.data:
        return 0

    synced = 0
    for job in jobs.data:
        result = _notion_request("POST", "pages", {
            "parent": {"database_id": settings.notion_jobs_db_id},
            "properties": _job_to_notion_properties(job),
        })
        if result and result.get("id"):
            sb.table("user_jobs").update({"notion_page_id": result["id"]}).eq("id", job["id"]).execute()
            synced += 1
        else:
            logger.error(f"Notion sync failed for user_job {job['id']}")

    if synced:
        logger.info(f"Notion: synced {synced} jobs for user {user_id[:8]}")
    return synced


async def sync_companies_to_notion(user_id: str) -> int:
    """Push companies without a notion_page_id to Notion. Returns count synced."""
    settings = get_settings()
    if not settings.notion_token or not settings.notion_companies_db_id:
        return 0

    sb = get_supabase()

    companies = (
        sb.table("companies")
        .select("id, name, website, location, sector, source, relevance_score, spontaneous_status")
        .eq("user_id", user_id)
        .is_("notion_page_id", "null")
        .order("relevance_score", desc=True)
        .limit(50)
        .execute()
    )

    if not companies.data:
        return 0

    synced = 0
    for company in companies.data:
        result = _notion_request("POST", "pages", {
            "parent": {"database_id": settings.notion_companies_db_id},
            "properties": _company_to_notion_properties(company),
        })
        if result and result.get("id"):
            sb.table("companies").update({"notion_page_id": result["id"]}).eq("id", company["id"]).execute()
            synced += 1
        else:
            logger.error(f"Notion sync failed for company {company['id']}")

    if synced:
        logger.info(f"Notion: synced {synced} companies for user {user_id[:8]}")
    return synced


def update_notion_job_status(notion_page_id: str, status: str):
    """Update a job's status in Notion when it changes locally."""
    settings = get_settings()
    if not notion_page_id or not settings.notion_token:
        return

    _notion_request("PATCH", f"pages/{notion_page_id}", {
        "properties": {
            "Statut": {"select": {"name": _map_status(status)}},
        },
    })


async def sync_all_users():
    """Sync jobs and companies to Notion for all users with notion_enabled=true."""
    settings = get_settings()
    if not settings.notion_token:
        return

    sb = get_supabase()
    profiles = (
        sb.table("profiles")
        .select("id")
        .eq("onboarding_completed", True)
        .eq("notion_enabled", True)
        .execute()
    )

    if not profiles.data:
        return

    for user in profiles.data:
        user_id = user["id"]
        try:
            await sync_jobs_to_notion(user_id)
            await sync_companies_to_notion(user_id)
        except Exception as e:
            logger.error(f"Notion sync failed for user {user_id[:8]}: {e}")


# ---------------------------------------------------------------------------
# Property builders
# ---------------------------------------------------------------------------

def _job_to_notion_properties(job: dict) -> dict:
    raw = job.get("raw_jobs", {})
    match_kw = job.get("match_keywords") or []
    if isinstance(match_kw, str):
        match_kw = json.loads(match_kw)
    score = job.get("match_score") or 0

    props = {
        "Titre": {"title": [{"text": {"content": raw.get("title", "")[:100]}}]},
        "Entreprise": {"rich_text": [{"text": {"content": raw.get("company", "")[:100]}}]},
        "Score": {"number": score},
        "Statut": {"select": {"name": _map_status(job.get("status", "new"))}},
        "Source": {"select": {"name": raw.get("source", "unknown")}},
    }

    if raw.get("location"):
        props["Localisation"] = {"rich_text": [{"text": {"content": raw["location"][:100]}}]}

    if raw.get("source_url"):
        props["Lien offre"] = {"url": raw["source_url"]}

    if raw.get("remote_type") and raw["remote_type"] != "unknown":
        props["Remote"] = {"select": {"name": raw["remote_type"]}}

    if match_kw:
        props["Keywords"] = {"rich_text": [{"text": {"content": ", ".join(match_kw[:15])}}]}

    if job.get("match_reasoning"):
        props["Reasoning"] = {"rich_text": [{"text": {"content": job["match_reasoning"][:200]}}]}

    if job.get("match_priority"):
        props["Priorité"] = {"select": {"name": job["match_priority"]}}

    salary = _format_salary(raw)
    if salary:
        props["Salaire"] = {"rich_text": [{"text": {"content": salary}}]}

    if raw.get("scraped_at"):
        props["Date scrape"] = {"date": {"start": raw["scraped_at"][:10]}}

    return props


def _company_to_notion_properties(company: dict) -> dict:
    props = {
        "Nom": {"title": [{"text": {"content": company["name"][:100]}}]},
        "Statut": {"select": {"name": _map_status(company.get("spontaneous_status", "pending"))}},
        "Source": {"select": {"name": company.get("source", "manual")}},
    }

    if company.get("website"):
        props["Site"] = {"url": company["website"]}

    if company.get("location"):
        props["Localisation"] = {"rich_text": [{"text": {"content": company["location"][:100]}}]}

    if company.get("sector"):
        props["Secteur"] = {"rich_text": [{"text": {"content": company["sector"][:100]}}]}

    if company.get("relevance_score"):
        props["Score"] = {"number": company["relevance_score"]}

    return props


def _map_status(status: str) -> str:
    return {
        "new": "Nouveau",
        "notified": "Notifié",
        "interested": "Intéressé",
        "rejected": "Rejeté",
        "applied": "Postulé",
        "pending": "En attente",
        "prepared": "Préparé",
        "sent": "Envoyé",
    }.get(status, status)


def _format_salary(job: dict) -> str:
    s_min = job.get("salary_min")
    s_max = job.get("salary_max")
    currency = job.get("salary_currency", "EUR")
    if s_min and s_max:
        return f"{s_min // 1000}K-{s_max // 1000}K {currency}" if s_min >= 1000 else f"{s_min}-{s_max} {currency}"
    if s_min:
        return f"{s_min // 1000}K+ {currency}" if s_min >= 1000 else f"{s_min}+ {currency}"
    return ""
