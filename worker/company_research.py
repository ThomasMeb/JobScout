"""Company research — La Bonne Boite integration + manual targets.

Adapted from legacy/job_agent/company_research.py for multi-tenant SaaS (Supabase).
"""

import logging

import httpx

from worker.config import get_settings
from worker.db import get_supabase

logger = logging.getLogger(__name__)

LBB_API_URL = "https://api.francetravail.io/partenaire/labonneboite/v1/company/"
TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"

DEFAULT_ROME_CODES = [
    "M1805",  # Études et développement informatique
    "M1810",  # Production et exploitation de systèmes d'information
]


async def _get_ft_token() -> str | None:
    settings = get_settings()
    client_id = settings.france_travail_client_id
    client_secret = settings.france_travail_client_secret
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


async def search_labonneboite(user_id: str, locations: list[dict]) -> int:
    """Search La Bonne Boite for companies. Returns count of new companies."""
    token = await _get_ft_token()
    if not token:
        logger.warning("France Travail token unavailable, skipping La Bonne Boite")
        return 0

    sb = get_supabase()
    new_count = 0

    async with httpx.AsyncClient(timeout=30) as client:
        for rome in DEFAULT_ROME_CODES:
            for location in locations:
                try:
                    params = {
                        "rome_codes": rome,
                        "distance": location.get("distance", 30),
                        "page_size": 20,
                        "sort": "score",
                    }
                    if location.get("commune_id"):
                        params["commune_id"] = location["commune_id"]
                    if location.get("latitude") and location.get("longitude"):
                        params["latitude"] = location["latitude"]
                        params["longitude"] = location["longitude"]

                    resp = await client.get(
                        LBB_API_URL,
                        params=params,
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Accept": "application/json",
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    logger.error(f"La Bonne Boite error for ROME {rome}: {e}")
                    continue

                companies = data.get("companies", [])
                for company in companies:
                    inserted = _upsert_company(
                        sb,
                        user_id=user_id,
                        name=company.get("name", "Unknown"),
                        website=company.get("url"),
                        sector=company.get("naf_text"),
                        location=company.get("city", ""),
                        source="labonneboite",
                        relevance_score=company.get("stars", 0) * 20,
                    )
                    if inserted:
                        new_count += 1

    if new_count:
        logger.info(f"La Bonne Boite: {new_count} new companies for user {user_id[:8]}")
    return new_count


def _upsert_company(
    sb, user_id: str, name: str, website: str | None = None,
    careers_url: str | None = None, sector: str | None = None,
    location: str | None = None, source: str = "manual",
    relevance_score: float = 0,
) -> bool:
    """Insert a company if not already present for this user+name+source. Returns True if new."""
    existing = (
        sb.table("companies")
        .select("id")
        .eq("user_id", user_id)
        .eq("name", name)
        .eq("source", source)
        .limit(1)
        .execute()
    )
    if existing.data:
        return False

    sb.table("companies").insert({
        "user_id": user_id,
        "name": name,
        "website": website,
        "careers_url": careers_url,
        "sector": sector,
        "location": location,
        "source": source,
        "relevance_score": relevance_score,
    }).execute()
    return True


async def run_company_research_all_users():
    """Run company research for all active users with search_locations configured."""
    settings = get_settings()
    if not settings.france_travail_client_id:
        return

    sb = get_supabase()
    profiles = (
        sb.table("profiles")
        .select("id, search_locations")
        .eq("onboarding_completed", True)
        .execute()
    )

    if not profiles.data:
        return

    for user in profiles.data:
        user_id = user["id"]
        search_locations = user.get("search_locations") or []
        if not search_locations:
            continue

        # Convert location strings to LBB-compatible dicts
        locations = [{"commune_id": "", "distance": 30} for _ in search_locations]

        try:
            await search_labonneboite(user_id, locations)
        except Exception as e:
            logger.error(f"Company research failed for user {user_id[:8]}: {e}")
