import asyncio
import logging
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from job_agent.scrapers.base import BaseScraper, RawJob
from job_agent.scrapers.browser import get_page

logger = logging.getLogger(__name__)

BASE_URL = "https://www.hellowork.com/fr-fr/emploi/recherche.html"


class HelloWorkScraper(BaseScraper):
    @property
    def source_name(self) -> str:
        return "hellowork"

    async def scrape(self, queries: list[str], locations: list[str], config: dict) -> list[RawJob]:
        max_pages = config.get("max_pages", 3)
        delay = config.get("delay_between_requests", 5)
        jobs = []
        seen_urls = set()

        for query in queries:
            for location in locations:
                for page_num in range(1, max_pages + 1):
                    params = urlencode({"k": query, "l": location, "p": page_num})
                    url = f"{BASE_URL}?{params}"
                    try:
                        async with get_page() as page:
                            await page.goto(url, wait_until="domcontentloaded")
                            # Wait for job cards to appear
                            try:
                                await page.wait_for_selector(
                                    "[data-cy='offerCard'], .offer-card, article",
                                    timeout=10_000,
                                )
                            except Exception:
                                pass  # Page may have loaded but no cards
                            html = await page.content()
                    except Exception as e:
                        logger.error(f"HelloWork error for '{query}' p{page_num}: {e}")
                        break

                    new_jobs = self._parse_page(html, seen_urls)
                    if not new_jobs:
                        break
                    jobs.extend(new_jobs)
                    await asyncio.sleep(delay)

        logger.info(f"HelloWork: {len(jobs)} jobs found")
        return jobs

    def _parse_page(self, html: str, seen_urls: set) -> list[RawJob]:
        soup = BeautifulSoup(html, "lxml")
        jobs = []

        cards = soup.select("[data-cy='offerCard'], .offer-card, article.tw-flex")
        if not cards:
            cards = soup.select("li[class*='offer'], div[class*='job-card']")

        for card in cards:
            try:
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

                company_el = card.select_one("[data-cy='companyName'], span[class*='company'], p[class*='company']")
                company = company_el.get_text(strip=True) if company_el else "Unknown"

                loc_el = card.select_one("[data-cy='localization'], span[class*='location'], p[class*='location']")
                location = loc_el.get_text(strip=True) if loc_el else ""

                contract_el = card.select_one("[data-cy='contractType'], span[class*='contract']")
                contract = contract_el.get_text(strip=True) if contract_el else ""

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
