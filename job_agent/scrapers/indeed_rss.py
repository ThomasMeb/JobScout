import logging
from urllib.parse import quote_plus

import feedparser
import httpx

from job_agent.scrapers.base import BaseScraper, RawJob

logger = logging.getLogger(__name__)

RSS_TEMPLATES = {
    "fr": "https://fr.indeed.com/rss?q={query}&l={location}&sort=date",
    "us": "https://www.indeed.com/rss?q={query}&l={location}&sort=date",
    "uk": "https://uk.indeed.com/rss?q={query}&l={location}&sort=date",
}


class IndeedRSSScraper(BaseScraper):
    @property
    def source_name(self) -> str:
        return "indeed"

    async def scrape(self, queries: list[str], locations: list[str], config: dict) -> list[RawJob]:
        country = config.get("country", "fr")
        template = RSS_TEMPLATES.get(country, RSS_TEMPLATES["fr"])
        jobs = []
        seen_urls = set()

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            for query in queries:
                for location in locations:
                    url = template.format(
                        query=quote_plus(query),
                        location=quote_plus(location),
                    )
                    try:
                        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                        resp.raise_for_status()
                        feed = feedparser.parse(resp.text)
                    except Exception as e:
                        logger.error(f"Indeed RSS error for '{query}' in '{location}': {e}")
                        continue

                    for entry in feed.entries:
                        link = entry.get("link", "")
                        if link in seen_urls:
                            continue
                        seen_urls.add(link)

                        title = entry.get("title", "")
                        # Indeed RSS format: "Title - Company - Location"
                        company = _extract_company(title, entry)
                        clean_title = _clean_title(title)

                        jobs.append(RawJob(
                            title=clean_title,
                            company=company,
                            location=location,
                            remote_type="unknown",
                            description=entry.get("summary", ""),
                            tags=[],
                            source="indeed",
                            source_url=link,
                            apply_url=link,
                            posted_at=None,
                        ))

        logger.info(f"Indeed RSS: {len(jobs)} jobs found")
        return jobs


def _extract_company(title: str, entry: dict) -> str:
    """Try to extract company from RSS entry or title."""
    # Some Indeed RSS entries have 'source' or 'author'
    if entry.get("source", {}).get("title"):
        return entry["source"]["title"]
    # Fallback: split title by " - "
    parts = title.split(" - ")
    if len(parts) >= 2:
        return parts[-2].strip()
    return "Unknown"


def _clean_title(title: str) -> str:
    """Remove company and location suffix from Indeed RSS title."""
    parts = title.split(" - ")
    if len(parts) >= 2:
        return parts[0].strip()
    return title
