import asyncio
import logging

import httpx
from bs4 import BeautifulSoup

from job_agent.scrapers.base import BaseScraper, RawJob

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

        async with httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "fr-FR,fr;q=0.9",
            },
        ) as client:
            for query in queries:
                # APEC uses an internal API for search results
                # Try the JSON API endpoint first
                try:
                    api_jobs = await self._scrape_api(client, query, config)
                    for j in api_jobs:
                        if j.source_url not in seen_urls:
                            seen_urls.add(j.source_url)
                            jobs.append(j)
                except Exception as e:
                    logger.error(f"APEC API error for '{query}': {e}")

                await asyncio.sleep(delay)

        logger.info(f"APEC: {len(jobs)} jobs found")
        return jobs

    async def _scrape_api(self, client: httpx.AsyncClient, query: str, config: dict) -> list[RawJob]:
        """Try APEC's internal JSON API."""
        jobs = []
        max_results = config.get("max_results", 50)

        try:
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
                logger.debug(f"APEC API returned {resp.status_code}, falling back to HTML")
                return await self._scrape_html(client, query, config)

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

        except Exception as e:
            logger.error(f"APEC API parse error: {e}")

        return jobs

    async def _scrape_html(self, client: httpx.AsyncClient, query: str, config: dict) -> list[RawJob]:
        """Fallback: scrape APEC HTML search results."""
        jobs = []
        try:
            resp = await client.get(
                SEARCH_URL,
                params={"motsCles": query, "sortsType": "DATE"},
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            cards = soup.select("[class*='card-offer'], [class*='offer-item']")
            for card in cards:
                title_el = card.select_one("h2 a, h3 a, a[class*='title']")
                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                url = title_el.get("href", "")
                if url and not url.startswith("http"):
                    url = f"https://www.apec.fr{url}"

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
                    source_url=url,
                    apply_url=url,
                ))

        except Exception as e:
            logger.error(f"APEC HTML scrape error: {e}")

        return jobs


def _parse_salary_text(text: str) -> tuple[int | None, int | None]:
    import re
    numbers = re.findall(r'(\d+)\s*[kK€]', text.replace(" ", ""))
    if len(numbers) >= 2:
        return int(numbers[0]) * 1000, int(numbers[1]) * 1000
    if len(numbers) == 1:
        return int(numbers[0]) * 1000, None
    # Try with full numbers
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
