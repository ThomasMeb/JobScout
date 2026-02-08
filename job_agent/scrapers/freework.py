import asyncio
import json
import logging

import httpx
from bs4 import BeautifulSoup

from job_agent.scrapers.base import BaseScraper, RawJob

logger = logging.getLogger(__name__)

BASE_URL = "https://www.free-work.com"


class FreeWorkScraper(BaseScraper):
    @property
    def source_name(self) -> str:
        return "freework"

    async def scrape(self, queries: list[str], locations: list[str], config: dict) -> list[RawJob]:
        max_pages = config.get("max_pages", 2)
        delay = config.get("delay_between_requests", 3)
        contract_type = config.get("contract_type", "")  # "freelance", "cdi", etc.
        jobs = []
        seen_urls = set()

        async with httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/json",
                "Accept-Language": "fr-FR,fr;q=0.9",
            },
        ) as client:
            for query in queries:
                for page in range(1, max_pages + 1):
                    params = {"query": query, "page": page}
                    if contract_type:
                        params["contractType"] = contract_type

                    try:
                        # Try the internal API first (Free-Work is a SPA)
                        resp = await client.get(
                            f"{BASE_URL}/fr/tech-it/jobs",
                            params=params,
                        )
                        resp.raise_for_status()
                    except Exception as e:
                        logger.error(f"Free-Work error for '{query}' p{page}: {e}")
                        break

                    new_jobs = self._parse_page(resp.text, seen_urls)
                    if not new_jobs:
                        break
                    jobs.extend(new_jobs)
                    await asyncio.sleep(delay)

        logger.info(f"Free-Work: {len(jobs)} jobs found")
        return jobs

    def _parse_page(self, html: str, seen_urls: set) -> list[RawJob]:
        jobs = []
        soup = BeautifulSoup(html, "lxml")

        # Try to find JSON data embedded in the page (Next.js __NEXT_DATA__)
        script = soup.find("script", {"id": "__NEXT_DATA__"})
        if script and script.string:
            try:
                data = json.loads(script.string)
                return self._parse_nextjs_data(data, seen_urls)
            except (json.JSONDecodeError, KeyError):
                pass

        # Fallback: parse HTML cards
        cards = soup.select("article, div[class*='job-card'], div[class*='offer-card'], a[class*='job']")
        for card in cards:
            try:
                title_el = card.select_one("h2, h3, [class*='title']")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)

                link_el = card.select_one("a[href*='/jobs/']") or card if card.name == "a" else None
                url = ""
                if link_el:
                    url = link_el.get("href", "")
                    if url and not url.startswith("http"):
                        url = f"{BASE_URL}{url}"
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)

                company_el = card.select_one("[class*='company'], [class*='enterprise']")
                company = company_el.get_text(strip=True) if company_el else "Unknown"

                loc_el = card.select_one("[class*='location'], [class*='city']")
                location = loc_el.get_text(strip=True) if loc_el else ""

                desc_el = card.select_one("[class*='description'], [class*='excerpt'], p")
                description = desc_el.get_text(strip=True) if desc_el else ""

                jobs.append(RawJob(
                    title=title,
                    company=company,
                    location=location,
                    remote_type="partial" if "remote" in (description + location).lower() else "office",
                    description=description,
                    tags=[],
                    source="freework",
                    source_url=url,
                    apply_url=url,
                ))
            except Exception as e:
                logger.debug(f"Free-Work parse error: {e}")
                continue

        return jobs

    def _parse_nextjs_data(self, data: dict, seen_urls: set) -> list[RawJob]:
        """Parse job data from Next.js __NEXT_DATA__ JSON."""
        jobs = []
        try:
            # Navigate the Next.js data structure
            props = data.get("props", {}).get("pageProps", {})
            items = props.get("jobs", props.get("offers", props.get("results", [])))

            if isinstance(items, dict):
                items = items.get("data", items.get("items", []))

            for item in items:
                url = item.get("url", "") or item.get("slug", "")
                if url and not url.startswith("http"):
                    url = f"{BASE_URL}/fr/tech-it/jobs/{url}"
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)

                jobs.append(RawJob(
                    title=item.get("title", ""),
                    company=item.get("company", {}).get("name", "Unknown") if isinstance(item.get("company"), dict) else str(item.get("company", "Unknown")),
                    location=item.get("location", {}).get("name", "") if isinstance(item.get("location"), dict) else str(item.get("location", "")),
                    remote_type="partial" if item.get("remote") else "office",
                    salary_min=item.get("salaryMin") or item.get("tjmMin"),
                    salary_max=item.get("salaryMax") or item.get("tjmMax"),
                    description=item.get("description", ""),
                    tags=item.get("skills", []) if isinstance(item.get("skills"), list) else [],
                    source="freework",
                    source_url=url,
                    apply_url=url,
                ))
        except Exception as e:
            logger.debug(f"Free-Work Next.js parse error: {e}")

        return jobs
