import asyncio
import logging

import httpx
from bs4 import BeautifulSoup

from job_agent.scrapers.base import BaseScraper, RawJob

logger = logging.getLogger(__name__)

BASE_URL = "https://www.hellowork.com/fr-fr/emploi/recherche.html"


class HelloWorkScraper(BaseScraper):
    @property
    def source_name(self) -> str:
        return "hellowork"

    async def scrape(self, queries: list[str], locations: list[str], config: dict) -> list[RawJob]:
        max_pages = config.get("max_pages", 3)
        delay = config.get("delay_between_requests", 3)
        jobs = []
        seen_urls = set()

        async with httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "fr-FR,fr;q=0.9",
            },
        ) as client:
            for query in queries:
                for location in locations:
                    for page in range(1, max_pages + 1):
                        params = {
                            "k": query,
                            "l": location,
                            "p": page,
                        }
                        try:
                            resp = await client.get(BASE_URL, params=params)
                            resp.raise_for_status()
                        except Exception as e:
                            logger.error(f"HelloWork error for '{query}' p{page}: {e}")
                            break

                        new_jobs = self._parse_page(resp.text, seen_urls)
                        if not new_jobs:
                            break
                        jobs.extend(new_jobs)
                        await asyncio.sleep(delay)

        logger.info(f"HelloWork: {len(jobs)} jobs found")
        return jobs

    def _parse_page(self, html: str, seen_urls: set) -> list[RawJob]:
        soup = BeautifulSoup(html, "lxml")
        jobs = []

        # HelloWork uses article or li elements for job cards
        cards = soup.select("[data-cy='offerCard'], .offer-card, article.tw-flex")
        if not cards:
            # Try alternative selectors
            cards = soup.select("li[class*='offer'], div[class*='job-card']")

        for card in cards:
            try:
                # Title
                title_el = card.select_one("h3 a, h2 a, a[data-cy='offerTitle'], a[class*='title']")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                url = title_el.get("href", "")
                if url and not url.startswith("http"):
                    url = f"https://www.hellowork.com{url}"
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                # Company
                company_el = card.select_one("[data-cy='companyName'], span[class*='company'], p[class*='company']")
                company = company_el.get_text(strip=True) if company_el else "Unknown"

                # Location
                loc_el = card.select_one("[data-cy='localization'], span[class*='location'], p[class*='location']")
                location = loc_el.get_text(strip=True) if loc_el else ""

                # Contract type
                contract_el = card.select_one("[data-cy='contractType'], span[class*='contract']")
                contract = contract_el.get_text(strip=True) if contract_el else ""

                # Description snippet
                desc_el = card.select_one("[data-cy='description'], p[class*='description']")
                description = desc_el.get_text(strip=True) if desc_el else ""

                jobs.append(RawJob(
                    title=title,
                    company=company,
                    location=location,
                    remote_type="partial" if "télétravail" in (description + location).lower() else "office",
                    description=f"{contract} - {description}" if contract else description,
                    tags=[],
                    source="hellowork",
                    source_url=url,
                    apply_url=url,
                ))
            except Exception as e:
                logger.debug(f"HelloWork parse error: {e}")
                continue

        return jobs
