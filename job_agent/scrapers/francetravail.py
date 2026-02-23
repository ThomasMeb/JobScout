import asyncio
import logging
from datetime import datetime

import httpx

from job_agent.scrapers.base import BaseScraper, RawJob, retry_request

logger = logging.getLogger(__name__)

# OAuth2 endpoints
TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
API_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"


class FranceTravailScraper(BaseScraper):
    @property
    def source_name(self) -> str:
        return "francetravail"

    async def scrape(self, queries: list[str], locations: list[str], config: dict) -> list[RawJob]:
        import os
        client_id = os.environ.get("FRANCE_TRAVAIL_CLIENT_ID", "")
        client_secret = os.environ.get("FRANCE_TRAVAIL_CLIENT_SECRET", "")

        if not client_id or not client_secret:
            logger.warning("France Travail credentials not configured, skipping")
            return []

        # Get OAuth2 token
        token = await self._get_token(client_id, client_secret)
        if not token:
            return []

        jobs = []
        seen_ids = set()

        async with httpx.AsyncClient(timeout=30) as client:
            first_request = True
            for query in queries:
                if not first_request:
                    await asyncio.sleep(2)
                first_request = False

                try:
                    resp = await retry_request(
                        client, "GET",
                        API_URL,
                        params={
                            "motsCles": query,
                            "range": "0-149",
                            "sort": 1,  # Sort by date
                            "typeContrat": config.get("contract_types", "CDI"),
                        },
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Accept": "application/json",
                        },
                    )
                    data = resp.json()
                except Exception as e:
                    logger.error(f"France Travail error for '{query}': {e}")
                    continue

                results = data.get("resultats", [])
                for item in results:
                    offer_id = item.get("id", "")
                    if offer_id in seen_ids:
                        continue
                    seen_ids.add(offer_id)

                    title = item.get("intitule", "")
                    entreprise = item.get("entreprise", {})
                    company = entreprise.get("nom", "")
                    if not title or not company:
                        logger.debug(f"France Travail: skipping job with missing title or company: {offer_id}")
                        continue

                    lieu = item.get("lieuTravail", {})
                    location_str = lieu.get("libelle", "")

                    salaire = item.get("salaire", {})
                    salary_min, salary_max = _parse_salary(salaire)

                    posted_at = None
                    date_str = item.get("dateCreation")
                    if date_str:
                        try:
                            posted_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        except ValueError:
                            pass

                    description = item.get("description", "")
                    competences = [c.get("libelle", "") for c in item.get("competences", [])]

                    jobs.append(RawJob(
                        title=title,
                        company=company,
                        location=location_str,
                        remote_type=_detect_remote(item),
                        salary_min=salary_min,
                        salary_max=salary_max,
                        salary_currency="EUR",
                        description=description,
                        tags=competences[:10],
                        source="francetravail",
                        source_url=item.get("origineOffre", {}).get("urlOrigine", f"https://candidat.francetravail.fr/offres/recherche/detail/{offer_id}"),
                        apply_url=item.get("contact", {}).get("urlPostulation"),
                        posted_at=posted_at,
                    ))

        logger.info(f"France Travail: {len(jobs)} jobs found")
        return jobs

    async def _get_token(self, client_id: str, client_secret: str) -> str | None:
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await retry_request(
                    client, "POST",
                    TOKEN_URL,
                    params={"realm": "/partenaire"},
                    data={
                        "grant_type": "client_credentials",
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "scope": "api_offresdemploiv2 o2dsoffre",
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                return resp.json().get("access_token")
            except Exception as e:
                logger.error(f"France Travail OAuth2 error: {e}")
                return None


def _parse_salary(salaire: dict) -> tuple[int | None, int | None]:
    libelle = salaire.get("libelle", "")
    s_min = None
    s_max = None

    # Try to extract numbers from libelle like "Annuel de 45000,00 Euros à 55000,00 Euros"
    import re
    numbers = re.findall(r'(\d+[\s,.]?\d*)', libelle)
    cleaned = []
    for n in numbers:
        n = n.replace(" ", "").replace(",", ".").replace(".00", "")
        try:
            val = int(float(n))
            if val > 1000:  # Ignore small numbers
                cleaned.append(val)
        except ValueError:
            pass

    if len(cleaned) >= 2:
        s_min, s_max = cleaned[0], cleaned[1]
    elif len(cleaned) == 1:
        s_min = cleaned[0]

    return s_min, s_max


def _detect_remote(item: dict) -> str:
    description = item.get("description", "").lower()

    if "télétravail" in description or "remote" in description:
        if "100%" in description or "full remote" in description:
            return "full"
        return "partial"
    return "office"
