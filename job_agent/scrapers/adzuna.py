import logging
import os

import httpx

from job_agent.scrapers.base import BaseScraper, RawJob

ADZUNA_APP_ID = os.environ.get("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.environ.get("ADZUNA_APP_KEY", "")

logger = logging.getLogger(__name__)

BASE_URL = "https://api.adzuna.com/v1/api/jobs"


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
        jobs = []
        seen_urls = set()

        async with httpx.AsyncClient(timeout=30) as client:
            for query in queries:
                for location in locations:
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
                        resp.raise_for_status()
                        data = resp.json()
                    except Exception as e:
                        logger.error(f"Adzuna error for '{query}' in '{location}': {e}")
                        continue

                    for item in data.get("results", []):
                        url = item.get("redirect_url", "")
                        if url in seen_urls:
                            continue
                        seen_urls.add(url)

                        salary_min = item.get("salary_min")
                        salary_max = item.get("salary_max")

                        loc = item.get("location", {})
                        display_name = loc.get("display_name", "")

                        jobs.append(RawJob(
                            title=item.get("title", ""),
                            company=item.get("company", {}).get("display_name", "Unknown"),
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

        logger.info(f"Adzuna: {len(jobs)} jobs found")
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
