import asyncio
import logging

import httpx

from job_agent.scrapers.base import BaseScraper, RawJob

logger = logging.getLogger(__name__)

# WTTJ uses Algolia for search — these are the public credentials
# visible in their frontend JavaScript
ALGOLIA_APP_ID = "CSEKHVMS53"
ALGOLIA_URL = f"https://{ALGOLIA_APP_ID}-dsn.algolia.net/1/indexes/*/queries"

# Fallback: WTTJ API
WTTJ_API_URL = "https://www.welcometothejungle.com/api/v1/search"


class WTTJScraper(BaseScraper):
    @property
    def source_name(self) -> str:
        return "wttj"

    async def scrape(self, queries: list[str], locations: list[str], config: dict) -> list[RawJob]:
        max_results = config.get("max_results_per_query", 50)
        delay = config.get("delay_between_requests", 5)
        jobs = []
        seen_slugs = set()

        # First, try to get the Algolia API key from WTTJ frontend
        api_key = await self._get_algolia_key()

        if api_key:
            jobs = await self._scrape_algolia(queries, locations, api_key, max_results, delay, seen_slugs)
        else:
            logger.warning("Could not get Algolia key, falling back to WTTJ search page")
            jobs = await self._scrape_fallback(queries, locations, max_results, delay, seen_slugs)

        logger.info(f"WTTJ: {len(jobs)} jobs found")
        return jobs

    async def _get_algolia_key(self) -> str | None:
        """Extract the Algolia search-only API key from WTTJ frontend."""
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            try:
                resp = await client.get(
                    "https://www.welcometothejungle.com/fr/jobs",
                    headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
                )
                text = resp.text
                # WTTJ exposes key as ALGOLIA_API_KEY_CLIENT in page config
                import re
                match = re.search(r'ALGOLIA_API_KEY_CLIENT["\s:]+["\']([a-f0-9]{32})["\']', text)
                if match:
                    return match.group(1)
                # Fallback: search for any 32-char hex near "algolia"
                for m in re.finditer(r'"([a-f0-9]{32})"', text):
                    start = max(0, m.start() - 100)
                    context = text[start:m.start()].lower()
                    if "algolia" in context and "key" in context:
                        return m.group(1)
            except Exception as e:
                logger.error(f"Failed to extract Algolia key: {e}")
        return None

    async def _scrape_algolia(
        self, queries, locations, api_key, max_results, delay, seen_slugs
    ) -> list[RawJob]:
        jobs = []
        async with httpx.AsyncClient(timeout=30) as client:
            for query in queries:
                for location in locations:
                    try:
                        resp = await client.post(
                            ALGOLIA_URL,
                            headers={
                                "x-algolia-application-id": ALGOLIA_APP_ID,
                                "x-algolia-api-key": api_key,
                                "Content-Type": "application/json",
                                "Referer": "https://www.welcometothejungle.com/",
                                "Origin": "https://www.welcometothejungle.com",
                            },
                            json={
                                "requests": [
                                    {
                                        "indexName": "wttj_jobs_production_fr",
                                        "params": (
                                            f"query={query}"
                                            f"&aroundLatLngViaIP=false"
                                            f"&hitsPerPage={max_results}"
                                            f"&facetFilters=[]"
                                        ),
                                    }
                                ]
                            },
                        )
                        resp.raise_for_status()
                        data = resp.json()
                    except Exception as e:
                        logger.error(f"WTTJ Algolia error for '{query}': {e}")
                        continue

                    results = data.get("results", [{}])
                    hits = results[0].get("hits", []) if results else []

                    for hit in hits:
                        slug = hit.get("slug", "")
                        if slug in seen_slugs:
                            continue
                        seen_slugs.add(slug)

                        company_name = hit.get("organization", {}).get("name", "Unknown")
                        offices = hit.get("offices", [])
                        if offices and isinstance(offices, list):
                            office = offices[0]
                            city = office.get("city", "")
                            country = office.get("country", "")
                            location_str = f"{city}, {country}" if city else country
                        else:
                            location_str = ""

                        jobs.append(RawJob(
                            title=hit.get("name", ""),
                            company=company_name,
                            location=location_str,
                            remote_type=_parse_remote(hit),
                            salary_min=_parse_salary(hit.get("salary_minimum") or hit.get("salary_yearly_minimum")),
                            salary_max=_parse_salary(hit.get("salary_maximum")),
                            salary_currency=hit.get("salary_currency", "EUR"),
                            description=hit.get("summary", "") or hit.get("description", "") or hit.get("profile", ""),
                            tags=_extract_tags(hit),
                            source="wttj",
                            source_url=f"https://www.welcometothejungle.com/fr/companies/{hit.get('organization', {}).get('slug', '')}/jobs/{slug}",
                            apply_url=hit.get("apply_url"),
                            company_url=f"https://www.welcometothejungle.com/fr/companies/{hit.get('organization', {}).get('slug', '')}",
                            posted_at=None,
                        ))

                    await asyncio.sleep(delay)

        return jobs

    async def _scrape_fallback(self, queries, locations, max_results, delay, seen_slugs) -> list[RawJob]:
        """Fallback: use WTTJ's public search page with httpx + parsing."""
        jobs = []
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            for query in queries:
                try:
                    await client.get(
                        "https://www.welcometothejungle.com/fr/jobs",
                        params={"query": query, "refinementList%5Bremote%5D%5B%5D": "no"},
                        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
                    )
                    # Parse from page JSON data would go here
                    # For now, log that fallback was used
                    logger.warning(f"WTTJ fallback scraping not fully implemented for '{query}'")
                except Exception as e:
                    logger.error(f"WTTJ fallback error: {e}")
                await asyncio.sleep(delay)
        return jobs


def _parse_remote(hit: dict) -> str:
    remote = hit.get("remote", "")
    if remote in ("fulltime", "full"):
        return "full"
    if remote in ("partial", "punctual", "hybrid"):
        return "partial"
    if remote == "no":
        return "office"
    # Check benefits for remote info
    benefits = hit.get("benefits", [])
    if any("télétravail" in b.lower() for b in benefits if isinstance(b, str)):
        return "partial"
    return "office"


def _parse_salary(val) -> int | None:
    if val is None:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def _extract_tags(hit: dict) -> list[str]:
    tags = []
    # New profession structure
    new_prof = hit.get("new_profession", {})
    if isinstance(new_prof, dict):
        for key in ("pivot_name", "sub_category_name", "category_name"):
            val = new_prof.get(key, "")
            if val:
                tags.append(val)
    # Sectors
    for sector in hit.get("sectors", []):
        if isinstance(sector, dict):
            name = sector.get("name", "")
            if name:
                tags.append(name)
    return [t for t in tags if t]
