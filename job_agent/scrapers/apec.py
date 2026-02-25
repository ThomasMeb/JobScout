import asyncio
import logging

import httpx
from bs4 import BeautifulSoup

from job_agent.scrapers.base import BaseScraper, RawJob
from job_agent.scrapers.browser import get_page

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.apec.fr/candidat/recherche-emploi.html/emploi"


class APECScraper(BaseScraper):
    @property
    def source_name(self) -> str:
        return "apec"

    async def scrape(self, queries: list[str], locations: list[str], config: dict) -> list[RawJob]:
        delay = config.get("delay_between_requests", 3)
        jobs = []
        seen_urls = set()

        for query in queries:
            # Try JSON API first (faster, no browser needed)
            try:
                api_jobs = await self._scrape_api(query, config)
                for j in api_jobs:
                    if j.source_url not in seen_urls:
                        seen_urls.add(j.source_url)
                        jobs.append(j)
                await asyncio.sleep(delay)
                continue  # API worked, skip Playwright for this query
            except Exception as e:
                logger.warning(f"APEC API failed for '{query}': {e}, falling back to Playwright")

            # Fallback: Playwright
            try:
                pw_jobs = await self._scrape_playwright(query, seen_urls)
                jobs.extend(pw_jobs)
            except Exception as e:
                logger.error(f"APEC Playwright error for '{query}': {e}")

            await asyncio.sleep(delay)

        logger.info(f"APEC: {len(jobs)} jobs found")
        return jobs

    async def _scrape_api(self, query: str, config: dict) -> list[RawJob]:
        """Try APEC's internal JSON API."""
        jobs = []
        max_results = config.get("max_results", 50)

        async with httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "fr-FR,fr;q=0.9",
            },
        ) as client:
            resp = await client.post(
                "https://www.apec.fr/cms/webservices/rechercheOffre/search",
                json={
                    "motsCles": query,
                    "pagination": {"startIndex": 0, "range": max_results},
                    "sort": {"type": "DATE"},
                    "activeFiltre": True,
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            if resp.status_code != 200:
                raise httpx.HTTPStatusError(
                    f"APEC API returned {resp.status_code}",
                    request=resp.request, response=resp,
                )

            data = resp.json()
            results = data.get("resultats", [])

            for item in results:
                numero = item.get("numeroOffre", "")
                url = f"https://www.apec.fr/candidat/recherche-emploi.html/emploi/detail-offre/{numero}"

                salary_text = item.get("salaireTexte", "")
                s_min, s_max = _parse_salary_text(salary_text)

                location = item.get("lieux", "")
                if isinstance(location, list):
                    location = ", ".join(location)

                jobs.append(RawJob(
                    title=item.get("intitule", ""),
                    company=item.get("nomCompagnie", "Non précisé"),
                    location=str(location),
                    remote_type=_detect_remote(item),
                    salary_min=s_min,
                    salary_max=s_max,
                    salary_currency="EUR",
                    description=item.get("texteHtml", "") or item.get("texte", ""),
                    tags=[],
                    source="apec",
                    source_url=url,
                    apply_url=url,
                ))

        return jobs

    async def _scrape_playwright(self, query: str, seen_urls: set) -> list[RawJob]:
        """Fallback: render APEC search page with Playwright."""
        jobs = []
        try:
            async with get_page() as page:
                url = f"{SEARCH_URL}?motsCles={query}&sortsType=DATE"
                await page.goto(url, wait_until="domcontentloaded")
                try:
                    await page.wait_for_selector(
                        "[class*='card-offer'], [class*='offer-item']",
                        timeout=10_000,
                    )
                except Exception:
                    pass
                html = await page.content()

            soup = BeautifulSoup(html, "lxml")
            cards = soup.select("[class*='card-offer'], [class*='offer-item']")
            for card in cards:
                title_el = card.select_one("h2 a, h3 a, a[class*='title']")
                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                card_url = title_el.get("href", "")
                if card_url and not card_url.startswith("http"):
                    card_url = f"https://www.apec.fr{card_url}"
                if not card_url or card_url in seen_urls:
                    continue
                seen_urls.add(card_url)

                company_el = card.select_one("[class*='company'], [class*='entreprise']")
                company = company_el.get_text(strip=True) if company_el else "Non précisé"

                loc_el = card.select_one("[class*='location'], [class*='lieu']")
                location = loc_el.get_text(strip=True) if loc_el else ""

                jobs.append(RawJob(
                    title=title,
                    company=company,
                    location=location,
                    remote_type="office",
                    description="",
                    tags=[],
                    source="apec",
                    source_url=card_url,
                    apply_url=card_url,
                ))

        except Exception as e:
            logger.error(f"APEC Playwright scrape error: {e}")

        return jobs


def _parse_salary_text(text: str) -> tuple[int | None, int | None]:
    import re
    numbers = re.findall(r'(\d+)\s*[kK€]', text.replace(" ", ""))
    if len(numbers) >= 2:
        return int(numbers[0]) * 1000, int(numbers[1]) * 1000
    if len(numbers) == 1:
        return int(numbers[0]) * 1000, None
    numbers = re.findall(r'(\d{2,})', text.replace(" ", ""))
    cleaned = [int(n) for n in numbers if int(n) > 10000]
    if len(cleaned) >= 2:
        return cleaned[0], cleaned[1]
    if len(cleaned) == 1:
        return cleaned[0], None
    return None, None


def _detect_remote(item: dict) -> str:
    text = str(item).lower()
    if "télétravail" in text or "remote" in text:
        if "100%" in text or "full remote" in text:
            return "full"
        return "partial"
    return "office"
