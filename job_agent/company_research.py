import logging
import os

import httpx

from job_agent.storage import insert_company

logger = logging.getLogger(__name__)

LBB_API_URL = "https://api.francetravail.io/partenaire/labonneboite/v1/company/"
TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"

# ROME codes relevant to ML/Data Science
DEFAULT_ROME_CODES = [
    "M1805",  # Études et développement informatique
    "M1810",  # Production et exploitation de systèmes d'information
]


async def _get_ft_token() -> str | None:
    client_id = os.environ.get("FRANCE_TRAVAIL_CLIENT_ID", "")
    client_secret = os.environ.get("FRANCE_TRAVAIL_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        return None

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.post(
                TOKEN_URL,
                params={"realm": "/partenaire"},
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "scope": "api_labonneboitev1",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            return resp.json().get("access_token")
        except Exception as e:
            logger.error(f"La Bonne Boite OAuth2 error: {e}")
            return None


async def search_labonneboite(conn, config: dict) -> int:
    """Search La Bonne Boite for companies with high hiring potential. Returns count of new companies."""
    token = await _get_ft_token()
    if not token:
        logger.warning("France Travail token unavailable, skipping La Bonne Boite")
        return 0

    rome_codes = config.get("rome_codes", DEFAULT_ROME_CODES)
    locations = config.get("locations", [])
    new_count = 0

    async with httpx.AsyncClient(timeout=30) as client:
        for rome in rome_codes:
            for location in locations:
                try:
                    resp = await client.get(
                        LBB_API_URL,
                        params={
                            "rome_codes": rome,
                            "commune_id": location.get("commune_id", ""),
                            "latitude": location.get("latitude"),
                            "longitude": location.get("longitude"),
                            "distance": location.get("distance", 30),
                            "page_size": 20,
                            "sort": "score",
                        },
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Accept": "application/json",
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    logger.error(f"La Bonne Boite error for ROME {rome}, {location}: {e}")
                    continue

                companies = data.get("companies", [])
                for company in companies:
                    company_id = insert_company(
                        conn,
                        name=company.get("name", "Unknown"),
                        website=company.get("url"),
                        sector=company.get("naf_text"),
                        location=f"{company.get('city', '')}",
                        source="labonneboite",
                        relevance_score=company.get("stars", 0) * 20,
                    )
                    if company_id:
                        new_count += 1

    logger.info(f"La Bonne Boite: {new_count} new companies")
    return new_count


async def load_target_companies(conn, config: dict) -> int:
    """Load manually defined target companies from config. Returns count of new companies."""
    targets = config.get("target_companies", [])
    new_count = 0

    for target in targets:
        company_id = insert_company(
            conn,
            name=target["name"],
            website=target.get("website"),
            careers_url=target.get("careers_url"),
            sector=target.get("sector"),
            location=target.get("location"),
            source="manual",
            relevance_score=target.get("relevance_score", 80),
        )
        if company_id:
            new_count += 1

    if new_count:
        logger.info(f"Target companies: {new_count} new")
    return new_count


async def run_company_research(conn, config: dict) -> int:
    """Run all company research sources. Returns total new companies."""
    total = 0
    total += await load_target_companies(conn, config)

    lbb_config = config.get("labonneboite", {})
    if lbb_config.get("enabled", False):
        total += await search_labonneboite(conn, lbb_config)

    return total
