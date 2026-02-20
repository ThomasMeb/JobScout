import logging
from pathlib import Path

from job_agent.config import APPLICATIONS_DIR, load_config, load_profile_text
from job_agent.llm import call_llm

logger = logging.getLogger(__name__)

COMPANY_BRIEF_PROMPT = """Tu es un expert en recherche d'emploi ML/Data Science.
Génère un brief de candidature spontanée pour cette entreprise.

PROFIL CANDIDAT (résumé) :
{profile_summary}

ENTREPRISE :
Nom : {company_name}
Site : {website}
Secteur : {sector}
Localisation : {location}

INSTRUCTIONS :
Génère un brief en markdown avec :
1. **Contexte entreprise** : ce qu'ils font, pourquoi ils auraient besoin d'un ML Engineer
2. **Points de match** : les forces du candidat qui correspondent à cette entreprise
3. **Angle d'approche** : comment formuler la candidature spontanée
4. **Suggestions de personnalisation** : éléments du parcours à mettre en avant

Sois concis et actionnable."""

JOB_BRIEF_PROMPT = """Tu es un expert en recherche d'emploi ML/Data Science.
Génère un brief pour préparer une candidature ciblée.

PROFIL CANDIDAT (résumé) :
{profile_summary}

OFFRE :
Titre : {title}
Entreprise : {company}
Localisation : {location}
Description : {description}

Mots-clés match : {match_keywords}
Mots-clés manquants : {missing_keywords}
Score : {score}/100

INSTRUCTIONS :
Génère un brief en markdown avec :
1. **Résumé de l'offre** : les points clés en 3-4 bullets
2. **Stratégie de candidature** : comment adresser les keywords manquants
3. **Expériences à mettre en avant** : lesquelles du parcours sont les plus pertinentes
4. **Ton et style** : formel/startup, FR/EN, technique/business

Sois concis et actionnable."""


def _get_profile_summary() -> str:
    """Get a short version of the profile for briefs."""
    profile = load_profile_text()
    if len(profile) > 2000:
        return profile[:2000] + "\n..."
    return profile


async def prepare_company_brief(company: dict) -> Path | None:
    """Generate a brief for a spontaneous application to a company."""
    company_dir = APPLICATIONS_DIR / "spontaneous" / _safe_name(company["name"])
    company_dir.mkdir(parents=True, exist_ok=True)
    brief_path = company_dir / "brief.md"

    if brief_path.exists():
        logger.info(f"Brief already exists for {company['name']}")
        return brief_path

    cfg = load_config()
    profile_summary = _get_profile_summary()

    prompt = COMPANY_BRIEF_PROMPT.format(
        profile_summary=profile_summary,
        company_name=company["name"],
        website=company.get("website") or "Non connu",
        sector=company.get("sector") or "Non connu",
        location=company.get("location") or "Non connu",
    )

    try:
        response, _, _ = await call_llm(
            "Tu génères des briefs de candidature.",
            prompt,
            max_tokens=cfg["llm"]["max_tokens_tailoring"],
            temperature=cfg["llm"]["temperature_tailoring"],
        )
    except Exception as e:
        logger.error(f"Failed to generate brief for {company['name']}: {e}")
        return None

    header = f"""# Brief candidature spontanée — {company['name']}

> Généré automatiquement par Job Agent
> Pour lancer la création du CV : `/resume-tailoring`

---

## Infos entreprise
- **Nom** : {company['name']}
- **Site** : {company.get('website') or 'N/A'}
- **Secteur** : {company.get('sector') or 'N/A'}
- **Localisation** : {company.get('location') or 'N/A'}

---

"""
    brief_path.write_text(header + response, encoding="utf-8")
    logger.info(f"Brief generated: {brief_path}")
    return brief_path


async def prepare_job_brief(job: dict) -> Path | None:
    """Generate a brief for a targeted job application."""
    import json

    company_name = job.get("company", "unknown")
    job_dir = APPLICATIONS_DIR / _safe_name(company_name) / _safe_name(job["title"])
    job_dir.mkdir(parents=True, exist_ok=True)
    brief_path = job_dir / "brief.md"

    if brief_path.exists():
        return brief_path

    cfg = load_config()
    profile_summary = _get_profile_summary()

    match_kw = json.loads(job.get("match_keywords") or "[]")
    missing_kw = json.loads(job.get("missing_keywords") or "[]")

    description = job.get("description") or ""
    if len(description) > 3000:
        description = description[:3000] + "..."

    prompt = JOB_BRIEF_PROMPT.format(
        profile_summary=profile_summary,
        title=job["title"],
        company=company_name,
        location=job.get("location") or "Non précisé",
        description=description,
        match_keywords=", ".join(match_kw),
        missing_keywords=", ".join(missing_kw),
        score=job.get("match_score", 0),
    )

    try:
        response, _, _ = await call_llm(
            "Tu génères des briefs de candidature.",
            prompt,
            max_tokens=cfg["llm"]["max_tokens_tailoring"],
            temperature=cfg["llm"]["temperature_tailoring"],
        )
    except Exception as e:
        logger.error(f"Failed to generate brief for {job['title']}: {e}")
        return None

    header = f"""# Brief candidature — {job['title']} @ {company_name}

> Généré automatiquement par Job Agent
> Pour lancer la création du CV : `/resume-tailoring`

---

## Infos offre
- **Titre** : {job['title']}
- **Entreprise** : {company_name}
- **Localisation** : {job.get('location') or 'N/A'}
- **Score** : {job.get('match_score', 0):.0f}/100
- **Lien** : {job.get('source_url', 'N/A')}

---

"""
    brief_path.write_text(header + response, encoding="utf-8")
    logger.info(f"Brief generated: {brief_path}")
    return brief_path


def _safe_name(name: str) -> str:
    """Convert a name to a safe directory name."""
    import re
    safe = re.sub(r'[^\w\s-]', '', name.strip())
    safe = re.sub(r'[\s]+', '_', safe)
    return safe[:80].lower()
