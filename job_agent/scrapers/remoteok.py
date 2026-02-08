import logging

import httpx

from job_agent.scrapers.base import BaseScraper, RawJob

logger = logging.getLogger(__name__)

API_URL = "https://remoteok.com/api"


class RemoteOKScraper(BaseScraper):
    @property
    def source_name(self) -> str:
        return "remoteok"

    async def scrape(self, queries: list[str], locations: list[str], config: dict) -> list[RawJob]:
        filter_tags = set(config.get("filter_tags", []))
        jobs = []

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(API_URL, headers={"User-Agent": "job-agent/1.0"})
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.error(f"RemoteOK API error: {e}")
                return []

        # First element is metadata, skip it
        for item in data[1:] if len(data) > 1 else []:
            item_tags = [t.lower() for t in item.get("tags", [])]

            # Filter by tags if configured
            if filter_tags and not any(t in filter_tags for t in item_tags):
                continue

            slug = item.get("slug", "")
            jobs.append(RawJob(
                title=item.get("position", ""),
                company=item.get("company", ""),
                location=item.get("location", "Remote"),
                remote_type="full",
                salary_min=_parse_int(item.get("salary_min")),
                salary_max=_parse_int(item.get("salary_max")),
                salary_currency="USD",
                description=item.get("description", ""),
                tags=item.get("tags", []),
                source="remoteok",
                source_url=f"https://remoteok.com/remote-jobs/{slug}" if slug else API_URL,
                apply_url=item.get("apply_url") or item.get("url"),
                company_url=item.get("company_logo"),
                posted_at=None,
            ))

        logger.info(f"RemoteOK: {len(jobs)} jobs after filtering")
        return jobs


def _parse_int(val) -> int | None:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None
