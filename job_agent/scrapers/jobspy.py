import asyncio
import logging
from functools import partial

import pandas as pd

from job_agent.scrapers.base import BaseScraper, RawJob

logger = logging.getLogger(__name__)


class JobSpyScraper(BaseScraper):
    """Aggregates LinkedIn, Indeed, and Glassdoor via python-jobspy."""

    @property
    def source_name(self) -> str:
        return "jobspy"

    async def scrape(self, queries: list[str], locations: list[str], config: dict) -> list[RawJob]:
        sites = config.get("sites", ["indeed", "linkedin", "glassdoor"])
        results_wanted = config.get("results_per_query", 25)
        country = config.get("country", "France")
        jobs = []
        seen_urls = set()

        for query in queries:
            for location in locations:
                try:
                    # jobspy is synchronous — run in executor
                    loop = asyncio.get_event_loop()
                    df = await loop.run_in_executor(
                        None,
                        partial(
                            _scrape_sync,
                            sites=sites,
                            query=query,
                            location=location,
                            results_wanted=results_wanted,
                            country=country,
                        ),
                    )
                    if df is None or df.empty:
                        continue

                    for _, row in df.iterrows():
                        url = str(row.get("job_url", ""))
                        if not url or url in seen_urls:
                            continue
                        seen_urls.add(url)

                        jobs.append(RawJob(
                            title=str(row.get("title", "")),
                            company=str(row.get("company_name", "Unknown")),
                            location=str(row.get("location", location)),
                            remote_type=_parse_remote(row),
                            salary_min=_safe_int(row.get("min_amount")),
                            salary_max=_safe_int(row.get("max_amount")),
                            salary_currency=str(row.get("currency", "EUR")),
                            description=str(row.get("description", "")),
                            tags=[],
                            source=f"jobspy_{row.get('site', 'unknown')}",
                            source_url=url,
                            apply_url=url,
                            company_url=str(row.get("company_url", "")) or None,
                            posted_at=None,
                        ))

                except Exception as e:
                    logger.error(f"JobSpy error for '{query}' in '{location}': {e}")
                    continue

        logger.info(f"JobSpy: {len(jobs)} jobs found across {sites}")
        return jobs


def _scrape_sync(sites, query, location, results_wanted, country):
    """Synchronous wrapper for jobspy scrape_jobs."""
    try:
        from jobspy import scrape_jobs
        df = scrape_jobs(
            site_name=sites,
            search_term=query,
            location=location,
            results_wanted=results_wanted,
            country_indeed=country,
            hours_old=168,  # Last 7 days
        )
        return df
    except Exception as e:
        logger.error(f"JobSpy scrape_jobs failed: {e}")
        return None


def _parse_remote(row) -> str:
    is_remote = row.get("is_remote")
    if is_remote is True:
        return "full"
    desc = str(row.get("description", "")).lower()
    if "hybrid" in desc or "hybride" in desc or "télétravail partiel" in desc:
        return "partial"
    if "remote" in desc or "télétravail" in desc:
        return "partial"
    return "office"


def _safe_int(val) -> int | None:
    if val is None or pd.isna(val):
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None
