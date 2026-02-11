import json
import logging
import os
import sqlite3

import httpx

logger = logging.getLogger(__name__)

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _headers() -> dict:
    token = os.environ.get("NOTION_TOKEN", "")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def get_database_id() -> str:
    return os.environ.get("NOTION_DATABASE_ID", "")


def _notion_request(method: str, path: str, body: dict | None = None) -> dict | None:
    """Make a Notion API request. Returns response dict or None on failure."""
    token = os.environ.get("NOTION_TOKEN", "")
    if not token:
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
    jobs_db = get_database_id()
    companies_db = os.environ.get("NOTION_COMPANIES_DB_ID", "")

    success = True
    if jobs_db:
        result = _notion_request("PATCH", f"databases/{jobs_db}", {
            "properties": {
                "Nom": {"name": "Titre"},
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
            logger.info("Jobs database properties created")
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
            logger.info("Companies database properties created")
        else:
            success = False

    return success


def sync_jobs_to_notion(conn: sqlite3.Connection, min_score: float) -> int:
    """Push high-scoring jobs without a Notion page ID to Notion. Returns count synced."""
    from job_agent.storage import get_jobs_without_notion, update_job_notion_id

    db_id = get_database_id()
    if not db_id or not os.environ.get("NOTION_TOKEN"):
        return 0

    jobs = get_jobs_without_notion(conn, min_score)
    if not jobs:
        return 0

    synced = 0
    for job in jobs:
        result = _notion_request("POST", "pages", {
            "parent": {"database_id": db_id},
            "properties": _job_to_notion_properties(job),
        })
        if result and result.get("id"):
            update_job_notion_id(conn, job["id"], result["id"])
            synced += 1
        else:
            logger.error(f"Notion sync failed for job {job['id']}")

    if synced:
        logger.info(f"Notion: synced {synced} jobs")
    return synced


def sync_companies_to_notion(conn: sqlite3.Connection) -> int:
    """Push companies without a Notion page ID to Notion. Returns count synced."""
    from job_agent.storage import update_company_notion_id

    db_id = os.environ.get("NOTION_COMPANIES_DB_ID", "")
    if not db_id or not os.environ.get("NOTION_TOKEN"):
        return 0

    rows = conn.execute(
        "SELECT * FROM companies WHERE notion_page_id IS NULL ORDER BY relevance_score DESC"
    ).fetchall()
    companies = [dict(r) for r in rows]

    synced = 0
    for company in companies:
        result = _notion_request("POST", "pages", {
            "parent": {"database_id": db_id},
            "properties": _company_to_notion_properties(company),
        })
        if result and result.get("id"):
            update_company_notion_id(conn, company["id"], result["id"])
            synced += 1
        else:
            logger.error(f"Notion sync failed for company {company['id']}")

    if synced:
        logger.info(f"Notion: synced {synced} companies")
    return synced


def update_notion_job_status(job: dict):
    """Update a job's status in Notion when it changes locally."""
    if not job.get("notion_page_id") or not os.environ.get("NOTION_TOKEN"):
        return

    _notion_request("PATCH", f"pages/{job['notion_page_id']}", {
        "properties": {
            "Statut": {"select": {"name": _map_status(job["status"])}},
        },
    })


def _job_to_notion_properties(job: dict) -> dict:
    match_kw = json.loads(job.get("match_keywords") or "[]")
    score = job.get("match_score") or 0

    props = {
        "Titre": {"title": [{"text": {"content": job["title"][:100]}}]},
        "Entreprise": {"rich_text": [{"text": {"content": job.get("company", "")[:100]}}]},
        "Score": {"number": score},
        "Statut": {"select": {"name": _map_status(job.get("status", "new"))}},
        "Source": {"select": {"name": job.get("source", "unknown")}},
    }

    if job.get("location"):
        props["Localisation"] = {"rich_text": [{"text": {"content": job["location"][:100]}}]}

    if job.get("source_url"):
        props["Lien offre"] = {"url": job["source_url"]}

    if job.get("remote_type") and job["remote_type"] != "unknown":
        props["Remote"] = {"select": {"name": job["remote_type"]}}

    if match_kw:
        props["Keywords"] = {"rich_text": [{"text": {"content": ", ".join(match_kw[:15])}}]}

    if job.get("match_reasoning"):
        props["Reasoning"] = {"rich_text": [{"text": {"content": job["match_reasoning"][:200]}}]}

    if job.get("match_priority"):
        props["Priorité"] = {"select": {"name": job["match_priority"]}}

    salary = _format_salary(job)
    if salary:
        props["Salaire"] = {"rich_text": [{"text": {"content": salary}}]}

    if job.get("scraped_at"):
        props["Date scrape"] = {"date": {"start": job["scraped_at"][:10]}}

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
