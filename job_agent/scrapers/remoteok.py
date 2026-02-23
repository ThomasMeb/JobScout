import logging

import httpx

from job_agent.scrapers.base import BaseScraper, RawJob, retry_request

logger = logging.getLogger(__name__)

API_URL = "https://remoteok.com/api"


class RemoteOKScraper(BaseScraper):
    @property
    def source_name(self) -> str:
        return "remoteok"

    async def scrape(self, queries: list[str], locations: list[str], config: dict) -> list[RawJob]:
        filter_tags = set(config.get("filter_tags", []))
        jobs = []
        seen_ids = set()

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await retry_request(
                    client, "GET", API_URL,
                    headers={"User-Agent": "job-agent/1.0"},
                )
                data = resp.json()
            except Exception as e:
                logger.error(f"RemoteOK API error: {e}")
                return []

        # First element is metadata, skip it
        for item in data[1:] if len(data) > 1 else []:
            # Deduplication by id or slug
            item_id = item.get("id") or item.get("slug", "")
            if item_id in seen_ids:
                continue
            seen_ids.add(item_id)

            item_tags = [t.lower() for t in item.get("tags", [])]

            # Filter by tags if configured
            if filter_tags and not any(t in filter_tags for t in item_tags):
                continue

            title = item.get("position", "")
            company = item.get("company", "")
            if not title or not company:
                slug = item.get("slug", "")
                logger.debug(f"RemoteOK: skipping job with missing title or company: {slug}")
                continue

            slug = item.get("slug", "")
            jobs.append(RawJob(
                title=title,
                company=company,
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
