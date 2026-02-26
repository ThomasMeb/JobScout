"""Worker tasks — scrape global + score per-user for multi-tenant SaaS.

Architecture:
- scrape_global(): union all active user queries, scrape into raw_jobs (shared pool)
- score_per_user(): for each active user, score unscored jobs with their cv_text
"""
import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timezone

import sentry_sdk

from job_agent.scrapers.adzuna import AdzunaScraper
from job_agent.scrapers.base import RawJob
from job_agent.scrapers.francetravail import FranceTravailScraper
from job_agent.scrapers.remoteok import RemoteOKScraper
from job_agent.scrapers.wttj import WTTJScraper

from worker.config import SCRAPER_CONFIGS, get_settings
from worker.db import get_supabase, get_user_monthly_cost
from worker.scoring import (
    build_system_prompt,
    call_llm,
    estimate_cost,
    format_salary,
    parse_scoring_response,
)

logger = logging.getLogger(__name__)

ALL_SCRAPERS = [
    ("wttj", WTTJScraper()),
    ("remoteok", RemoteOKScraper()),
    ("adzuna", AdzunaScraper()),
    ("francetravail", FranceTravailScraper()),
    # JobSpy disabled — runs in executor (uninterruptible by asyncio timeout),
    # 18 sequential requests with sleeps, and returns 0 jobs consistently.
    # ("jobspy", JobSpyScraper()),
    # Playwright scrapers disabled — Chromium exceeds Render Starter 512MB RAM limit.
    # ("hellowork", HelloWorkScraper()),
    # ("apec", APECScraper()),
    # ("freework", FreeWorkScraper()),
    # ("welovedevs", WeLoveDevsScraper()),
]


def _job_hash(title: str, company: str, source_url: str) -> str:
    """SHA256 hash for deduplication — same logic as job_agent/storage.py."""
    raw = f"{title.lower().strip()}|{company.lower().strip()}|{source_url.strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def scrape_global():
    """Scrape jobs from all sources into the shared raw_jobs pool.

    1. Fetch all active user profiles to collect queries/locations
    2. Run enabled scrapers with the union of all queries
    3. Upsert results into raw_jobs (deduplicate via hash)
    4. Log scrape_runs for monitoring
    """
    sb = get_supabase()

    # 1. Get all active users' search parameters
    profiles = (
        sb.table("profiles")
        .select("search_queries, search_locations")
        .eq("onboarding_completed", True)
        .execute()
    )

    if not profiles.data:
        logger.info("No active users found, skipping scrape")
        return

    # Union all queries and locations (deduplicated)
    all_queries = set()
    all_locations = set()
    for p in profiles.data:
        for q in (p.get("search_queries") or []):
            all_queries.add(q)
        for loc in (p.get("search_locations") or []):
            all_locations.add(loc)

    if not all_queries:
        logger.info("No search queries configured by any user, skipping scrape")
        return

    queries = list(all_queries)
    locations = list(all_locations) or ["France"]

    logger.info(f"Scraping with {len(queries)} queries, {len(locations)} locations")

    # 2. Run each enabled scraper
    total_found = 0
    total_new = 0

    for source_key, scraper in ALL_SCRAPERS:
        source_cfg = SCRAPER_CONFIGS.get(source_key, {})
        if not source_cfg.get("enabled", True):
            continue

        logger.info(f"Scraping {source_key}...")
        run_id = _log_scrape_start(sb, source_key, queries)
        t0 = time.monotonic()

        sentry_sdk.add_breadcrumb(
            category="scraper", message=f"Starting {source_key}", level="info",
        )

        raw_jobs = None
        max_retries = 1
        scraper_timeout = 120  # 2 minutes max per scraper attempt
        for attempt in range(max_retries + 1):
            try:
                raw_jobs = await asyncio.wait_for(
                    scraper.scrape(queries, locations, source_cfg),
                    timeout=scraper_timeout,
                )
                break
            except asyncio.TimeoutError:
                duration = time.monotonic() - t0
                logger.error(f"Scraper {source_key} timed out after {scraper_timeout}s (attempt {attempt + 1})")
                if attempt == max_retries:
                    sentry_sdk.add_breadcrumb(
                        category="scraper", message=f"{source_key} TIMEOUT in {duration:.1f}s", level="error",
                    )
                    _log_scrape_finish(sb, run_id, 0, 0, "timeout", f"Timed out after {scraper_timeout}s", duration)
            except Exception as e:
                if attempt < max_retries:
                    wait = 5 * (attempt + 1)
                    logger.warning(f"Scraper {source_key} attempt {attempt + 1} failed: {e}, retrying in {wait}s")
                    await asyncio.sleep(wait)
                else:
                    duration = time.monotonic() - t0
                    logger.error(f"Scraper {source_key} failed after {max_retries + 1} attempts: {e}")
                    sentry_sdk.add_breadcrumb(
                        category="scraper", message=f"{source_key} FAILED in {duration:.1f}s: {e}", level="error",
                    )
                    _log_scrape_finish(sb, run_id, 0, 0, "error", str(e), duration)

        if raw_jobs is None:
            continue

        found = len(raw_jobs)
        new = 0
        for rj in raw_jobs:
            inserted = _upsert_raw_job(sb, rj)
            if inserted:
                new += 1

        duration = time.monotonic() - t0
        _log_scrape_finish(sb, run_id, found, new, "success", duration=duration)
        total_found += found
        total_new += new
        logger.info(f"  {source_key}: {found} found, {new} new ({duration:.1f}s)")

    logger.info(f"Scrape complete: {total_found} found, {total_new} new")


def _upsert_raw_job(sb, rj: RawJob) -> bool:
    """Insert a raw job if not already present. Returns True if new."""
    h = _job_hash(rj.title, rj.company, rj.source_url)

    # Check if hash already exists
    existing = sb.table("raw_jobs").select("id").eq("hash", h).execute()
    if existing.data:
        return False

    tags = rj.tags if isinstance(rj.tags, list) else []

    sb.table("raw_jobs").insert({
        "hash": h,
        "title": rj.title,
        "company": rj.company,
        "location": rj.location,
        "remote_type": rj.remote_type,
        "salary_min": rj.salary_min,
        "salary_max": rj.salary_max,
        "salary_currency": rj.salary_currency,
        "description": rj.description,
        "tags": json.dumps(tags),
        "source": rj.source,
        "source_url": rj.source_url,
        "apply_url": rj.apply_url,
        "company_url": rj.company_url,
        "posted_at": rj.posted_at.isoformat() if rj.posted_at else None,
    }).execute()

    return True


def _log_scrape_start(sb, source: str, queries: list[str]) -> int | None:
    """Log the start of a scrape run."""
    result = sb.table("scrape_runs").insert({
        "source": source,
        "queries_used": json.dumps(queries),
        "status": "running",
    }).execute()
    if result.data and len(result.data) > 0:
        return result.data[0]["id"]
    return None


def _log_scrape_finish(
    sb, run_id: int | None, found: int, new: int, status: str,
    error: str | None = None, duration: float | None = None,
):
    """Update scrape run with results and duration."""
    if run_id is None:
        return
    row = {
        "jobs_found": found,
        "jobs_new": new,
        "status": status,
        "error_message": error,
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    if duration is not None:
        row["duration_seconds"] = round(duration, 2)
    sb.table("scrape_runs").update(row).eq("id", run_id).execute()


async def score_per_user():
    """Score unscored jobs for each active user.

    1. For each user with onboarding_completed=true:
       a. Check monthly LLM budget
       b. Get unscored jobs via RPC
       c. Score each job using their cv_text as profile
       d. Insert into user_jobs + log llm_usage
    """
    sb = get_supabase()
    settings = get_settings()

    # Get all active users
    profiles = (
        sb.table("profiles")
        .select("id, cv_text, profile_summary, search_queries, search_locations, "
                "bonus_keywords, penalty_keywords, remote_accepted, min_salary, "
                "monthly_budget_usd, plan")
        .eq("onboarding_completed", True)
        .execute()
    )

    if not profiles.data:
        logger.info("No active users to score")
        return

    for user in profiles.data:
        user_id = user["id"]
        cv_text = user.get("cv_text") or user.get("profile_summary") or ""

        if not cv_text:
            logger.info(f"User {user_id[:8]}... has no CV, skipping scoring")
            continue

        # Check monthly budget
        budget = float(user.get("monthly_budget_usd") or 5.0)
        monthly_cost = get_user_monthly_cost(sb, user_id)
        if monthly_cost >= budget:
            logger.info(f"User {user_id[:8]}... budget exhausted: ${monthly_cost:.4f} >= ${budget:.2f}")
            continue

        # Get unscored jobs via RPC
        queries = user.get("search_queries") or []
        locations = user.get("search_locations") or []

        try:
            unscored = sb.rpc("get_unscored_jobs_for_user", {
                "p_user_id": user_id,
                "p_queries": queries,
                "p_locations": locations,
                "p_days_back": settings.job_lookback_days,
                "p_limit": settings.max_jobs_per_user_per_cycle,
            }).execute()
        except Exception as e:
            logger.error(f"RPC get_unscored_jobs failed for {user_id[:8]}...: {e}")
            continue

        jobs = unscored.data or []
        if not jobs:
            logger.info(f"User {user_id[:8]}...: no unscored jobs")
            continue

        # Enforce plan limits: Free = 10 jobs/cycle, Pro/Trial = unlimited
        user_plan = user.get("plan") or "free"
        if user_plan == "free":
            free_limit = 10
            jobs = jobs[:free_limit]

        logger.info(f"User {user_id[:8]}... [{user_plan}]: scoring {len(jobs)} jobs")

        # Build system prompt with user's full profile and preferences
        system_prompt = build_system_prompt(user)

        scored_count = 0
        for job in jobs:
            # Check budget before each scoring
            if monthly_cost >= budget:
                logger.info(f"User {user_id[:8]}... budget hit mid-cycle, stopping")
                break

            try:
                result = await _score_single_job(
                    sb, user_id, job, system_prompt, settings, budget - monthly_cost
                )
                if result:
                    monthly_cost += result
                    scored_count += 1
            except Exception as e:
                logger.error(f"Failed to score job {job['id']} for {user_id[:8]}...: {e}")
                continue

        logger.info(f"User {user_id[:8]}...: scored {scored_count}/{len(jobs)} jobs")


async def _score_single_job(
    sb, user_id: str, job: dict, system_prompt: str,
    settings, remaining_budget: float,
) -> float | None:
    """Score a single job for a user. Returns cost or None on failure."""
    description = job.get("description") or ""
    if len(description) > 3000:
        description = description[:3000] + "..."

    user_prompt = f"""OFFRE D'EMPLOI :
Titre : {job.get('title', '')}
Entreprise : {job.get('company', '')}
Localisation : {job.get('location') or 'Non précisé'}
Tags : {job.get('tags') or 'Aucun'}
Salaire : {format_salary(job.get('salary_min'), job.get('salary_max'), job.get('salary_currency', 'EUR'))}

Description :
{description}"""

    response_text, in_tokens, out_tokens = await call_llm(
        system_prompt,
        user_prompt,
        max_tokens=settings.scoring_max_tokens,
        temperature=settings.scoring_temperature,
    )

    result = parse_scoring_response(response_text)
    cost = estimate_cost(settings.deepseek_model, in_tokens, out_tokens)

    # Insert into user_jobs + llm_usage atomically
    uj_result = sb.table("user_jobs").insert({
        "user_id": user_id,
        "raw_job_id": job["id"],
        "match_score": result["score"],
        "match_reasoning": result["reasoning"],
        "match_keywords": json.dumps(result["match_keywords"]),
        "missing_keywords": json.dumps(result["missing_keywords"]),
        "match_priority": result["priority"],
        "status": "new",
    }).execute()

    user_job_id = uj_result.data[0]["id"] if uj_result.data and len(uj_result.data) > 0 else None

    # Log LLM usage — rollback user_jobs entry on failure
    try:
        sb.table("llm_usage").insert({
            "user_id": user_id,
            "operation": "scoring",
            "user_job_id": user_job_id,
            "model": settings.deepseek_model,
            "tokens_in": in_tokens,
            "tokens_out": out_tokens,
            "cost_usd": cost,
        }).execute()
    except Exception as e:
        logger.error(f"Failed to log LLM usage for job {job['id']}, rolling back user_job: {e}")
        if user_job_id:
            sb.table("user_jobs").delete().eq("id", user_job_id).execute()
        raise

    return cost


