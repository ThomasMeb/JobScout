import json
import logging
import os
import sqlite3

logger = logging.getLogger(__name__)


def _get_notion_client():
    token = os.environ.get("NOTION_TOKEN", "")
    if not token:
        return None
    try:
        from notion_client import Client
        return Client(auth=token)
    except ImportError:
        logger.warning("notion-sdk not installed, skipping Notion sync")
        return None


def get_database_id() -> str:
    return os.environ.get("NOTION_DATABASE_ID", "")


def sync_jobs_to_notion(conn: sqlite3.Connection, min_score: float) -> int:
    """Push high-scoring jobs without a Notion page ID to Notion. Returns count synced."""
    from job_agent.storage import get_jobs_without_notion, update_job_notion_id

    notion = _get_notion_client()
    db_id = get_database_id()
    if not notion or not db_id:
        return 0

    jobs = get_jobs_without_notion(conn, min_score)
    if not jobs:
        return 0

    synced = 0
    for job in jobs:
        try:
            page = notion.pages.create(
                parent={"database_id": db_id},
                properties=_job_to_notion_properties(job),
            )
            update_job_notion_id(conn, job["id"], page["id"])
            synced += 1
        except Exception as e:
            logger.error(f"Notion sync failed for job {job['id']}: {e}")
            continue

    if synced:
        logger.info(f"Notion: synced {synced} jobs")
    return synced


def sync_companies_to_notion(conn: sqlite3.Connection) -> int:
    """Push companies without a Notion page ID to Notion. Returns count synced."""
    from job_agent.storage import update_company_notion_id

    notion = _get_notion_client()
    db_id = os.environ.get("NOTION_COMPANIES_DB_ID", "")
    if not notion or not db_id:
        return 0

    rows = conn.execute(
        "SELECT * FROM companies WHERE notion_page_id IS NULL ORDER BY relevance_score DESC"
    ).fetchall()
    companies = [dict(r) for r in rows]

    synced = 0
    for company in companies:
        try:
            page = notion.pages.create(
                parent={"database_id": db_id},
                properties=_company_to_notion_properties(company),
            )
            update_company_notion_id(conn, company["id"], page["id"])
            synced += 1
        except Exception as e:
            logger.error(f"Notion sync failed for company {company['id']}: {e}")
            continue

    if synced:
        logger.info(f"Notion: synced {synced} companies")
    return synced


def update_notion_job_status(job: dict):
    """Update a job's status in Notion when it changes locally."""
    notion = _get_notion_client()
    if not notion or not job.get("notion_page_id"):
        return

    try:
        notion.pages.update(
            page_id=job["notion_page_id"],
            properties={
                "Statut": {"select": {"name": _map_status(job["status"])}},
            },
        )
    except Exception as e:
        logger.error(f"Notion status update failed: {e}")


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
        "Statut": {"select": {"name": company.get("spontaneous_status", "pending")}},
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
