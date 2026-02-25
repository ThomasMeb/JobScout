import asyncio
import json
import logging
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from job_agent.scrapers.base import BaseScraper, RawJob
from job_agent.scrapers.browser import get_page

logger = logging.getLogger(__name__)

BASE_URL = "https://welovedevs.com"


class WeLoveDevsScraper(BaseScraper):
    @property
    def source_name(self) -> str:
        return "welovedevs"

    async def scrape(self, queries: list[str], locations: list[str], config: dict) -> list[RawJob]:
        delay = config.get("delay_between_requests", 3)
        max_pages = config.get("max_pages", 2)
        jobs = []
        seen_urls = set()

        for query in queries:
            for page_num in range(1, max_pages + 1):
                params = urlencode({"query": query, "page": page_num})
                url = f"{BASE_URL}/app/job?{params}"
                try:
                    async with get_page() as page:
                        await page.goto(url, wait_until="domcontentloaded")
                        try:
                            await page.wait_for_selector(
                                "a[href*='/app/job/'], div[class*='job-card'], article",
                                timeout=10_000,
                            )
                        except Exception:
                            pass
                        html = await page.content()
                except Exception as e:
                    logger.error(f"WeLoveDevs error for '{query}' p{page_num}: {e}")
                    break

                new_jobs = self._parse_page(html, seen_urls)
                if not new_jobs:
                    break
                jobs.extend(new_jobs)
                await asyncio.sleep(delay)

        logger.info(f"WeLoveDevs: {len(jobs)} jobs found")
        return jobs

    def _parse_page(self, html: str, seen_urls: set) -> list[RawJob]:
        jobs = []
        soup = BeautifulSoup(html, "lxml")

        # Try __NEXT_DATA__ or __NUXT_DATA__ first
        for script_id in ("__NEXT_DATA__", "__NUXT_DATA__"):
            script = soup.find("script", {"id": script_id})
            if script and script.string:
                try:
                    data = json.loads(script.string)
                    return self._parse_json_data(data, seen_urls)
                except (json.JSONDecodeError, KeyError):
                    pass

        # Fallback: HTML parsing
        cards = soup.select("a[href*='/app/job/'], div[class*='job-card'], article[class*='job']")
        for card in cards:
            try:
                if card.name == "a":
                    card_url = card.get("href", "")
                    title_el = card.select_one("h2, h3, [class*='title'], span[class*='title']")
                else:
                    link = card.select_one("a[href*='/app/job/']")
                    card_url = link.get("href", "") if link else ""
                    title_el = card.select_one("h2, h3, [class*='title']")

                if not title_el:
                    continue
                title = title_el.get_text(strip=True)

                if card_url and not card_url.startswith("http"):
                    card_url = f"{BASE_URL}{card_url}"
                if not card_url or card_url in seen_urls:
                    continue
                seen_urls.add(card_url)

                company_el = card.select_one("[class*='company'], [class*='entreprise']")
                company = company_el.get_text(strip=True) if company_el else "Unknown"

                loc_el = card.select_one("[class*='location'], [class*='city']")
                location = loc_el.get_text(strip=True) if loc_el else ""

                salary_el = card.select_one("[class*='salary'], [class*='salaire']")
                salary_text = salary_el.get_text(strip=True) if salary_el else ""

                s_min, s_max = _parse_salary(salary_text)

                jobs.append(RawJob(
                    title=title,
                    company=company,
                    location=location,
                    remote_type="office",
                    salary_min=s_min,
                    salary_max=s_max,
                    salary_currency="EUR",
                    description="",
                    tags=[],
                    source="welovedevs",
                    source_url=card_url,
                    apply_url=card_url,
                ))
            except Exception as e:
                logger.debug(f"WeLoveDevs parse error: {e}")
                continue

        return jobs

    def _parse_json_data(self, data: dict, seen_urls: set) -> list[RawJob]:
        jobs = []
        try:
            props = data.get("props", {}).get("pageProps", {})
            items = props.get("jobs", props.get("offers", []))
            if isinstance(items, dict):
                items = items.get("data", [])

            for item in items:
                slug = item.get("slug", "") or item.get("id", "")
                url = f"{BASE_URL}/app/job/{slug}"
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                jobs.append(RawJob(
                    title=item.get("title", ""),
                    company=item.get("company", {}).get("name", "Unknown") if isinstance(item.get("company"), dict) else str(item.get("company", "Unknown")),
                    location=item.get("location", ""),
                    remote_type="partial" if item.get("remote") else "office",
                    salary_min=item.get("salaryMin"),
                    salary_max=item.get("salaryMax"),
                    salary_currency="EUR",
                    description=item.get("description", ""),
                    tags=item.get("tags", []) if isinstance(item.get("tags"), list) else [],
                    source="welovedevs",
                    source_url=url,
                    apply_url=url,
                ))
        except Exception as e:
            logger.debug(f"WeLoveDevs JSON parse error: {e}")

        return jobs


def _parse_salary(text: str) -> tuple[int | None, int | None]:
    import re
    numbers = re.findall(r'(\d+)', text.replace(" ", ""))
    cleaned = [int(n) for n in numbers if int(n) > 20]
    if len(cleaned) >= 2:
        s_min = cleaned[0] * 1000 if cleaned[0] < 200 else cleaned[0]
        s_max = cleaned[1] * 1000 if cleaned[1] < 200 else cleaned[1]
        return s_min, s_max
    if len(cleaned) == 1:
        s_min = cleaned[0] * 1000 if cleaned[0] < 200 else cleaned[0]
        return s_min, None
    return None, None
