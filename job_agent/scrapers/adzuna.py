import asyncio
import logging
import os

import httpx

from job_agent.scrapers.base import BaseScraper, RawJob

ADZUNA_APP_ID = os.environ.get("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.environ.get("ADZUNA_APP_KEY", "")

logger = logging.getLogger(__name__)

BASE_URL = "https://api.adzuna.com/v1/api/jobs"


class AdzunaQuotaExhaustedError(Exception):
    """Raised on HTTP 429 — caller should stop calling Adzuna for this cycle."""


class AdzunaScraper(BaseScraper):
    @property
    def source_name(self) -> str:
        return "adzuna"

    async def scrape(self, queries: list[str], locations: list[str], config: dict) -> list[RawJob]:
        if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
            logger.warning("Adzuna API keys not configured, skipping")
            return []

        country = config.get("country", "fr")
        distance = config.get("distance_km", 100)
        # Adzuna free tier = 250 calls / month. We cap calls per cycle
        # aggressively to stay below quota even if the worker runs hourly.
        max_calls = max(1, int(config.get("max_calls_per_cycle", 10)))

        jobs = []
        seen_urls = set()
        calls_made = 0

        async with httpx.AsyncClient(timeout=30) as client:
            first_request = True
            for query in queries:
                for location in locations:
                    if calls_made >= max_calls:
                        logger.info(
                            f"Adzuna: hit per-cycle cap ({max_calls} calls), "
                            f"stopping early to preserve monthly quota"
                        )
                        break
                    if not first_request:
                        await asyncio.sleep(2)
                    first_request = False
                    calls_made += 1

                    try:
                        resp = await client.get(
                            f"{BASE_URL}/{country}/search/1",
                            params={
                                "app_id": ADZUNA_APP_ID,
                                "app_key": ADZUNA_APP_KEY,
                                "results_per_page": 50,
                                "what": query,
                                "where": location,
                                "distance": distance,
                                "sort_by": "date",
                                "content-type": "application/json",
                            },
                        )
                        # Hard-stop on 429: every retry burns more quota and the
                        # API will keep refusing until the monthly window resets.
                        if resp.status_code == 429:
                            logger.warning(
                                f"Adzuna 429 (quota exhausted) after {calls_made} calls — "
                                f"aborting cycle; returning {len(jobs)} jobs scraped so far"
                            )
                            raise AdzunaQuotaExhaustedError(
                                f"Adzuna monthly quota hit after {calls_made} calls"
                            )
                        resp.raise_for_status()
                        data = resp.json()
                    except AdzunaQuotaExhaustedError:
                        raise
                    except Exception as e:
                        logger.error(f"Adzuna error for '{query}' in '{location}': {e}")
                        continue

                    for item in data.get("results", []):
                        url = item.get("redirect_url", "")
                        if url in seen_urls:
                            continue
                        seen_urls.add(url)

                        title = item.get("title", "")
                        company = item.get("company", {}).get("display_name", "")
                        if not title or not company:
                            logger.debug(f"Adzuna: skipping job with missing title or company: {url}")
                            continue

                        salary_min = item.get("salary_min")
                        salary_max = item.get("salary_max")

                        loc = item.get("location", {})
                        display_name = loc.get("display_name", "")

                        jobs.append(RawJob(
                            title=title,
                            company=company,
                            location=display_name,
                            remote_type=_detect_remote(item),
                            salary_min=int(salary_min) if salary_min else None,
                            salary_max=int(salary_max) if salary_max else None,
                            salary_currency="EUR" if country == "fr" else "GBP",
                            description=item.get("description", ""),
                            tags=_extract_tags(item),
                            source="adzuna",
                            source_url=url,
                            apply_url=url,
                            company_url=None,
                            posted_at=None,
                        ))
                # Inner location loop done; honor the cap break.
                if calls_made >= max_calls:
                    break

        logger.info(f"Adzuna: {len(jobs)} jobs found ({calls_made} API calls)")
        return jobs


def _detect_remote(item: dict) -> str:
    title = item.get("title", "").lower()
    desc = item.get("description", "").lower()
    text = f"{title} {desc}"
    if "full remote" in text or "fully remote" in text or "100% remote" in text:
        return "full"
    if "remote" in text or "télétravail" in text or "hybride" in text:
        return "partial"
    return "office"


def _extract_tags(item: dict) -> list[str]:
    tags = []
    category = item.get("category", {}).get("tag", "")
    if category:
        tags.append(category)
    return tags
